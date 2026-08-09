import base64
import datetime
import io
import json
import random
import sqlite3
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والثيم الملكي (Royal Dark & Gold)
# ==========================================
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ثيم ملكي متوافق مع تصميم القائمة
CURRENT_THEME = {
    "primary": "#B8860B",  # ذهبي دافئ
    "bg": "#0B0F19",  # كحلي غامق جداً
    "card": "#111827",  # بطاقات داكنة
    "text": "#F9FAFB",
    "accent": "#D97706",
    "border": "#1F2937",
    "sidebar_bg": "#0F172A",
}

# تطبيق تنسيقات CSS للقائمة المخصصة
st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {CURRENT_THEME["bg"]} !important;
        color: {CURRENT_THEME["text"]} !important;
    }}
    .main-header {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {CURRENT_THEME["primary"]} !important;
        text-align: center;
        margin-bottom: 20px;
        padding: 12px;
        border-bottom: 2px solid {CURRENT_THEME["accent"]};
        background-color: {CURRENT_THEME["card"]};
        border-radius: 10px;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {CURRENT_THEME["sidebar_bg"]} !important;
        border-right: 1px solid {CURRENT_THEME["border"]} !important;
    }}
    /* تنسيق كارت الهوية الأسفل */
    .company-card {{
        background-color: #131C2E;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-top: 20px;
    }}
    .company-card h4 {{
        color: #D97706;
        margin: 0;
        font-size: 1.1rem;
    }}
    .company-card p {{
        color: #94A3B8;
        font-size: 0.85rem;
        margin-top: 4px;
        margin-bottom: 0px;
    }}
    /* أزرار النظام */
    .stButton>button {{
        background-color: {CURRENT_THEME["primary"]} !important;
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
# 2. قاعدة البيانات وتدقيق الصلاحيات
# ==========================================
def get_db_connection():
    return sqlite3.connect("mh_group_erp.db", timeout=20)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            phone TEXT
        )
    """)

    # الجلسات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, ip_address TEXT, login_time TEXT, status TEXT
        )
    """)

    # العقارات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, location TEXT, price REAL, status TEXT, type TEXT, finishing TEXT
        )
    """)

    # المستثمرين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT, notes TEXT
        )
    """)

    try:
        cursor.execute("SELECT notes FROM investors LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE investors ADD COLUMN notes TEXT")

    # الموظفين والعمالة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, emp_type TEXT, position TEXT, pay_type TEXT, total_pay REAL, hire_date TEXT
        )
    """)

    # الموردين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, service_type TEXT, phone TEXT, balance REAL
        )
    """)

    # الدعم الفني
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, category TEXT, status TEXT, created_at TEXT
        )
    """)

    # المستندات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT, category TEXT, upload_date TEXT, file_data BLOB
        )
    """)

    # إضافة مستخدم Admin افتراضي
    cursor.execute("SELECT * FROM users WHERE LOWER(TRIM(username)) = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
        )

    conn.commit()
    conn.close()


init_db()


def safe_read_sql(query, params=()):
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


# ==========================================
# 3. خريطة الصلاحيات للأقسام (Role Mapping)
# ==========================================
# الأدوار المتاحة للنظام
ROLE_OPTIONS = {
    "Admin": "مدير النظام (جميع الصلاحيات)",
    "RealEstate": "العقارات والمشروعات",
    "Finance": "الإدارة المالية",
    "HR": "الموارد البشرية والعمالة",
    "Investor": "المستثمرين",
    "Vendor": "الموردين",
    "Employee": "الموظفين",
    "IT": "تقنية المعلومات IT Support",
    "Document": "المستندات والتقارير",
}

# ربط كل صفحة بالصلاحية المسؤولة عنها
PAGE_ROLE_MAP = {
    "🏠 لوحة التحكم": "ALL",
    "🏢 العقارات والمشروعات": ["Admin", "RealEstate"],
    "💰 الإدارة المالية": ["Admin", "Finance"],
    "👥 الموارد البشرية": ["Admin", "HR"],
    "🤝 المستثمرين": ["Admin", "Investor"],
    "📦 الموردين": ["Admin", "Vendor"],
    "👷 الموظفين": ["Admin", "Employee", "HR"],
    "🎧 IT Support": ["Admin", "IT"],
    "📁 المستندات": ["Admin", "Document"],
    "📊 التقارير": ["Admin", "Finance", "RealEstate", "HR"],
    "⚙️ المستخدمين والصلاحيات": ["Admin"],
    "🛠️ الإعدادات": ["Admin"],
    "⏱️ سجل العمليات": ["Admin"],
}


# ==========================================
# 4. إدارة الجلسة وتسجيل الدخول
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""


def login_page():
    st.markdown(
        "<h1 class='main-header'>🏢 نظام إدارة MH GROUP ERP</h1>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 تسجيل الدخول للنظام")

        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button("تسجيل الدخول", use_container_width=True):
            clean_username = username_input.strip()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, username FROM users WHERE LOWER(TRIM(username)) = LOWER(?) AND password = ?",
                (clean_username, password_input),
            )
            res = cursor.fetchone()
            conn.close()

            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = res[1]
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")


# ==========================================
# 5. القائمة الجانبية والشاشات المخصصة
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    # --- رأس القائمة الجانبية ---
    st.sidebar.markdown(
        """
        <div style="text-align: center; padding-bottom: 10px;">
            <h2 style="color: #D97706; margin:0; font-weight: 900;">👑 MH GROUP</h2>
            <p style="color: #94A3B8; font-size: 0.75rem; margin:0;">ERP SYSTEM</p>
        </div>
        <hr style="border-color: #1E293B; margin-top: 5px; margin-bottom: 15px;">
    """,
        unsafe_allow_html=True,
    )

    # فلترة الأقسام بناءً على صلاحية المستخدم الحالي
    user_role = st.session_state["user_role"]

    allowed_pages = []
    for page_name, required_roles in PAGE_ROLE_MAP.items():
        if required_roles == "ALL" or user_role == "Admin":
            allowed_pages.append(page_name)
        elif (
            isinstance(required_roles, list) and user_role in required_roles
        ):
            allowed_pages.append(page_name)

    # عرض القائمة الجانبية المفلترة
    selected_page = st.sidebar.radio("التنقل بين الأقسام", allowed_pages)

    # --- الجزء الأسفل من القائمة الجانبية (شعار الشركة وزر الخروج) ---
    st.sidebar.markdown(
        """
        <div class="company-card">
            <h4>M H Group</h4>
            <p>للاستثمار والتطوير العقاري</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.write("")
    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # ==========================================
    # 6. محتوى الأقسام الشامل
    # ==========================================

    # --- 1. لوحة التحكم ---
    if selected_page == "🏠 لوحة التحكم":
        st.markdown(
            "<h1 class='main-header'>🏠 لوحة التحكم الرئيسية</h1>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "إجمالي العقارات",
            f"{len(safe_read_sql('SELECT id FROM properties'))} وحدة",
        )
        c2.metric(
            "العمالة والموظفين",
            f"{len(safe_read_sql('SELECT id FROM employees'))} فرد",
        )
        inv_df = safe_read_sql("SELECT investment_amount FROM investors")
        c3.metric(
            "حجم الاستثمارات",
            f"{inv_df['investment_amount'].sum() if not inv_df.empty else 0:,.0f} EGP",
        )

    # --- 2. العقارات والمشروعات ---
    elif selected_page == "🏢 العقارات والمشروعات":
        st.title("🏢 العقارات والمشروعات")
        tab1, tab2 = st.tabs(["📋 قائمة العقارات", "➕ إضافة عقار"])
        with tab1:
            st.dataframe(
                safe_read_sql("SELECT * FROM properties"),
                use_container_width=True,
            )
        with tab2:
            with st.form("add_p"):
                p_n = st.text_input("اسم العقار")
                p_l = st.text_input("الموقع")
                p_p = st.number_input("السعر", min_value=0.0)
                if st.form_submit_button("حفظ"):
                    if p_n:
                        conn = get_db_connection()
                        conn.execute(
                            "INSERT INTO properties (name, location, price) VALUES (?, ?, ?)",
                            (p_n, p_l, p_p),
                        )
                        conn.commit()
                        conn.close()
                        st.success("تم الحفظ!")
                        st.rerun()

    # --- 3. الإدارة المالية ---
    elif selected_page == "💰 الإدارة المالية":
        st.title("💰 الإدارة المالية والمصروفات")
        st.info("قسم الإدارة المالية والميزانية العمومية.")

    # --- 4. الموارد البشرية ---
    elif selected_page == "👥 الموارد البشرية":
        st.title("👥 الموارد البشرية والعمالة")
        st.dataframe(
            safe_read_sql("SELECT * FROM employees"), use_container_width=True
        )

    # --- 5. المستثمرين ---
    elif selected_page == "🤝 المستثمرين":
        st.title("🤝 قسم المستثمرين والأرباح")
        tab1, tab2 = st.tabs(["➕ إضافة مستثمر", "📊 سجل المستثمرين"])
        with tab1:
            with st.form("add_inv"):
                i_n = st.text_input("اسم المستثمر")
                i_a = st.number_input("المبلغ", min_value=0.0)
                i_r = st.number_input("نسبة الربح (%)", min_value=0.0)
                if st.form_submit_button("إضافة"):
                    if i_n and i_a > 0:
                        conn = get_db_connection()
                        conn.execute(
                            "INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                            (
                                i_n,
                                i_a,
                                i_r,
                                str(datetime.date.today()),
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.success("تمت الإضافة بنجاح!")
                        st.rerun()
        with tab2:
            st.dataframe(
                safe_read_sql("SELECT * FROM investors"),
                use_container_width=True,
            )

    # --- 6. الموردين ---
    elif selected_page == "📦 الموردين":
        st.title("📦 إدارة الموردين ومواد البناء")
        st.dataframe(
            safe_read_sql("SELECT * FROM vendors"), use_container_width=True
        )

    # --- 7. الموظفين ---
    elif selected_page == "👷 الموظفين":
        st.title("👷 سجل الموظفين الحليين")
        st.dataframe(
            safe_read_sql("SELECT * FROM employees"), use_container_width=True
        )

    # --- 8. IT Support ---
    elif selected_page == "🎧 IT Support":
        st.title("🎧 الدعم الفني وتذاكر IT")
        st.dataframe(
            safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True
        )

    # --- 9. المستندات ---
    elif selected_page == "📁 المستندات":
        st.title("📁 الأرشيف الإلكتروني والمستندات")
        st.dataframe(
            safe_read_sql("SELECT id, file_name, category FROM documents"),
            use_container_width=True,
        )

    # --- 10. التقارير ---
    elif selected_page == "📊 التقارير":
        st.title("📊 التقارير المجمعة والتحليلات")
        st.info("تقارير أداء العقارات والمالية والموارد البشرية.")

    # --- 11. إدارة المستخدمين والصلاحيات (خاص بالـ Admin فقط) ---
    elif selected_page == "⚙️ المستخدمين والصلاحيات":
        st.title("⚙️ إدارة المستخدمين وتحديد الصلاحيات")
        tab1, tab2 = st.tabs(["📋 قائمة المستخدمين", "➕ إضافة مستخدم وصلاحية"])

        with tab1:
            st.dataframe(
                safe_read_sql("SELECT id, username, role, phone FROM users"),
                use_container_width=True,
            )

        with tab2:
            if "u_succ" in st.session_state:
                st.success(st.session_state.pop("u_succ"))
            if "u_err" in st.session_state:
                st.error(st.session_state.pop("u_err"))

            with st.form("add_user_role_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_phone = st.text_input("رقم الهاتف")
                selected_role = st.selectbox(
                    "حدد الصلاحية والقسم المسموح له برؤيته فقط",
                    options=list(ROLE_OPTIONS.keys()),
                    format_func=lambda x: f"{x} - {ROLE_OPTIONS[x]}",
                )

                if st.form_submit_button("إنشاء الحساب بالصلاحية"):
                    clean_u = u_name.strip()
                    clean_p = u_pass.strip()
                    if clean_u and clean_p:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                (clean_u, clean_p, selected_role, u_phone),
                            )
                            conn.commit()
                            conn.close()
                            st.session_state["u_succ"] = (
                                f"✅ تم إنشاء حساب '{clean_u}' بصلاحية '{selected_role}' بنجاح!"
                            )
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.session_state["u_err"] = (
                                "❌ اسم المستخدم مسجل مسبقاً!"
                            )
                        except Exception as e:
                            st.session_state["u_err"] = f"❌ خطأ: {e}"
                    else:
                        st.error("يرجى ملء البيانات!")

    # --- 12. الإعدادات وسجل العمليات ---
    elif selected_page in ["🛠️ الإعدادات", "⏱️ سجل العمليات"]:
        st.title(selected_page)
        st.info("قسم إعدادات النظام ومراقبة النشاط.")
