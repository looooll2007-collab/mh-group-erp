import base64
import datetime
import io
import random
import sqlite3
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. قائمة الثيمات وإعدادات الألوان (Themes)
# ==========================================
THEMES = {
    "الداكن الملكي والذهبي (Royal Dark & Gold)": {
        "primary": "#D97706",
        "bg": "#0F172A",
        "card": "#1E293B",
        "text": "#F8FAFC",
        "accent": "#F59E0B",
        "border": "#334155",
    },
    "أزرق نيلي احترافي (Modern Indigo)": {
        "primary": "#4F46E5",
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "text": "#1E293B",
        "accent": "#6366F1",
        "border": "#E2E8F0",
    },
    "أخضر زمردي فخم (Emerald Slate)": {
        "primary": "#059669",
        "bg": "#F4FBF7",
        "card": "#FFFFFF",
        "text": "#064E3B",
        "accent": "#10B981",
        "border": "#D1FAE5",
    },
    "عنابي فاخر (Burgundy Premium)": {
        "primary": "#881337",
        "bg": "#FFF1F2",
        "card": "#FFFFFF",
        "text": "#4C0519",
        "accent": "#E11D48",
        "border": "#FFE4E6",
    },
    "الليل والسيبربانك (Cyberpunk Neon)": {
        "primary": "#06B6D4",
        "bg": "#0B0F19",
        "card": "#111827",
        "text": "#F3F4F6",
        "accent": "#A855F7",
        "border": "#1F2937",
    },
}

# --- تهيئة الصفحة ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- إعدادات الجلسات (Session States) ---
if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 نظام إدارة MH Group ERP",
        "subtitle": "🔐 تسجيل الدخول للنظام",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
        "logo_bytes": None,
    }

if "dashboard_config" not in st.session_state:
    st.session_state["dashboard_config"] = {
        "header_title": "📊 لوحة التحكم المتقدمة والملخص العام",
        "show_metrics": True,
        "custom_note": "أهلاً بك في لوحة تحكم النظام العامة. يمكنك متابعة العمليات من هنا.",
    }

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الداكن الملكي والذهبي (Royal Dark & Gold)"

current_theme = THEMES[st.session_state["selected_theme"]]

# --- تطبيق CSS للمظهر العام ---
st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {current_theme["bg"]} !important;
        color: {current_theme["text"]} !important;
    }}
    .main-header {{
        font-size: 2rem;
        font-weight: 800;
        color: {current_theme["primary"]} !important;
        text-align: center;
        margin-bottom: 20px;
        padding: 12px;
        border-bottom: 3px solid {current_theme["accent"]};
        background-color: {current_theme["card"]};
        border-radius: 10px;
    }}
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid {current_theme["border"]} !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {current_theme["card"]} !important;
        border-right: 1px solid {current_theme["border"]} !important;
    }}
    .stButton>button {{
        background-color: {current_theme["primary"]} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. تهيئة قاعدة البيانات والتحديث التلقائي
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        # جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)

        cursor.execute("PRAGMA table_info(users)")
        u_cols = [c[1] for c in cursor.fetchall()]
        if "phone" not in u_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
            )

        # جدول العقارات (معالجة الأخطاء السابقة)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, 
                location TEXT, 
                price REAL, 
                status TEXT,
                type TEXT, 
                finishing TEXT
            )
        """)

        # فحص وتحديث أعمدة جدول العقارات تلقائياً
        cursor.execute("PRAGMA table_info(properties)")
        p_cols = [c[1] for c in cursor.fetchall()]
        required_p_cols = {
            "name": "TEXT",
            "location": "TEXT",
            "price": "REAL",
            "status": "TEXT",
            "type": "TEXT",
            "finishing": "TEXT",
        }
        for col_name, col_type in required_p_cols.items():
            if col_name not in p_cols:
                cursor.execute(
                    f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}"
                )

        # جدول مصاريف العقارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER, expense_type TEXT, amount REAL, notes TEXT, date TEXT,
                FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # جدول الموظفين والعمالة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
                hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
                workers_count INTEGER DEFAULT 1, craft_type TEXT
            )
        """)

        # جدول المستثمرين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
            )
        """)

        # جدول تذاكر IT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, category TEXT, status TEXT, created_at TEXT
            )
        """)

        # جدول سندات القبض والمعاملات الماليّة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT, amount REAL, description TEXT, payment_method TEXT, date TEXT
            )
        """)

        conn.commit()


init_db()


def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db") as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()


# ==========================================
# 3. منشئ طباعة السندات والعقود (HTML to Print)
# ==========================================
def generate_receipt_html(receipt_id, client_name, amount, description, method, date_str):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff; padding: 20px; color: #333; }}
            .receipt-box {{ max-width: 650px; margin: auto; border: 2px solid #1a365d; padding: 25px; border-radius: 8px; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #1a365d; padding-bottom: 10px; }}
            .title {{ color: #1a365d; margin: 0; font-size: 24px; }}
            .amount {{ background: #f1f5f9; text-align: center; font-size: 22px; font-weight: bold; color: #d97706; padding: 10px; margin: 20px 0; border-radius: 6px; }}
            .field {{ margin-bottom: 12px; font-size: 16px; }}
            .signatures {{ display: flex; justify-content: space-between; margin-top: 40px; padding-top: 15px; border-top: 1px dashed #ccc; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="receipt-box">
            <div class="header">
                <div>
                    <h2 class="title">MH GROUP</h2>
                    <small>لإدارة العقارات والخدمات الماليّة</small>
                </div>
                <div style="text-align: left;">
                    <div>رقم السند: #{receipt_id}</div>
                    <small>التاريخ: {date_str}</small>
                </div>
            </div>
            <h3 style="text-align:center; margin-top:20px;">سند قبض نقدية</h3>
            <div class="field"><strong>استلمنا من السيد/السادة:</strong> {client_name}</div>
            <div class="amount">المبلغ: {amount:,.2f} جنيه مصري</div>
            <div class="field"><strong>وذلك عن:</strong> {description or 'سداد دفعة حساب'}</div>
            <div class="field"><strong>طريقة الدفع:</strong> {method}</div>
            <div class="signatures">
                <div>المستلم: ..................</div>
                <div>الختم والتوقيع: ..................</div>
            </div>
        </div>
    </body>
    </html>
    """


# ==========================================
# 4. إدارة الجلسة والدخول
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "is_developer" not in st.session_state:
    st.session_state["is_developer"] = False


def login_page():
    cfg = st.session_state["login_config"]
    st.markdown(f"<h1 class='main-header'>{cfg['title']}</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(cfg["subtitle"])
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button(cfg["btn_text"], use_container_width=True):
            with sqlite3.connect("mh_group_erp.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role FROM users WHERE username = ? AND password = ?",
                    (username_input, password_input),
                )
                res = cursor.fetchone()

            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = username_input
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")


# ==========================================
# 5. الصفحة الرئيسية والأقسام
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(f"**المستخدم:** {st.session_state['username']}\n\n**الصلاحية:** {st.session_state['user_role']}")

    is_admin = st.session_state["user_role"] == "Admin"

    pages = [
        "📊 لوحة التحكم الرئيسية",
        "🏡 إدارة العقارات والوحدات",
        "💼 قسم المستثمرين والمالية",
        "🧾 سندات القبض والطباعة (PDF)",
        "👷 إدارة الموارد البشرية والعمالة",
        "👥 إدارة المستخدمين",
    ]

    if is_admin:
        pages.append("⚙️ إعدادات المطور والثيمات")

    page = st.sidebar.radio("القائمة الرئيسية", pages)

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 1. Dashboard ---
    if page == "📊 لوحة التحكم الرئيسية":
        st.markdown(f"<h1 class='main-header'>📊 لوحة التحكم الرئيسية</h1>", unsafe_allow_html=True)
        prop_df = safe_read_sql("SELECT COUNT(*) as count FROM properties")
        inv_df = safe_read_sql("SELECT SUM(investment_amount) as sum FROM investors")
        
        c1, c2 = st.columns(2)
        c1.metric("إجمالي العقارات المسجلة", f"{prop_df['count'][0] if not prop_df.empty else 0} وحدة")
        c2.metric("حجم الاستثمارات الكلي", f"{inv_df['sum'][0] if (not inv_df.empty and inv_df['sum'][0]) else 0:,.0f} EGP")

    # --- 2. Properties ---
    elif page == "🏡 إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات")
        with st.form("add_prop_form"):
            p_name = st.text_input("اسم العقار / الوحدة")
            p_type = st.selectbox("نوع العقار", ["شقة", "فيلا", "محل تجاري", "أرض", "مبنى كامل"])
            p_loc = st.text_input("الموقع")
            p_price = st.number_input("السعر المقدر", min_value=0.0)
            p_finishing = st.selectbox("التشطيب", ["بدون تشطيب", "لوكس", "سوبر لوكس"])
            p_stat = st.selectbox("الحالة", ["متاح", "تم البيع", "محجوز"])

            if st.form_submit_button("حفظ العقار"):
                if p_name.strip():
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            "INSERT INTO properties (name, location, price, status, type, finishing) VALUES (?, ?, ?, ?, ?, ?)",
                            (p_name.strip(), p_loc, float(p_price), p_stat, p_type, p_finishing)
                        )
                        conn.commit()
                    st.success("تم حفظ العقار بنجاح!")
                    st.rerun()
                else:
                    st.error("يرجى كتابة اسم العقار!")

        st.subheader("📋 قائمة العقارات")
        st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)

    # --- 3. Investors & P&L ---
    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين وحاسبة الأرباح")
        tab1, tab2 = st.tabs(["➕ تسجيل مستثمر", "🧮 حاسبة الأرباح والخسائر"])

        with tab1:
            with st.form("add_inv"):
                i_name = st.text_input("اسم المستثمر")
                i_amount = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                i_rate = st.number_input("نسبة العائد المتفق عليها (%)", min_value=0.0)
                if st.form_submit_button("تسجيل المستثمر"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                                     (i_name, i_amount, i_rate, str(datetime.date.today())))
                        conn.commit()
                    st.success("تم تسجل المستثمر بنجاح!")
                    st.rerun()

        with tab2:
            amt = st.number_input("رأس المال (EGP):", min_value=0.0, value=100000.0)
            rate = st.number_input("نسبة العائد التقديرية (%):", min_value=0.0, value=15.0)
            profit = amt * (rate / 100)
            st.metric("إجمالي الربح المتوقع", f"{profit:,.2f} EGP")
            st.metric("المبلغ النهائي مع الأرباح", f"{(amt + profit):,.2f} EGP")

    # --- 4. Receipts & Printing (Auto PDF / Print Generator) ---
    elif page == "🧾 سندات القبض والطباعة (PDF)":
        st.title("🧾 إنشاء وطباعة سندات القبض")
        tab_add, tab_list = st.tabs(["➕ إصدار سند جديد", "📋 السندات الصادرة للطباعة"])

        with tab_add:
            with st.form("create_receipt"):
                c_name = st.text_input("اسم العميل / المستثمر:")
                r_amount = st.number_input("المبلغ (EGP):", min_value=0.0)
                r_desc = st.text_input("البيان / السبب:")
                r_method = st.selectbox("طريقة الدفع:", ["نقداً", "تحويل بنكي", "شيك"])

                if st.form_submit_button("إصدار السند"):
                    if c_name and r_amount > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO receipts (client_name, amount, description, payment_method, date) VALUES (?, ?, ?, ?, ?)",
                                (c_name, float(r_amount), r_desc, r_method, str(datetime.date.today()))
                            )
                            conn.commit()
                        st.success("تم إصدار السند بنجاح!")
                        st.rerun()

        with tab_list:
            receipts_df = safe_read_sql("SELECT * FROM receipts ORDER BY id DESC")
            if not receipts_df.empty:
                for idx, row in receipts_df.iterrows():
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**سند #{row['id']}** | العميل: **{row['client_name']}** | المبلغ: **{row['amount']:,.2f} EGP** | التاريخ: {row['date']}")
                    with col_btn:
                        html_code = generate_receipt_html(row['id'], row['client_name'], row['amount'], row['description'], row['payment_method'], row['date'])
                        st.download_button(
                            label="🖨️ طباعة السند (HTML/PDF)",
                            data=html_code,
                            file_name=f"Receipt_{row['id']}.html",
                            mime="text/html",
                            key=f"btn_{row['id']}"
                        )
            else:
                st.info("لا توجد سندات صادر حتى الآن.")

    # --- 5. HR ---
    elif page == "👷 إدارة الموارد البشرية والعمالة":
        st.title("👷 إدارة العمالة والموظفين")
        st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)

    # --- 6. Users ---
    elif page == "👥 إدارة المستخدمين":
        st.title("👥 قائمة المستخدمين")
        st.dataframe(safe_read_sql("SELECT id, username, role, phone FROM users"), use_container_width=True)

    # --- 7. Settings & Themes ---
    elif page == "⚙️ إعدادات المطور والثيمات":
        st.title("🎨 التحكم بمظهر النظام")
        selected_theme_name = st.selectbox("اختر الثيم المطبق:", list(THEMES.keys()))
        if selected_theme_name != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = selected_theme_name
            st.rerun()
