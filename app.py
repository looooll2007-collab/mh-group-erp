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
    page_title="MH Group ERP System - Enterprise Edition",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- إعدادات الجلسات المتطورة ---
if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 مجموعة شركات MH Group ERP",
        "subtitle": "🔐 بوابة الدخول الموحدة للمجموعة",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
        "logo_bytes": None,
    }

if "dashboard_config" not in st.session_state:
    st.session_state["dashboard_config"] = {
        "header_title": "📊 لوحة التحليلات التنفيذية والملخص العام",
        "show_metrics": True,
        "custom_note": "أهلاً بك في لوحة تحكم MH Group. يمكنك متابعة المؤشرات والرسوم البيانية للشركات والأقسام.",
    }

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الداكن الملكي والذهبي (Royal Dark & Gold)"

current_theme = THEMES[st.session_state["selected_theme"]]

# --- تطبيق CSS للمظهر العام الاحترافي ---
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
# 2. تهيئة قاعدة البيانات الشاملة مع معالجة الهيكلة
# ==========================================
def get_ip_address():
    try:
        headers = st.context.headers
        if "X-Forwarded-For" in headers:
            return headers["X-Forwarded-For"].split(",")[0]
    except Exception:
        pass
    return "127.0.0.1"

def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        # 1. المستخدمين والجلسات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)
        
        # إنشاء جدول user_sessions أو تحديثه بالحقوق المطلوبة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_time TEXT,
                logout_time TEXT,
                ip_address TEXT,
                status TEXT
            )
        """)
        
        # فحص وإضافة الأعمدة إن كانت غائبة في الجداول القديمة
        existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(user_sessions)").fetchall()]
        for col in ["logout_time", "ip_address", "status"]:
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE user_sessions ADD COLUMN {col} TEXT")
                except Exception:
                    pass

        # 2. المالية والحسابات والمصروفات والسلف
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trans_type TEXT,
                department TEXT,
                amount REAL,
                description TEXT,
                trans_date TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_advances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_custom_id TEXT,
                emp_name TEXT,
                advance_amount REAL,
                notes TEXT,
                date_given TEXT
            )
        """)

        # 3. العمالة والموارد البشرية (HR)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT UNIQUE,
                name TEXT,
                emp_type TEXT,
                craft_type TEXT,
                hourly_rate REAL,
                hours_worked REAL,
                daily_rate REAL,
                workers_count INTEGER DEFAULT 1,
                total_pay REAL,
                hire_date TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hr_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT,
                doc_type TEXT,
                file_name TEXT,
                upload_date TEXT,
                file_data BLOB
            )
        """)

        # 4. العقارات والمخزون
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT UNIQUE,
                name TEXT,
                location TEXT,
                price REAL,
                finishing_type TEXT,
                expenses REAL DEFAULT 0.0,
                sale_price REAL DEFAULT 0.0,
                status TEXT
            )
        """)

        # 5. المستثمرين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                property_custom_id TEXT,
                investment_amount REAL,
                investment_ratio REAL,
                return_rate REAL,
                total_returns REAL,
                start_date TEXT
            )
        """)

        # 6. IT Support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT UNIQUE,
                name TEXT,
                daily_rate REAL,
                hourly_rate REAL,
                hours_worked REAL,
                total_pay REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT,
                doc_type TEXT,
                file_name TEXT,
                upload_date TEXT,
                file_data BLOB
            )
        """)

        # 7. سجل الأنشطة والعمليات الفاشلة والناجحة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                department TEXT,
                action TEXT,
                status TEXT,
                ip_address TEXT,
                timestamp TEXT
            )
        """)

        # 8. قسم الإبلاغ عن المشاكل (Helpdesk)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problem_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_username TEXT,
                issue_category TEXT,
                description TEXT,
                doc_type TEXT,
                file_name TEXT,
                file_data BLOB,
                status TEXT,
                report_date TEXT
            )
        """)

        # إضافة مسؤول Admin تلقائياً
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')")

        conn.commit()

init_db()

def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db") as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()

def log_audit_action(username, department, action, status="ناجحة"):
    try:
        ip = get_ip_address()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute(
                "INSERT INTO audit_logs (username, department, action, status, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (username, department, action, status, ip, now)
            )
            conn.commit()
    except Exception:
        pass

# ==========================================
# 3. إدارة الجلسات والدخول
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

def login_page():
    cfg = st.session_state["login_config"]
    st.markdown(f"<h1 class='main-header'>{cfg['title']}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(cfg["subtitle"])
        st.caption(cfg["welcome_msg"])

        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button(cfg["btn_text"], use_container_width=True):
            with sqlite3.connect("mh_group_erp.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username_input.strip(), password_input.strip()))
                res = cursor.fetchone()

            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = username_input.strip()

                # تسجيل الجلسة بالوقت والـ IP
                login_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_ip = get_ip_address()
                with sqlite3.connect("mh_group_erp.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO user_sessions (username, login_time, logout_time, ip_address, status) VALUES (?, ?, ?, ?, ?)",
                        (username_input.strip(), login_now, "نشطة حالياً", user_ip, "نشطة")
                    )
                    conn.commit()
                    st.session_state["session_id"] = cur.lastrowid

                log_audit_action(username_input.strip(), "تسجيل الدخول", "تسجيل دخول ناجح للمنظومة", "ناجحة")
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                log_audit_action(username_input.strip() or "مجهول", "تسجيل الدخول", "محاولة دخول ببيانات خاطئة", "فاشلة")
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

# ==========================================
# 4. التطبيق الرئيسي بعد تسجيل الدخول
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(f"**المستخدم الحالي:** {st.session_state['username']}\n\n**الصلاحية:** {st.session_state['user_role']}")

    all_pages = [
        "📊 لوحة التحليلات والداشبورد",
        "⚙️ قسم المستخدمين وصلاحيات الدخول",
        "💰 قسم الإدارة المالية الشاملة",
        "👷 قسم الموارد البشرية والعمالة (HR)",
        "🏢 قسم العقارات والمخزون",
        "🤝 قسم المستثمرين والأرباح",
        "💻 قسم تقنية المعلومات (IT Support)",
        "⏱️ قسم سجل العمليات والمراقبة",
        "⚠️ قسم الإبلاغ عن مشكلة (Helpdesk)"
    ]

    selected_page = st.sidebar.radio("تنقل بين أقسام المنظومة", all_pages)

    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        if st.session_state["session_id"]:
            logout_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute("UPDATE user_sessions SET logout_time = ?, status = 'منتهية' WHERE id = ?", (logout_now, st.session_state["session_id"]))
                conn.commit()
        log_audit_action(st.session_state["username"], "تسجيل الخروج", "تسجيل خروج آمن من النظام", "ناجحة")
        st.session_state["logged_in"] = False
        st.session_state["session_id"] = None
        st.rerun()

    # ----------------------------------------------------
    # 1️⃣ قسم المستخدمين وصلاحيات الدخول والجلسات
    # ----------------------------------------------------
    if selected_page == "⚙️ قسم المستخدمين وصلاحيات الدخول":
        st.markdown("<h1 class='main-header'>⚙️ إدارة المستخدمين وجلسات الدخول النشطة</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["👥 إدارة الحسابات والصلاحيات", "➕ إضافة مستخدم جديد", "📡 سجل جلسات الدخول والـ IP"])

        with tab1:
            st.subheader("📋 مستخدمي النظام الحاليين")
            df_users = safe_read_sql("SELECT id, username, role, phone FROM users")
            st.dataframe(df_users, use_container_width=True)

            # حذف مستخدم
            st.markdown("---")
            st.write("### 🗑️ حذف مستخدم")
            user_to_del = st.selectbox("اختر المستخدم للحذف:", options=[""] + df_users["username"].tolist())
            if st.button("تأكيد حذف الحساب"):
                if user_to_del and user_to_del != "admin":
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                        conn.commit()
                    log_audit_action(st.session_state["username"], "إدارة المستخدمين", f"حذف المستخدم {user_to_del}")
                    st.success(f"تم حذف الحساب {user_to_del} بنجاح!")
                    st.rerun()
                elif user_to_del == "admin":
                    st.error("لا يمكن حذف حساب Admin الرئيسي!")

        with tab2:
            st.subheader("➕ إضافة حساب مستخدم جديد")
            with st.form("add_new_user_form"):
                new_u = st.text_input("اسم المستخدم")
                new_p = st.text_input("كلمة المرور", type="password")
                new_ph = st.text_input("رقم الهاتف")
                new_r = st.selectbox("الصلاحية / القسم", ["Admin", "HR", "Finance", "RealEstate", "Investor", "IT"])
                if st.form_submit_button("إضافة الحساب"):
                    if new_u and new_p:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)", (new_u.strip(), new_p.strip(), new_r, new_ph))
                                conn.commit()
                            log_audit_action(st.session_state["username"], "إدارة المستخدمين", f"إضافة حساب جديد {new_u}")
                            st.success(f"تم إضافة المستخدم {new_u} بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مسجل بالفعل!")

        with tab3:
            st.subheader("📡 سجل الجلسات المباشرة والتفصيلية (IP & Duration)")
            df_sessions = safe_read_sql("SELECT id, username, login_time, logout_time, ip_address, status FROM user_sessions ORDER BY id DESC")
            st.dataframe(df_sessions, use_container_width=True)

    # ----------------------------------------------------
    # 2️⃣ قسم الداشبورد والرسوم البيانية المتقدمة
    # ----------------------------------------------------
    elif selected_page == "📊 لوحة التحليلات والداشبورد":
        st.markdown("<h1 class='main-header'>📊 لوحة التحليلات التنفيذية والملخص العام</h1>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        total_p = safe_read_sql("SELECT COUNT(*) as count FROM properties")["count"].iloc[0] if not safe_read_sql("SELECT COUNT(*) as count FROM properties").empty else 0
        total_e = safe_read_sql("SELECT COUNT(*) as count FROM employees")["count"].iloc[0] if not safe_read_sql("SELECT COUNT(*) as count FROM employees").empty else 0
        total_inv = safe_read_sql("SELECT SUM(investment_amount) as sum FROM investors")["sum"].iloc[0] or 0.0
        total_inc = safe_read_sql("SELECT SUM(amount) as sum FROM financial_transactions WHERE trans_type = 'واردات'")["sum"].iloc[0] or 0.0

        m1.metric("إجمالي العقارات المسجلة", f"{total_p} وحدات")
        m2.metric("إجمالي العمالة والموظفين", f"{total_e} فرد")
        m3.metric("إجمالي رؤوس الأموال المستثمرة", f"{total_inv:,.2f} EGP")
        m4.metric("إجمالي الصادرات / الإيرادات", f"{total_inc:,.2f} EGP")

        st.markdown("---")
        st.subheader("📈 الرسوم البيانية التوضيحية للمجموعة")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### 🧱 توزيع العمالة والموظفين حسب المهنة (Craft Type)")
            emp_craft_df = safe_read_sql("SELECT craft_type, COUNT(*) as count FROM employees GROUP BY craft_type")
            if not emp_craft_df.empty:
                st.bar_chart(data=emp_craft_df.set_index("craft_type"))
            else:
                st.info("لا توجد بيانات كافية لعرض الرسم البياني للعمالة.")

        with c2:
            st.markdown("##### 💵 حركة الحسابات المالية (واردات vs صادرات)")
            fin_df = safe_read_sql("SELECT trans_type, SUM(amount) as total FROM financial_transactions GROUP BY trans_type")
            if not fin_df.empty:
                st.bar_chart(data=fin_df.set_index("trans_type"))
            else:
                st.info("لا توجد معاملات مالية مسجلة للرسم البياني.")

    # ----------------------------------------------------
    # 3️⃣ قسم الإدارة المالية الشاملة
    # ----------------------------------------------------
    elif selected_page == "💰 قسم الإدارة المالية الشاملة":
        st.markdown("<h1 class='main-header'>💰 الإدارة المالية وحاسبة المستحقات السريعة</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["🧮 حاسبة المستحقات والعمالة", "💸 الصادرات والواردات", "💳 إدارة السلف الخصم", "📜 كشف حساب الأقسام"])

        with tab1:
            st.subheader("🧮 حاسبة الساعات واليوميات والعمالة مع الموردين")
            col_a, col_b = st.columns(2)
            with col_a:
                craft_sel = st.selectbox("نوع العامل / المهنة", ["نقاش", "نحات", "عامل", "مورد عمال", "فنّي صيانة", "أخرى"])
                workers_cnt = st.number_input("عدد العمال المتواجدين", min_value=1, value=1)
                pay_mode = st.radio("نظام الحساب", ["بالساعة", "باليومية الأساسية"])
            with col_b:
                if pay_mode == "بالساعة":
                    h_rate = st.number_input("سعر الساعة الواحدة (EGP)", min_value=0.0)
                    h_worked = st.number_input("عدد الساعات المنجزة", min_value=0.0)
                    total_calc = h_rate * h_worked * workers_cnt
                else:
                    d_rate = st.number_input("سعر اليومية الأساسية (EGP)", min_value=0.0)
                    days_w = st.number_input("عدد الأيام", min_value=0.0, value=1.0)
                    total_calc = d_rate * days_w * workers_cnt

            st.markdown(f"### 💵 إجمالي المستحق النهائي: **{total_calc:,.2f} EGP**")

        with tab2:
            st.subheader("📊 تسجيل الصادرات والواردات المالية")
            with st.form("financial_trans_form"):
                t_type = st.selectbox("نوع المعاملة", ["صادرات (مصروفات)", "واردات (إيرادات)"])
                t_dept = st.selectbox("القسم التابع له", ["العقارات", "الموارد البشرية", "المستثمرين", "IT Support", "عام"])
                t_amount = st.number_input("المبلغ (EGP)", min_value=0.0)
                t_desc = st.text_input("وصف المعاملة / البيان")
                if st.form_submit_button("حفظ المعاملة المالية"):
                    if t_amount > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO financial_transactions (trans_type, department, amount, description, trans_date) VALUES (?, ?, ?, ?, ?)",
                                (t_type, t_dept, t_amount, t_desc, str(datetime.date.today()))
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المالية", f"تسجيل معاملة {t_type} بمبلغ {t_amount}")
                        st.success("تم تسجيل المعاملة المالية بنجاح!")
                        st.rerun()

        with tab3:
            st.subheader("💳 تسليم وإدارة سلف الموظفين والعمال")
            with st.form("advances_form"):
                adv_id = st.text_input("ID الموظف / العامل")
                adv_name = st.text_input("اسم الموظف / العامل")
                adv_amt = st.number_input("مبلغ السلفة (EGP)", min_value=0.0)
                adv_notes = st.text_area("ملاحظات / سبب السلفة")
                if st.form_submit_button("تسجيل السلفة"):
                    if adv_name and adv_amt > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO employee_advances (emp_custom_id, emp_name, advance_amount, notes, date_given) VALUES (?, ?, ?, ?, ?)",
                                (adv_id, adv_name, adv_amt, adv_notes, str(datetime.date.today()))
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المالية", f"تسجيل سلفة للموظف {adv_name}")
                        st.success("تم تسجيل السلفة بنجاح!")
                        st.rerun()

            st.write("##### 📋 سجل السلف المسجلة")
            st.dataframe(safe_read_sql("SELECT * FROM employee_advances"), use_container_width=True)

        with tab4:
            st.subheader("📜 كشف حساب تفصيلي لكل قسم")
            dept_filter = st.selectbox("اختر القسم لعرض كشف الحساب:", ["الكل", "العقارات", "الموارد البشرية", "المستثمرين", "IT Support", "عام"])
            if dept_filter == "الكل":
                df_kashf = safe_read_sql("SELECT * FROM financial_transactions")
            else:
                df_kashf = safe_read_sql("SELECT * FROM financial_transactions WHERE department = ?", (dept_filter,))
            st.dataframe(df_kashf, use_container_width=True)

    # ----------------------------------------------------
    # 4️⃣ قسم الموارد البشرية والعمالة (HR)
    # ----------------------------------------------------
    elif selected_page == "👷 قسم الموارد البشرية والعمالة (HR)":
        st.markdown("<h1 class='main-header'>👷 قسم الموارد البشرية والعمالة والأرشيف</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📋 سجل الموظفين والعمال والموردين", "➕ إضافة كادر / مورد جديد", "📁 مرفقات ومستندات العمالة"])

        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)

        with tab2:
            st.subheader("➕ إضافة جديد برقم ID مخصص")
            with st.form("hr_add_emp"):
                c_id = st.text_input("رقم ID المخصص (Unique ID)", value=f"EMP-{random.randint(1000, 9999)}")
                e_name = st.text_input("الاسم الكامل")
                e_type = st.selectbox("الفئة", ["موظف ثابت", "مورد عمال", "عامل مستقل"])
                c_type = st.selectbox("التخصص / المهنة", ["نقاش", "نحات", "عامل", "مشرف", "إداري", "أخرى"])
                h_rate = st.number_input("سعر الساعة (EGP)", min_value=0.0)
                h_worked = st.number_input("ساعات العمل", min_value=0.0)
                d_rate = st.number_input("سعر اليومية (EGP)", min_value=0.0)
                w_cnt = st.number_input("عدد العمال التابعين له", min_value=1, value=1)
                
                tot_pay = (h_rate * h_worked * w_cnt) if h_rate > 0 else (d_rate * w_cnt)

                if st.form_submit_button("حفظ البيانات"):
                    if e_name and c_id:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute(
                                    "INSERT INTO employees (custom_id, name, emp_type, craft_type, hourly_rate, hours_worked, daily_rate, workers_count, total_pay, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (c_id, e_name, e_type, c_type, h_rate, h_worked, d_rate, w_cnt, tot_pay, str(datetime.date.today()))
                                )
                                conn.commit()
                            log_audit_action(st.session_state["username"], "HR", f"إضافة موظف/عامل {e_name} - ID: {c_id}")
                            st.success("تم حفظ بيانات الكادر بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("رقم الـ ID مستخدم مسبقاً!")

        with tab3:
            st.subheader("📁 أرشفة مستندات ومرفقات العمالة")
            with st.form("hr_doc_form"):
                doc_cid = st.text_input("رقم ID الخاص بالموضف / العامل")
                doc_type = st.selectbox("نوع المستند", ["عقد عمل", "بطاقة الرقم القومي", "شهادة صحية", "فيش وتشبيه", "أخرى"])
                uploaded_file = st.file_uploader("اختر المستند مرفق")
                if st.form_submit_button("رفع وأرشفة المستند"):
                    if doc_cid and uploaded_file:
                        file_bytes = uploaded_file.read()
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO hr_documents (custom_id, doc_type, file_name, upload_date, file_data) VALUES (?, ?, ?, ?, ?)",
                                (doc_cid, doc_type, uploaded_file.name, str(datetime.date.today()), file_bytes)
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "HR", f"أرشفة مستند {doc_type} لـ ID: {doc_cid}")
                        st.success("تم رفع المستند وأرشفته بنجاح!")
                        st.rerun()

            st.write("##### 📜 المستندات المرفوعة")
            st.dataframe(safe_read_sql("SELECT id, custom_id, doc_type, file_name, upload_date FROM hr_documents"), use_container_width=True)

    # ----------------------------------------------------
    # 5️⃣ قسم العقارات والمخزون
    # ----------------------------------------------------
    elif selected_page == "🏢 قسم العقارات والمخزون":
        st.markdown("<h1 class='main-header'>🏢 إدارة العقارات والمخزون الأرباح</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 قائمة العقارات وحساب الأرباح", "➕ تسجيل عقار جديد"])

        with tab1:
            df_p = safe_read_sql("SELECT * FROM properties")
            if not df_p.empty:
                df_p["صافي الأرباح المتوقعة"] = df_p["sale_price"] - (df_p["price"] + df_p["expenses"])
            st.dataframe(df_p, use_container_width=True)

        with tab2:
            with st.form("add_property_form"):
                p_cid = st.text_input("رقم ID العقار الفريد", value=f"PROP-{random.randint(100, 999)}")
                p_name = st.text_input("اسم العقار / المشروع")
                p_loc = st.text_input("الموقع")
                p_price = st.number_input("سعر الشراء الأساسي (EGP)", min_value=0.0)
                p_finish = st.selectbox("نوع التشطيب", ["بدون تشطيب (محارة)", "نصف تشطيب", "تشطيب سوبر لوكس", "ألترا لوكس"])
                p_expenses = st.number_input("المصروفات على العقار (EGP)", min_value=0.0)
                p_sale = st.number_input("سعر البيع المقدر (EGP)", min_value=0.0)
                p_status = st.selectbox("حالة العقار", ["متاح", "تم البيع", "تحت التطوير"])

                if st.form_submit_button("حفظ العقار"):
                    if p_cid and p_name:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute(
                                    "INSERT INTO properties (custom_id, name, location, price, finishing_type, expenses, sale_price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (p_cid, p_name, p_loc, p_price, p_finish, p_expenses, p_sale, p_status)
                                )
                                conn.commit()
                            log_audit_action(st.session_state["username"], "العقارات", f"إضافة عقار جديد {p_name} - ID: {p_cid}")
                            st.success("تم تسجيل العقار بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("رقم ID العقار مكرر!")

    # ----------------------------------------------------
    # 6️⃣ قسم المستثمرين والأرباح
    # ----------------------------------------------------
    elif selected_page == "🤝 قسم المستثمرين والأرباح":
        st.markdown("<h1 class='main-header'>🤝 قسم المستثمرين وحساب عوائد الأسهم</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📊 سجل المستثمرين والأرباح", "➕ تسجيل مستثمر جديد"])

        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM investors"), use_container_width=True)

        with tab2:
            with st.form("add_investor_form"):
                inv_name = st.text_input("اسم المستثمر")
                prop_cid = st.text_input("رقم ID العقار المستثمر فيه")
                inv_amt = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                inv_ratio = st.number_input("نسبة المشاركة في العقار (%)", min_value=0.0, max_value=100.0)
                ret_rate = st.number_input("نسبة العائد المتوقع (%)", min_value=0.0)

                tot_returns = inv_amt + (inv_amt * (ret_rate / 100.0))

                if st.form_submit_button("حفظ المستثمر"):
                    if inv_name and prop_cid:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO investors (name, property_custom_id, investment_amount, investment_ratio, return_rate, total_returns, start_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (inv_name, prop_cid, inv_amt, inv_ratio, ret_rate, tot_returns, str(datetime.date.today()))
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المستثمرين", f"إضافة مستثمر {inv_name} على عقار ID: {prop_cid}")
                        st.success("تم تسجيل بيانات المستثمر وحساب الأرباح بنجاح!")
                        st.rerun()

    # ----------------------------------------------------
    # 7️⃣ قسم تقنية المعلومات (IT Support)
    # ----------------------------------------------------
    elif selected_page == "💻 قسم تقنية المعلومات (IT Support)":
        st.markdown("<h1 class='main-header'>💻 قسم IT Support وإدارة الكوادر الفنية</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["👥 كادر IT وساعات العمل", "➕ إضافة موظف IT", "📁 مرفقات ومستندات IT"])

        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM it_staff"), use_container_width=True)

        with tab2:
            with st.form("add_it_staff"):
                it_cid = st.text_input("رقم ID موظف الـ IT", value=f"IT-{random.randint(100, 999)}")
                it_name = st.text_input("اسم الموظف / المهندس")
                it_d_rate = st.number_input("سعر اليومية (EGP)", min_value=0.0)
                it_h_rate = st.number_input("سعر الساعة (EGP)", min_value=0.0)
                it_h_worked = st.number_input("عدد ساعات العمل", min_value=0.0)

                it_pay = (it_h_rate * it_h_worked) if it_h_rate > 0 else it_d_rate

                if st.form_submit_button("حفظ موظف IT"):
                    if it_cid and it_name:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute(
                                    "INSERT INTO it_staff (custom_id, name, daily_rate, hourly_rate, hours_worked, total_pay) VALUES (?, ?, ?, ?, ?, ?)",
                                    (it_cid, it_name, it_d_rate, it_h_rate, it_h_worked, it_pay)
                                )
                                conn.commit()
                            log_audit_action(st.session_state["username"], "IT", f"إضافة موظف IT {it_name} - ID: {it_cid}")
                            st.success("تم تسجل موظف IT بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("رقم ID مستخدم مسبقاً!")

        with tab3:
            with st.form("it_doc_form"):
                it_dcid = st.text_input("رقم ID موظف الـ IT")
                it_dtype = st.selectbox("نوع المستند", ["ترخيص برمجيات", "عقد صيانة", "شهادة خبرة", "أخرى"])
                it_file = st.file_uploader("مرفق المستند الفني")
                if st.form_submit_button("رفع المستند الفني"):
                    if it_dcid and it_file:
                        file_bytes = it_file.read()
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO it_documents (custom_id, doc_type, file_name, upload_date, file_data) VALUES (?, ?, ?, ?, ?)",
                                (it_dcid, it_dtype, it_file.name, str(datetime.date.today()), file_bytes)
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "IT", f"رفع مستند فني {it_dtype} لـ ID: {it_dcid}")
                        st.success("تم حفظ المستند الفني!")
                        st.rerun()

    # ----------------------------------------------------
    # 8️⃣ قسم سجل العمليات والمراقبة (Audit Logs)
    # ----------------------------------------------------
    elif selected_page == "⏱️ قسم سجل العمليات والمراقبة":
        st.markdown("<h1 class='main-header'>⏱️ سجل العمليات والأنشطة والمحاولات (Audit Trail)</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📜 جميع الأنشطة والمحاولات", "🟢 الأقسام النشطة والتواجد"])

        with tab1:
            st.subheader("سجل محاولات الدخول والعمليات (الناجحة والعمليات الفاشلة)")
            df_logs = safe_read_sql("SELECT * FROM audit_logs ORDER BY id DESC")
            st.dataframe(df_logs, use_container_width=True)

        with tab2:
            st.subheader("حالة الأقسام النشطة حالياً")
            active_s = safe_read_sql("SELECT username, login_time, ip_address FROM user_sessions WHERE status = 'نشطة'")
            st.success(f"عدد المستخدمين النشطين المتواجدين حالياً: **{len(active_s)}**")
            st.dataframe(active_s, use_container_width=True)

    # ----------------------------------------------------
    # 9️⃣ قسم الإبلاغ عن مشكلة (Helpdesk)
    # ----------------------------------------------------
    elif selected_page == "⚠️ قسم الإبلاغ عن مشكلة (Helpdesk)":
        st.markdown("<h1 class='main-header'>⚠️ قسم الإبلاغ عن المشاكل والدعم الفني</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["➕ تقديم بلاغ / تذكرة جديد", "📋 متابعة التذاكر والبلاغات"])

        with tab1:
            with st.form("report_issue_form"):
                issue_cat = st.selectbox("تصنيف المشكلة", ["مشكلة مالية", "مشكلة في الحسابات", "عطل بالمنظومة / IT", "مشكلة في بيانات العمالة", "أخرى"])
                issue_desc = st.text_area("وصف المشكلة بالتفصيل")
                doc_t = st.selectbox("نوع المستند المرفق (إن وجد)", ["لا يوجد", "صورة الشاشة (Screenshot)", "ملف PDF", "مستند ورد"])
                issue_file = st.file_uploader("إرفاق ملف / مستند مع المشكلة")

                if st.form_submit_button("إرسال البلاغ"):
                    if issue_desc:
                        f_bytes = issue_file.read() if issue_file else None
                        f_name = issue_file.name if issue_file else "بدون ملف"
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO problem_reports (reporter_username, issue_category, description, doc_type, file_name, file_data, status, report_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (st.session_state["username"], issue_cat, issue_desc, doc_t, f_name, f_bytes, "قيد المعالجة", str(datetime.date.today()))
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "الدعم الفني", f"بلاغ عن مشكلة {issue_cat}")
                        st.success("تم إرسال البلاغ بنجاح إلى قسم الدعم والمطورين!")
                        st.rerun()

        with tab2:
            st.subheader("📋 قائمة المشاكل والبلاغات المسجلة")
            df_reports = safe_read_sql("SELECT id, reporter_username, issue_category, description, doc_type, file_name, status, report_date FROM problem_reports ORDER BY id DESC")
            st.dataframe(df_reports, use_container_width=True)
