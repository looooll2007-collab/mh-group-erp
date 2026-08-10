import datetime
import random
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. الثيمات وإعدادات الصفحة
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
}

st.set_page_config(
    page_title="MH Group ERP System - Enterprise Edition",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 مجموعة شركات MH Group ERP",
        "subtitle": "🔐 بوابة الدخول الموحدة للمجموعة",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
    }

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الداكن الملكي والذهبي (Royal Dark & Gold)"

current_theme = THEMES[st.session_state["selected_theme"]]

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
# 2. قواعد البيانات والدوال المساعدة
# ==========================================
def get_ip_address():
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            if "X-Forwarded-For" in headers:
                return headers["X-Forwarded-For"].split(",")[0]
    except Exception:
        pass
    return "127.0.0.1"

def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)

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
            un = username_input.strip()
            pw = password_input.strip()
            with sqlite3.connect("mh_group_erp.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (un, pw))
                res = cursor.fetchone()

            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = un

                login_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_ip = get_ip_address()
                with sqlite3.connect("mh_group_erp.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO user_sessions (username, login_time, logout_time, ip_address, status) VALUES (?, ?, ?, ?, ?)",
                        (un, login_now, "نشطة حالياً", user_ip, "نشطة")
                    )
                    conn.commit()
                    st.session_state["session_id"] = cur.lastrowid

                log_audit_action(un, "تسجيل الدخول", f"تسجيل دخول بصلاحية: {res[0]}")
                st.success(f"تم تسجيل الدخول بنجاح! مرحباً بك ({res[0]})")
                st.rerun()
            else:
                log_audit_action(un or "مجهول", "تسجيل الدخول", "محاولة دخول ببيانات خاطئة", "فاشلة")
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

# ==========================================
# 4. التحكم بالصلاحيات والأقسام
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(f"**المستخدم:** `{st.session_state['username']}`\n\n**الصلاحية:** `{st.session_state['user_role']}`")

    role = st.session_state["user_role"]
    allowed_pages = []

    if role == "Admin":
        allowed_pages = [
            "📊 لوحة التحليلات والداشبورد",
            "⚙️ قسم إدارة المستخدمين والـ IP",
            "💰 قسم الإدارة المالية الشاملة",
            "👷 قسم الموارد البشرية والعمالة (HR)",
            "🏢 قسم العقارات والمخزون",
            "🤝 قسم المستثمرين والأرباح",
            "⏱️ قسم سجل العمليات والمراقبة (Audit Logs)"
        ]
    elif role == "Finance":
        allowed_pages = ["💰 قسم الإدارة المالية الشاملة"]
    elif role == "HR":
        allowed_pages = ["👷 قسم الموارد البشرية والعمالة (HR)"]
    elif role == "RealEstate":
        allowed_pages = ["🏢 قسم العقارات والمخزون"]
    elif role == "Investor":
        allowed_pages = ["🤝 قسم المستثمرين والأرباح"]
    else:
        allowed_pages = ["📊 لوحة التحليلات والداشبورد"]

    selected_page = st.sidebar.radio("القائمة المتاحة لصلاحيتك:", allowed_pages)

    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        if st.session_state["session_id"]:
            logout_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute("UPDATE user_sessions SET logout_time = ?, status = 'منتهية' WHERE id = ?", (logout_now, st.session_state["session_id"]))
                conn.commit()
        log_audit_action(st.session_state["username"], "تسجيل الخروج", "تسجيل خروج آمن من النظام")
        st.session_state["logged_in"] = False
        st.session_state["session_id"] = None
        st.rerun()

    # 1️⃣ قسم المستخدمين والـ IP
    if selected_page == "⚙️ قسم إدارة المستخدمين والـ IP":
        st.markdown("<h1 class='main-header'>⚙️ إدارة المستخدمين وصلاحيات الدخول والـ IP</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["👥 الحسابات والصلاحيات", "➕ إضافة مستخدم جديد", "📡 إدارة سجل الجلسات وحذف الـ IP"])

        with tab1:
            df_users = safe_read_sql("SELECT id, username, role, phone FROM users")
            st.dataframe(df_users, use_container_width=True)
            st.markdown("---")
            st.write("### 🗑️ حذف مستخدم")
            user_to_del = st.selectbox("اختر المستخدم للحذف:", options=[""] + df_users["username"].tolist())
            if st.button("تأكيد حذف الحساب"):
                if user_to_del and user_to_del != "admin":
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                        conn.commit()
                    log_audit_action(st.session_state["username"], "إدارة المستخدمين", f"حذف حساب {user_to_del}")
                    st.success(f"تم حذف الحساب {user_to_del} بنجاح!")
                    st.rerun()

        with tab2:
            with st.form("add_user_f"):
                nu = st.text_input("اسم المستخدم")
                np = st.text_input("كلمة المرور", type="password")
                nr = st.selectbox("الصلاحية المخصصة للقسم", ["HR", "Finance", "RealEstate", "Investor", "Admin"])
                nph = st.text_input("رقم الهاتف")
                if st.form_submit_button("إضافة الحساب"):
                    if nu and np:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)", (nu.strip(), np.strip(), nr, nph))
                                conn.commit()
                            log_audit_action(st.session_state["username"], "إدارة المستخدمين", f"إنشاء حساب {nu} بصلاحية {nr}")
                            st.success(f"تم إضافة المستخدم {nu} بصلاحية {nr} بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مكرر!")

        with tab3:
            st.subheader("📡 سجل الجلسات المباشرة وإدارة الـ IPs")
            df_sessions = safe_read_sql("SELECT * FROM user_sessions ORDER BY id DESC")
            st.dataframe(df_sessions, use_container_width=True)

            c1, c2 = st.columns(2)
            with c1:
                st.write("#### 🗑️ حذف جلسة برقم ID")
                sess_id_del = st.number_input("أدخل ID الجلسة للحذف:", min_value=1, step=1)
                if st.button("حذف الجلسة"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM user_sessions WHERE id = ?", (sess_id_del,))
                        conn.commit()
                    log_audit_action(st.session_state["username"], "الأمان والـ IP", f"حذف الجلسة رقم {sess_id_del}")
                    st.success(f"تم حذف الجلسة {sess_id_del}!")
                    st.rerun()

            with c2:
                st.write("#### 🚫 مسح جلسات IP معين")
                ip_to_del = st.text_input("أدخل IP للـ مسح:")
                if st.button("مسح كافة سجلات الـ IP"):
                    if ip_to_del:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("DELETE FROM user_sessions WHERE ip_address = ?", (ip_to_del,))
                            conn.commit()
                        log_audit_action(st.session_state["username"], "الأمان والـ IP", f"مسح جميع جلسات الـ IP: {ip_to_del}")
                        st.success(f"تم مسح جلسات الـ IP {ip_to_del} بنجاح!")
                        st.rerun()

    # 2️⃣ قسم الإدارة المالية + الحاسبة
    elif selected_page == "💰 قسم الإدارة المالية الشاملة":
        st.markdown("<h1 class='main-header'>💰 الإدارة المالية وحاسبة المستحقات والعمالة</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🧮 حاسبة المستحقات والعمالة (مع الحفظ)", "💸 تسجيل المصروفات والواردات", "📜 كشف الحسابات المالية"])

        with tab1:
            st.subheader("🧮 حاسبة العمل وتوثيق مستحقات الموردين والعمالة")
            with st.form("calc_and_save_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    worker_name = st.text_input("اسم العامل / المورد / الجهة", value="مورد عمالة")
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
                notes_calc = st.text_input("بيان / ملاحظات إضافية للمستند", value=f"مستحقات {craft_sel} - العدد {workers_cnt}")
                
                submit_calc = st.form_submit_button("💾 حفظ المستحق في المصروفات المالية والسجل")
                
                if submit_calc:
                    if total_calc > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO financial_transactions (trans_type, department, amount, description, trans_date) VALUES (?, ?, ?, ?, ?)",
                                ("صادرات (مصروفات)", "الموارد البشرية والعمالة", total_calc, f"{worker_name} - {notes_calc}", str(datetime.date.today()))
                            )
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المالية والعمالة", f"حفظ مستحقات بقيمة {total_calc} EGP لـ {worker_name}")
                        st.success("تم حفظ الحركة المالية وتسجيلها بالسجل بنجاح!")
                        st.rerun()
                    else:
                        st.error("يرجى إدخال قيم صالحة للحساب!")

        with tab2:
            st.subheader("📊 تسجيل الصادرات والواردات")
            with st.form("fin_form"):
                ttype = st.selectbox("نوع المعاملة", ["صادرات (مصروفات)", "واردات (إيرادات)"])
                tdept = st.selectbox("القسم التابع له", ["العقارات", "الموارد البشرية", "المستثمرين", "عام"])
                tamt = st.number_input("المبلغ (EGP)", min_value=0.0)
                tdesc = st.text_input("الوصف / البيان")
                if st.form_submit_button("حفظ المعاملة"):
                    if tamt > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO financial_transactions (trans_type, department, amount, description, trans_date) VALUES (?, ?, ?, ?, ?)",
                                         (ttype, tdept, tamt, tdesc, str(datetime.date.today())))
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المالية", f"تسجيل {ttype} بمبلغ {tamt}")
                        st.success("تم الحفظ بنجاح!")
                        st.rerun()

        with tab3:
            st.subheader("📜 كشف الحسابات الموثقة")
            st.dataframe(safe_read_sql("SELECT * FROM financial_transactions ORDER BY id DESC"), use_container_width=True)

    # 3️⃣ قسم الموارد البشرية والعمالة
    elif selected_page == "👷 قسم الموارد البشرية والعمالة (HR)":
        st.markdown("<h1 class='main-header'>👷 قسم الموارد البشرية والعمالة</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 سجل الكادر والعمالة", "➕ إضافة كادر جديد"])

        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)

        with tab2:
            with st.form("add_emp_form"):
                cid = st.text_input("ID الفريد", value=f"EMP-{random.randint(1000, 9999)}")
                ename = st.text_input("اسم العامل / الموظف")
                etype = st.selectbox("الفئة", ["موظف ثابت", "مورد عمال", "عامل مستقل"])
                ctype = st.selectbox("التخصص", ["نقاش", "نحات", "عامل", "مشرف", "إداري"])
                hrate = st.number_input("سعر الساعة", min_value=0.0)
                drate = st.number_input("سعر اليومية", min_value=0.0)
                wcnt = st.number_input("عدد العمال", min_value=1, value=1)
                
                tot = (hrate * 8 * wcnt) if hrate > 0 else (drate * wcnt)

                if st.form_submit_button("حفظ البيانات"):
                    if ename:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO employees (custom_id, name, emp_type, craft_type, hourly_rate, daily_rate, workers_count, total_pay, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                         (cid, ename, etype, ctype, hrate, drate, wcnt, tot, str(datetime.date.today())))
                            conn.commit()
                        log_audit_action(st.session_state["username"], "HR", f"إضافة كادر جديد: {ename}")
                        st.success("تم الحفظ بنجاح!")
                        st.rerun()

    # 4️⃣ قسم العقارات والمخزون
    elif selected_page == "🏢 قسم العقارات والمخزون":
        st.markdown("<h1 class='main-header'>🏢 قسم إدارة العقارات والمشاريع</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 العقارات المسجلة", "➕ إضافة عقار جديد"])

        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)

        with tab2:
            with st.form("add_prop_f"):
                pid = st.text_input("ID العقار", value=f"PROP-{random.randint(100, 999)}")
                pname = st.text_input("اسم المشروع / العقار")
                ploc = st.text_input("الموقع")
                pprice = st.number_input("سعر الشراء", min_value=0.0)
                pexp = st.number_input("المصروفات", min_value=0.0)
                psale = st.number_input("سعر البيع المتوقع", min_value=0.0)
                if st.form_submit_button("حفظ العقار"):
                    if pname:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO properties (custom_id, name, location, price, expenses, sale_price, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                         (pid, pname, ploc, pprice, pexp, psale, "متاح"))
                            conn.commit()
                        log_audit_action(st.session_state["username"], "العقارات", f"إضافة عقار: {pname}")
                        st.success("تم الحفظ!")
                        st.rerun()

    # 5️⃣ قسم المستثمرين (مكتمل بالنماذج)
    elif selected_page == "🤝 قسم المستثمرين والأرباح":
        st.markdown("<h1 class='main-header'>🤝 قسم المستثمرين وحساب الأرباح</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 سجل المستثمرين", "➕ إضافة مستثمر جديد"])

        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM investors ORDER BY id DESC"), use_container_width=True)

        with tab2:
            df_props = safe_read_sql("SELECT custom_id, name FROM properties")
            prop_options = df_props["custom_id"].tolist() if not df_props.empty else ["عام"]

            with st.form("add_investor_form"):
                inv_name = st.text_input("اسم المستثمر")
                prop_id = st.selectbox("العقار / المشروع المرتبط", prop_options)
                inv_amt = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                inv_ratio = st.number_input("نسبة المشاركة (%)", min_value=0.0, max_value=100.0)
                return_rate = st.number_input("نسبة العائد المتوقع (%)", min_value=0.0)
                
                tot_returns = inv_amt * (1 + (return_rate / 100))

                if st.form_submit_button("حفظ بيانات المستثمر"):
                    if inv_name and inv_amt > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO investors (name, property_custom_id, investment_amount, investment_ratio, return_rate, total_returns, start_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                         (inv_name, prop_id, inv_amt, inv_ratio, return_rate, tot_returns, str(datetime.date.today())))
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المستثمرين", f"إضافة مستثمر: {inv_name}")
                        st.success("تم حفظ بيانات المستثمر بنجاح!")
                        st.rerun()

    # 6️⃣ سجل العمليات
    elif selected_page == "⏱️ قسم سجل العمليات والمراقبة (Audit Logs)":
        st.markdown("<h1 class='main-header'>⏱️ سجل العمليات والأنشطة المحدث (Audit Trail)</h1>", unsafe_allow_html=True)
        
        c_b1, c_b2 = st.columns([1, 5])
        with c_b1:
            if st.button("🔄 تحديث السجل"):
                st.rerun()
        with c_b2:
            if st.button("🗑️ تفريغ كافة السجلات"):
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("DELETE FROM audit_logs")
                    conn.commit()
                st.success("تم تفريغ السجل بالكامل!")
                st.rerun()

        df_logs = safe_read_sql("SELECT id, username, department, action, status, ip_address, timestamp FROM audit_logs ORDER BY id DESC")
        st.dataframe(df_logs, use_container_width=True)

    # 7️⃣ لوحة التحليلات
    elif selected_page == "📊 لوحة التحليلات والداشبورد":
        st.markdown("<h1 class='main-header'>📊 لوحة التحليلات التنفيذية والملخص العام</h1>", unsafe_allow_html=True)
        st.info("مرحباً بك في المنظومة. الأقسام المعروضة في القائمة الجانبية مخصصة وفقاً لصلاحيتك الحالية.")
