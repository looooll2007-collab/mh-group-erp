import datetime
import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والثيمات المؤسسية
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

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الداكن الملكي والذهبي (Royal Dark & Gold)"

current_theme = THEMES.get(st.session_state["selected_theme"], THEMES["الداكن الملكي والذهبي (Royal Dark & Gold)"])

st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {current_theme["bg"]} !important;
        color: {current_theme["text"]} !important;
    }}
    .main-header {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {current_theme["primary"]} !important;
        text-align: right;
        margin-bottom: 15px;
        padding: 10px;
        border-bottom: 2px solid {current_theme["accent"]};
        background-color: {current_theme["card"]};
        border-radius: 8px;
    }}
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important;
        padding: 12px !important;
        border-radius: 10px !important;
        border: 1px solid {current_theme["border"]} !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {current_theme["card"]} !important;
        border-right: 1px solid {current_theme["border"]} !important;
    }}
    .stButton>button {{
        background-color: {current_theme["primary"]} !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: bold !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)

UPLOAD_DIR = "uploads_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 2. قاعدة البيانات والجداول والهجرة التلقائية
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT,
                email TEXT,
                avatar_path TEXT
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS department_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT,
                filename TEXT,
                uploader TEXT,
                upload_date TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                department TEXT,
                issue_text TEXT,
                status TEXT,
                ticket_date TEXT
            )
        """)

        migrations = [
            ("users", "phone", "TEXT"),
            ("users", "email", "TEXT"),
            ("users", "avatar_path", "TEXT"),
            ("employees", "custom_id", "TEXT"),
            ("employees", "name", "TEXT"),
            ("employees", "emp_type", "TEXT"),
            ("employees", "craft_type", "TEXT"),
            ("employees", "hourly_rate", "REAL"),
            ("employees", "daily_rate", "REAL"),
            ("employees", "workers_count", "INTEGER DEFAULT 1"),
            ("employees", "total_pay", "REAL"),
            ("employees", "hire_date", "TEXT"),
            ("properties", "custom_id", "TEXT"),
            ("properties", "name", "TEXT"),
            ("properties", "location", "TEXT"),
            ("properties", "price", "REAL"),
            ("properties", "expenses", "REAL DEFAULT 0.0"),
            ("properties", "sale_price", "REAL DEFAULT 0.0"),
            ("properties", "status", "TEXT"),
        ]
        
        for table, col, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, phone, email, avatar_path) VALUES ('admin', 'admin123', 'Admin', '01000000000', 'admin@mhgroup.com', '')")

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
        ip = "127.0.0.1"
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            if "X-Forwarded-For" in headers:
                ip = headers["X-Forwarded-For"].split(",")[0]
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
# 3. تسجيل الدخول
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
    st.markdown("<h1 class='main-header' style='text-align: center;'>🏢 مجموعة شركات MH Group ERP</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 بوابة الدخول الموحدة للمجموعة")
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button("تسجيل الدخول", use_container_width=True):
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
                with sqlite3.connect("mh_group_erp.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO user_sessions (username, login_time, logout_time, ip_address, status) VALUES (?, ?, ?, ?, ?)",
                        (un, login_now, "نشطة حالياً", "127.0.0.1", "نشطة")
                    )
                    conn.commit()
                    st.session_state["session_id"] = cur.lastrowid

                log_audit_action(un, "الدخول", f"تسجيل دخول بصلاحية: {res[0]}")
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")

if not st.session_state["logged_in"]:
    login_page()
else:
    user_rec = safe_read_sql("SELECT phone, email, avatar_path FROM users WHERE username = ?", (st.session_state["username"],))
    user_avatar = user_rec.iloc[0]["avatar_path"] if not user_rec.empty and "avatar_path" in user_rec.columns and user_rec.iloc[0]["avatar_path"] else None

    st.sidebar.title("🏢 MH Group ERP")
    if user_avatar and os.path.exists(user_avatar):
        st.sidebar.image(user_avatar, width=80)
    st.sidebar.markdown(f"**المستخدم:** `{st.session_state['username']}`\n\n**الصلاحية:** `{st.session_state['user_role']}`")

    role = st.session_state["user_role"]
    allowed_pages = []

    if role == "Admin":
        allowed_pages = [
            "📊 لوحة التحليلات التنفيذية",
            "⚙️ المستخدمون والجلسات والـ IP",
            "💰 الإدارة المالية",
            "👷 الموارد البشرية",
            "🏢 العقارات والمشاريع",
            "🤝 المستثمرين",
            "⏱️ سجل العمليات",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ]
    elif role == "HR":
        allowed_pages = [
            "👷 الموارد البشرية",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ]
    elif role == "Finance":
        allowed_pages = [
            "💰 الإدارة المالية",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ]
    elif role == "RealEstate":
        allowed_pages = [
            "🏢 العقارات والمشاريع",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ]
    elif role == "Investor":
        allowed_pages = [
            "🤝 المستثمرين",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ]
    else:
        allowed_pages = [
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ]

    selected_page = st.sidebar.radio("الأقسام:", allowed_pages)

    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        if st.session_state["session_id"]:
            logout_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute("UPDATE user_sessions SET logout_time = ?, status = 'منتهية' WHERE id = ?", (logout_now, st.session_state["session_id"]))
                conn.commit()
        log_audit_action(st.session_state["username"], "خروج", "تسجيل خروج آمن")
        st.session_state["logged_in"] = False
        st.session_state["session_id"] = None
        st.rerun()

    def render_department_workspace(dept_name, core_content_func):
        st.markdown(f"<h1 class='main-header'>🏢 قسم: {dept_name}</h1>", unsafe_allow_html=True)
        
        t_op, t_prof, t_files, t_iss = st.tabs([
            f"📋 عمليات {dept_name}", 
            "👤 معلومات الحساب والصورة الشخصية", 
            "📁 رفع تقارير ومستندات القسم", 
            "🛠️ الإبلاغ عن مشكلة بالقسم"
        ])
        
        with t_op:
            core_content_func()
            
        with t_prof:
            st.markdown(f"### 👤 بيانات الحساب والصورة الشخصية (مسجلة من الإدارة - للقراءة فقط)")
            curr = st.session_state["username"]
            df_u = safe_read_sql("SELECT username, phone, email, role, avatar_path FROM users WHERE username = ?", (curr,))
            if df_u.empty:
                df_u = pd.DataFrame([{"username": curr, "phone": "غير متوفر", "email": "غير متوفر", "role": st.session_state["user_role"], "avatar_path": ""}])
            
            c_img, c_txt = st.columns([1, 2])
            with c_img:
                av = df_u.iloc[0]["avatar_path"] if "avatar_path" in df_u.columns else None
                if av and os.path.exists(av):
                    st.image(av, width=130, caption="الصورة الشخصية الحالية")
                else:
                    st.info("لا توجد صورة شخصية مرفوعة.")
            with c_txt:
                st.info("⚠️ هذه المعلومات مسجلة بمعرفة الإدارة ولا يمكن تعديلها من هذه الشاشة.")
                st.markdown(f"**اسم المستخدم:** `{df_u.iloc[0]['username']}`")
                st.markdown(f"**الصلاحية:** `{df_u.iloc[0]['role']}`")
                st.markdown(f"**رقم الهاتف:** `{df_u.iloc[0]['phone'] if 'phone' in df_u.columns and df_u.iloc[0]['phone'] else 'غير متوفر'}`")
                st.markdown(f"**البريد الإلكتروني:** `{df_u.iloc[0]['email'] if 'email' in df_u.columns and df_u.iloc[0]['email'] else 'غير متوفر'}`")

        with t_files:
            st.markdown(f"### 📁 رفع تقارير ومستندات قسم: {dept_name}")
            uploaded_file = st.file_uploader(f"رفع مستند أو تقرير لـ {dept_name}", key=f"up_{dept_name}_{random.randint(1,1000)}")
            if uploaded_file:
                filepath = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("INSERT INTO department_files (department, filename, uploader, upload_date) VALUES (?, ?, ?, ?)",
                                 (dept_name, uploaded_file.name, st.session_state["username"], str(datetime.date.today())))
                    conn.commit()
                log_audit_action(st.session_state["username"], dept_name, f"رفع مستند: {uploaded_file.name}")
                st.success("تم رفع المستند/التقرير بنجاح وتحديث لوحة تحكم الأدمن!")
            
            st.write("#### المستندات والتقارير المرفوعة للقسم:")
            df_files = safe_read_sql("SELECT filename, uploader, upload_date FROM department_files WHERE department = ?", (dept_name,))
            st.dataframe(df_files, use_container_width=True)

        with t_iss:
            st.markdown(f"### 🛠️ الإبلاغ عن مشكلة في قسم: {dept_name}")
            with st.form(f"issue_form_{dept_name}_{random.randint(1,1000)}"):
                issue_desc = st.text_area("تفاصيل المشكلة أو العطل التقني في القسم")
                if st.form_submit_button("إرسال الإبلاغ للإدارة"):
                    if issue_desc:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO support_tickets (username, department, issue_text, status, ticket_date) VALUES (?, ?, ?, ?, ?)",
                                         (st.session_state["username"], dept_name, issue_desc, "معلقة", str(datetime.date.today())))
                            conn.commit()
                        log_audit_action(st.session_state["username"], dept_name, f"إبلاغ عن مشكلة: {issue_desc}")
                        st.success("تم تسجيل الإبلاغ وإرساله لوحة تحكم الأدمن بنجاح!")

    # ==========================================
    # 📊 1. لوحة التحليلات التنفيذية الشاملة (للأدمن فقط)
    # ==========================================
    if selected_page == "📊 لوحة التحليلات التنفيذية":
        st.markdown(f"<h1 class='main-header'>🏢 لوحة التحكم التنفيذية الشاملة (جميع الأقسام)</h1>", unsafe_allow_html=True)
        st.markdown(f"👋 **مرحباً بك يا مدير النظام، {st.session_state['username']}** - متابعة مركزية فورية لبيانات وتقارير ومستندات كافة الأقسام.")

        # استعلامات تجميعية شاملة لكل أقسام الشركة
        df_fin = safe_read_sql("SELECT trans_type, amount, department FROM financial_transactions")
        tot_inc = df_fin[df_fin["trans_type"] == "واردات (إيرادات)"]["amount"].sum() if not df_fin.empty else 0.0
        tot_exp = df_fin[df_fin["trans_type"] == "صادرات (مصروفات)"]["amount"].sum() if not df_fin.empty else 0.0
        net_prof = tot_inc - tot_exp

        df_props = safe_read_sql("SELECT price, name, location, sale_price, status FROM properties")
        prop_val = df_props["price"].sum() if not df_props.empty else 0.0
        prop_count = len(df_props)

        df_emp = safe_read_sql("SELECT workers_count, total_pay FROM employees")
        total_workers = df_emp["workers_count"].sum() if not df_emp.empty and "workers_count" in df_emp.columns else len(df_emp)
        total_payroll = df_emp["total_pay"].sum() if not df_emp.empty and "total_pay" in df_emp.columns else 0.0

        df_inv = safe_read_sql("SELECT investment_amount, total_returns FROM investors")
        total_investments = df_inv["investment_amount"].sum() if not df_inv.empty and "investment_amount" in df_inv.columns else 0.0

        df_all_files = safe_read_sql("SELECT department, filename, uploader, upload_date FROM department_files ORDER BY id DESC")
        df_all_tickets = safe_read_sql("SELECT id, username, department, issue_text, status, ticket_date FROM support_tickets ORDER BY id DESC")

        # مؤشرات الأداء العليا (Metrics)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("إجمالي الإيرادات", f"{tot_inc:,.0f} ج.م", delta="حسابات المالية")
        with m2:
            st.metric("إجمالي المصروفات", f"{tot_exp:,.0f} ج.م", delta="حسابات المالية")
        with m3:
            st.metric("صافي الأرباح", f"{net_prof:,.0f} ج.م", delta="صافي العمليات")
        with m4:
            st.metric("قيمة العقارات", f"{prop_val:,.0f} ج.م", delta=f"{prop_count} عقار مسجل")

        m5, m6, m7, m8 = st.columns(4)
        with m5:
            st.metric("إجمالي الاستثمارات", f"{total_investments:,.0f} ج.م", delta="قسم المستثمرين")
        with m6:
            st.metric("إجمالي أجور العمالة", f"{total_payroll:,.0f} ج.م", delta="الموارد البشرية")
        with m7:
            st.metric("إجمالي التقارير والمستندات", f"{len(df_all_files)} مستند مرفوع", delta="جميع الأقسام")
        with m8:
            st.metric("إجمالي الإبلاغات والأعطال", f"{len(df_all_tickets)} إبلاغ", delta="متابعة الأعطال")

        st.markdown("---")

        # تبويبات متقدمة لمراجعة بيانات كافة الأقسام من لوحة الأدمن مباشرة
        tab_charts, tab_files, tab_tickets, tab_all_data = st.tabs([
            "📈 التحليلات والرسوم البيانية", 
            "📁 مستندات وتقارير الأقسام المرفوعة", 
            "🛠️ إبلاغات ومشاكل الأقسام", 
            "📋 جداول بيانات الأقسام الكاملة"
        ])

        with tab_charts:
            c_chart, c_activity = st.columns([2, 1])
            with c_chart:
                st.subheader("📈 نظرة عامة على الأداء المالي")
                if not df_fin.empty:
                    st.line_chart(df_fin, y="amount")
                else:
                    st.info("لا توجد بيانات مالية كافية لعرض الرسم البياني حالياً.")

            with c_activity:
                st.subheader("🔔 النشاط الأخير والعمليات")
                df_logs = safe_read_sql("SELECT action, timestamp FROM audit_logs ORDER BY id DESC LIMIT 5")
                if not df_logs.empty:
                    for idx, row in df_logs.iterrows():
                        st.markdown(f"- **{row['action']}**  \n  <small style='color: gray;'>{row['timestamp']}</small>", unsafe_allow_html=True)
                else:
                    st.info("لا توجد أنشطة مسجلة حديثاً.")

        with tab_files:
            st.subheader("📁 جميع التقارير والمستندات المرفوعة بواسطة الأقسام (تحديث فوري)")
            if not df_all_files.empty:
                st.dataframe(df_all_files, use_container_width=True)
            else:
                st.info("لم يتم رفع أي مستندات أو تقارير من الأقسام حتى الآن.")

        with tab_tickets:
            st.subheader("🛠️ إبلاغات ومشاكل الأقسام المسجلة (تحديث فوري)")
            if not df_all_tickets.empty:
                st.dataframe(df_all_tickets, use_container_width=True)
            else:
                st.info("لا توجد إبلاغات أو أعطال مسجلة من الأقسام.")

        with tab_all_data:
            st.subheader("📋 تفاصيل بيانات الأقسام التشغيلية بالكامل")
            sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs(["العقارات والمشاريع", "الموارد البشرية والعمال", "المستثمرين", "المعاملات المالية"])
            with sub_t1:
                st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)
            with sub_t2:
                st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)
            with sub_t3:
                st.dataframe(safe_read_sql("SELECT * FROM investors"), use_container_width=True)
            with sub_t4:
                st.dataframe(safe_read_sql("SELECT * FROM financial_transactions"), use_container_width=True)

    # ==========================================
    # 👤 الملف الشخصي
    # ==========================================
    elif selected_page == "👤 الملف الشخصي":
        st.markdown("<h1 class='main-header'>👤 الملف الشخصي وإعدادات الحساب</h1>", unsafe_allow_html=True)
        curr_user = st.session_state["username"]
        df_u = safe_read_sql("SELECT username, phone, email, role, avatar_path FROM users WHERE username = ?", (curr_user,))
        
        if df_u.empty:
            df_u = pd.DataFrame([{
                "username": curr_user,
                "phone": "01000000000",
                "email": "user@mhgroup.com",
                "role": st.session_state["user_role"],
                "avatar_path": ""
            }])

        col_img, col_info = st.columns([1, 2])
        with col_img:
            current_av = df_u.iloc[0]["avatar_path"] if "avatar_path" in df_u.columns else None
            if current_av and os.path.exists(current_av):
                st.image(current_av, width=160, caption="الصورة الشخصية الحالية")
            else:
                st.info("لا توجد صورة شخصية مرفوعة حالياً.")
            
            avatar_file = st.file_uploader("رفع أو تغيير الصورة الشخصية", type=["jpg", "png", "jpeg"], key="profile_avatar_upload")
            if avatar_file:
                av_path = os.path.join(UPLOAD_DIR, f"avatar_{curr_user}_{avatar_file.name}")
                with open(av_path, "wb") as f:
                    f.write(avatar_file.getbuffer())
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("UPDATE users SET avatar_path = ? WHERE username = ?", (av_path, curr_user))
                    conn.commit()
                st.success("تم تحديث الصورة الشخصية بنجاح!")
                st.rerun()

        with col_info:
            st.write(f"**اسم المستخدم:** `{df_u.iloc[0]['username']}`")
            st.write(f"**الصلاحية الحالية:** `{df_u.iloc[0]['role']}`")
            
            with st.form("update_profile_form"):
                phone_val = df_u.iloc[0]['phone'] if 'phone' in df_u.columns and df_u.iloc[0]['phone'] else ""
                email_val = df_u.iloc[0]['email'] if 'email' in df_u.columns and df_u.iloc[0]['email'] else ""
                
                new_phone = st.text_input("رقم الهاتف", value=phone_val)
                new_email = st.text_input("البريد الإلكتروني", value=email_val)
                
                st.markdown("---")
                st.subheader("🔑 تغيير كلمة المرور")
                old_pw = st.text_input("كلمة المرور الحالية", type="password")
                new_pw = st.text_input("كلمة المرور الجديدة (اختياري)", type="password")
                confirm_pw = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
                
                if st.form_submit_button("حفظ التحديثات"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        cur = conn.cursor()
                        cur.execute("SELECT password FROM users WHERE username = ?", (curr_user,))
                        res_pw = cur.fetchone()
                        db_pw = res_pw[0] if res_pw else ""
                        
                        if old_pw != db_pw:
                            st.error("كلمة المرور الحالية غير صحيحة!")
                        elif new_pw and new_pw != confirm_pw:
                            st.error("كلمتا المرور الجديدتان غير متطابقتين!")
                        else:
                            final_pw = new_pw if new_pw else db_pw
                            cur.execute("UPDATE users SET password = ?, phone = ?, email = ? WHERE username = ?", (final_pw, new_phone, new_email, curr_user))
                            conn.commit()
                            log_audit_action(curr_user, "الملف الشخصي", "تحديث البيانات الشخصية ووسائل التواصل")
                            st.success("تم تحديث بيانات الملف الشخصي بنجاح!")
                            st.rerun()

    # ==========================================
    # 🎨 الثيمات والألوان
    # ==========================================
    elif selected_page == "🎨 الثيمات والألوان":
        st.markdown("<h1 class='main-header'>🎨 تخصيص ألوان وثيم المنظومة</h1>", unsafe_allow_html=True)
        theme_options = list(THEMES.keys())
        selected_th = st.selectbox("اختر ثيم النظام:", theme_options, index=theme_options.index(st.session_state["selected_theme"]) if st.session_state["selected_theme"] in theme_options else 0)
        if selected_th != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = selected_th
            st.rerun()

    # ==========================================
    # ⚙️ المستخدمون والجلسات والـ IP (خاص بالأدمن)
    # ==========================================
    elif selected_page == "⚙️ المستخدمون والجلسات والـ IP":
        st.markdown("<h1 class='main-header'>⚙️ إدارة المستخدمين والجلسات النشطة والـ IP</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["👥 إدارة الحسابات", "➕ إضافة مستخدم", "📡 الجلسات النشطة وإدارة الـ IP"])

        with tab1:
            df_users = safe_read_sql("SELECT id, username, role, phone, email FROM users")
            st.dataframe(df_users, use_container_width=True)
            user_to_del = st.selectbox("اختر المستخدم للحذف:", options=[""] + df_users["username"].tolist() if not df_users.empty else [""])
            if st.button("تأكيد حذف الحساب"):
                if user_to_del and user_to_del != "admin":
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                        conn.commit()
                    st.success(f"تم حذف الحساب {user_to_del}!")
                    st.rerun()

        with tab2:
            with st.form("add_user_f"):
                nu = st.text_input("اسم المستخدم")
                np = st.text_input("كلمة المرور", type="password")
                nr = st.selectbox("الصلاحية", ["HR", "Finance", "RealEstate", "Investor", "Admin"])
                nph = st.text_input("رقم الهاتف")
                nem = st.text_input("البريد الإلكتروني")
                if st.form_submit_button("إضافة الحساب"):
                    if nu and np:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute("INSERT INTO users (username, password, role, phone, email, avatar_path) VALUES (?, ?, ?, ?, ?, ?)", (nu.strip(), np.strip(), nr, nph, nem, ""))
                                conn.commit()
                            st.success(f"تم إضافة المستخدم {nu} بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مكرر!")

        with tab3:
            st.subheader("📡 سجل الجلسات النشطة وإدارة الـ IPs")
            df_sessions = safe_read_sql("SELECT * FROM user_sessions ORDER BY id DESC")
            st.dataframe(df_sessions, use_container_width=True)

    # ==========================================
    # 💰 الإدارة المالية
    # ==========================================
    elif selected_page == "💰 الإدارة المالية":
        def finance_core():
            t1, t2 = st.tabs(["💸 تسجيل المصروفات والإيرادات", "📜 كشف الحسابات"])
            with t1:
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
                            log_audit_action(st.session_state["username"], "الإدارة المالية", f"إضافة معاملة بقيمة {tamt}")
                            st.success("تم الحفظ بنجاح!")
                            st.rerun()
            with t2:
                st.dataframe(safe_read_sql("SELECT * FROM financial_transactions ORDER BY id DESC"), use_container_width=True)
        
        render_department_workspace("الإدارة المالية", finance_core)

    # ==========================================
    # 👷 الموارد البشرية
    # ==========================================
    elif selected_page == "👷 الموارد البشرية":
        def hr_core():
            t1, t2 = st.tabs(["📋 سجل الكادر والعمالة", "➕ إضافة كادر"])
            with t1:
                st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)
            with t2:
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
                            log_audit_action(st.session_state["username"], "الموارد البشرية", f"إضافة موظف/عامل: {ename}")
                            st.success("تم الحفظ!")
                            st.rerun()

        render_department_workspace("الموارد البشرية", hr_core)

    # ==========================================
    # 🏢 العقارات والمشاريع
    # ==========================================
    elif selected_page == "🏢 العقارات والمشاريع":
        def real_estate_core():
            t1, t2 = st.tabs(["📋 العقارات المسجلة", "➕ إضافة عقار"])
            with t1:
                st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)
            with t2:
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
                            log_audit_action(st.session_state["username"], "العقارات والمشاريع", f"إضافة عقار: {pname}")
                            st.success("تم الحفظ!")
                            st.rerun()

        render_department_workspace("العقارات والمشاريع", real_estate_core)

    # ==========================================
    # 🤝 المستثمرين
    # ==========================================
    elif selected_page == "🤝 المستثمرين":
        def investors_core():
            t1, t2 = st.tabs(["📋 سجل المستثمرين", "➕ إضافة مستثمر"])
            with t1:
                st.dataframe(safe_read_sql("SELECT * FROM investors ORDER BY id DESC"), use_container_width=True)
            with t2:
                df_props = safe_read_sql("SELECT custom_id FROM properties")
                prop_options = df_props["custom_id"].tolist() if not df_props.empty else ["عام"]
                with st.form("add_investor_form"):
                    inv_name = st.text_input("اسم المستثمر")
                    prop_id = st.selectbox("العقار المرتبط", prop_options)
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
                            st.success("تم الحفظ!")
                            st.rerun()

        render_department_workspace("المستثمرين", investors_core)

    # ==========================================
    # ⏱️ سجل العمليات
    # ==========================================
    elif selected_page == "⏱️ سجل العمليات":
        st.markdown("<h1 class='main-header'>⏱️ سجل العمليات والأنشطة (Audit Trail)</h1>", unsafe_allow_html=True)
        if st.button("🗑️ تفريغ كافة السجلات"):
            with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute("DELETE FROM audit_logs")
                conn.commit()
            st.success("تم التفريغ!")
            st.rerun()
        df_logs = safe_read_sql("SELECT id, username, department, action, status, ip_address, timestamp FROM audit_logs ORDER BY id DESC")
        st.dataframe(df_logs, use_container_width=True)
