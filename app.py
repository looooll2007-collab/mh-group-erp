import sqlite3
import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1. تهيئة الصفحة والتصميم الداكن
# ==========================================
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

CURRENT_THEME = {
    "primary": "#D97706",
    "bg": "#0B0F19",
    "card": "#111827",
    "text": "#F9FAFB",
    "border": "#1F2937",
    "sidebar_bg": "#0F172A",
}

st.markdown(f"""
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
        border-bottom: 2px solid {CURRENT_THEME["primary"]};
        background-color: {CURRENT_THEME["card"]};
        border-radius: 10px;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {CURRENT_THEME["sidebar_bg"]} !important;
        border-right: 1px solid {CURRENT_THEME["border"]} !important;
    }}
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
    .stButton>button {{
        background-color: {CURRENT_THEME["primary"]} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إنشاء وتعديل قاعدة البيانات تلقائياً (Schema Auto-Fix)
# ==========================================
def get_db_connection():
    return sqlite3.connect('mh_group_erp.db', timeout=20)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # المستخدمين
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, phone TEXT)''')
    
    # العقارات والمشروعات
    cursor.execute('''CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT, price REAL, status TEXT, type TEXT)''')
    
    # المعاملات المالية
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, amount REAL, trans_type TEXT, category TEXT, date TEXT)''')
        
    # المستثمرين
    cursor.execute('''CREATE TABLE IF NOT EXISTS investors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT, notes TEXT)''')
        
    # جدول الموظفين المتوافق تماماً
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, position TEXT, salary REAL, hire_date TEXT)''')
    
    # التأكد من هيكلية جدول الموظفين لحل مشكلة OperationalError
    cursor.execute("PRAGMA table_info(employees)")
    cols = [column[1] for column in cursor.fetchall()]
    if 'position' not in cols:
        try: cursor.execute("ALTER TABLE employees ADD COLUMN position TEXT")
        except: pass
    if 'salary' not in cols:
        try: cursor.execute("ALTER TABLE employees ADD COLUMN salary REAL")
        except: pass
    if 'hire_date' not in cols:
        try: cursor.execute("ALTER TABLE employees ADD COLUMN hire_date TEXT")
        except: pass

    # باقي الجداول
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, service_type TEXT, phone TEXT, balance REAL)''')
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS it_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, status TEXT, created_at TEXT)''')
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, upload_date TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT, timestamp TEXT)''')

    # إضافة حساب Admin تلقائي
    cursor.execute("SELECT * FROM users WHERE LOWER(TRIM(username)) = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')")
    
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

def log_action(username, action):
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO audit_logs (username, action, timestamp) VALUES (?, ?, ?)",
                     (username, action, str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))
        conn.commit()
        conn.close()
    except Exception:
        pass

# ==========================================
# 3. الصلاحيات المخصصة
# ==========================================
ALL_PAGES = [
    "🏠 لوحة التحكم",
    "🏢 العقارات والمشروعات",
    "💰 الإدارة المالية",
    "👥 الموارد البشرية",
    "🤝 المستثمرين",
    "📦 الموردين",
    "👷 الموظفين",
    "🎧 IT Support",
    "📁 المستندات",
    "📊 التقارير",
    "⚙️ المستخدمين والصلاحيات",
    "🛠️ الإعدادات",
    "⏱️ سجل العمليات"
]

ROLE_PERMISSIONS = {
    "Admin": ALL_PAGES,
    "RealEstate": ["🏠 لوحة التحكم", "🏢 العقارات والمشروعات", "📊 التقارير"],
    "Finance": ["🏠 لوحة التحكم", "💰 الإدارة المالية", "📊 التقارير"],
    "HR": ["🏠 لوحة التحكم", "👥 الموارد البشرية", "👷 الموظفين", "📊 التقارير"],
    "Investor": ["🏠 لوحة التحكم", "🤝 المستثمرين"],
    "Vendor": ["🏠 لوحة التحكم", "📦 الموردين"],
    "Employee": ["🏠 لوحة التحكم", "👷 الموظفين"],
    "IT": ["🏠 لوحة التحكم", "🎧 IT Support"],
    "Document": ["🏠 لوحة التحكم", "📁 المستندات"]
}

# ==========================================
# 4. تسجيل الدخول للجلسة
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""

if not st.session_state["logged_in"]:
    st.markdown("<h1 class='main-header'>🏢 تسجيل الدخول - نظام MH GROUP ERP</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        u_input = st.text_input("اسم المستخدم")
        p_input = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role, username FROM users WHERE LOWER(TRIM(username)) = LOWER(?) AND password = ?", (u_input.strip(), p_input))
            res = cursor.fetchone()
            conn.close()
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = str(res[0]).strip()
                st.session_state["username"] = str(res[1]).strip()
                log_action(res[1], "تسجيل دخول للنظام")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")
else:
    # ==========================================
    # 5. القائمة الجانبية والصلاحيات المفلترة
    # ==========================================
    st.sidebar.markdown("""
        <div style="text-align: center; padding-bottom: 5px;">
            <h2 style="color: #D97706; margin:0; font-weight: 900;">👑 MH GROUP</h2>
            <p style="color: #94A3B8; font-size: 0.75rem; margin:0;">ERP SYSTEM</p>
        </div>
        <hr style="border-color: #1E293B; margin-top: 5px; margin-bottom: 15px;">
    """, unsafe_allow_html=True)

    current_role = st.session_state.get("user_role", "Admin")
    allowed_pages = ROLE_PERMISSIONS.get(current_role, ["🏠 لوحة التحكم"])

    selected_page = st.sidebar.radio("التنقل بين الأقسام", allowed_pages)

    st.sidebar.markdown("""
        <div class="company-card">
            <h4>M H Group</h4>
            <p>للاستثمار والتطوير العقاري</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.write("")
    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        log_action(st.session_state["username"], "تسجيل خروج")
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = ""
        st.session_state["username"] = ""
        st.rerun()

    # ==========================================
    # 6. تشغيل كافة الأقسام التفاعلية بالكامل
    # ==========================================
    
    if selected_page == "🏠 لوحة التحكم":
        st.markdown("<h1 class='main-header'>🏠 لوحة التحكم الرئيسية</h1>", unsafe_allow_html=True)
        st.success(f"مرحباً بك: **{st.session_state['username']}** | الصلاحية النشطة: **{st.session_state['user_role']}**")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي العقارات", f"{len(safe_read_sql('SELECT id FROM properties'))} وحدة")
        m2.metric("عدد الموظفين", f"{len(safe_read_sql('SELECT id FROM employees'))} موظف")
        m3.metric("المستثمرين المسجلين", f"{len(safe_read_sql('SELECT id FROM investors'))} مستثمر")
        m4.metric("التذاكر الفنية المفتوحة", f"{len(safe_read_sql('SELECT id FROM it_tickets WHERE status != \"مغلقة\"'))} تذكرة")

    elif selected_page == "🏢 العقارات والمشروعات":
        st.title("🏢 العقارات والمشروعات")
        tab1, tab2 = st.tabs(["📋 عرض العقارات والمشروعات", "➕ إضافة عقار جديد"])
        
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)
            
        with tab2:
            with st.form("add_prop_form"):
                p_name = st.text_input("اسم المشروع / العقار")
                p_loc = st.text_input("الموقع / العنوان")
                p_price = st.number_input("السعر التقديري (EGP)", min_value=0.0)
                p_type = st.selectbox("نوع العقار", ["شقة", "فيلا", "محل تجاري", "أرض", "مبنى إداري"])
                p_status = st.selectbox("الحالة", ["متاح للبيع", "تم البيع", "تحت الإنشاء"])
                
                if st.form_submit_button("إضافة العقار"):
                    if p_name:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO properties (name, location, price, status, type) VALUES (?, ?, ?, ?, ?)",
                                         (p_name, p_loc, p_price, p_status, p_type))
                            conn.commit()
                            conn.close()
                            log_action(st.session_state["username"], f"إضافة عقار: {p_name}")
                            st.success("تم تسجيل العقار بنجاح!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"حدث خطأ أثناء الإضافة: {err}")

    elif selected_page == "💰 الإدارة المالية":
        st.title("💰 الإدارة المالية والمصروفات")
        tab1, tab2 = st.tabs(["📊 سجل المعاملات المالية", "➕ تسجيل معاملة مالية"])
        
        with tab1:
            df_trans = safe_read_sql("SELECT * FROM transactions")
            st.dataframe(df_trans, use_container_width=True)

        with tab2:
            with st.form("add_trans_form"):
                t_title = st.text_input("وصف المعاملة المالية")
                t_amount = st.number_input("المبلغ (EGP)", min_value=0.0)
                t_type = st.selectbox("نوع المعاملة", ["إيراد", "مصروف"])
                t_cat = st.selectbox("البند", ["مبيعات عقارية", "رواتب عمالة", "مواد بناء", "صيانة", "أخرى"])
                
                if st.form_submit_button("حفظ المعاملة"):
                    if t_title and t_amount > 0:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO transactions (title, amount, trans_type, category, date) VALUES (?, ?, ?, ?, ?)",
                                         (t_title, t_amount, t_type, t_cat, str(datetime.date.today())))
                            conn.commit()
                            conn.close()
                            log_action(st.session_state["username"], f"معاملة مالية: {t_title}")
                            st.success("تم حفظ المعاملة المالية!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"خطأ: {err}")

    # --- قسم الموظفين والموارد البشرية (مُعالج تماماً) ---
    elif selected_page in ["👥 الموارد البشرية", "👷 الموظفين"]:
        st.title("👷 إدارة الموظفين والعمالة")
        tab1, tab2 = st.tabs(["📋 قائمة الموظفين", "➕ إضافة موظف جديد"])
        
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)
            
        with tab2:
            with st.form("add_emp_form"):
                e_name = st.text_input("اسم الموظف / العامل")
                e_pos = st.text_input("المسمى الوظيفي / القسم")
                e_sal = st.number_input("الراتب الشهرى (EGP)", min_value=0.0)
                
                if st.form_submit_button("إضافة الموظف"):
                    if e_name:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO employees (name, position, salary, hire_date) VALUES (?, ?, ?, ?)",
                                         (e_name, e_pos, e_sal, str(datetime.date.today())))
                            conn.commit()
                            conn.close()
                            log_action(st.session_state["username"], f"إضافة موظف: {e_name}")
                            st.success("تم إضافة الموظف بنجاح ورُبطت بقاعدة البيانات!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"حدث خطأ أثناء حفظ بيانات الموظف: {err}")

    elif selected_page == "🤝 المستثمرين":
        st.title("🤝 المستثمرين والأرباح")
        tab1, tab2 = st.tabs(["📊 سجل المستثمرين", "➕ إضافة مستثمر"])
        
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM investors"), use_container_width=True)
            
        with tab2:
            with st.form("add_inv_form"):
                inv_name = st.text_input("اسم المستثمر")
                inv_amt = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                inv_rate = st.number_input("نسبة الربح (%)", min_value=0.0)
                
                if st.form_submit_button("إضافة المستثمر"):
                    if inv_name and inv_amt > 0:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                                         (inv_name, inv_amt, inv_rate, str(datetime.date.today())))
                            conn.commit()
                            conn.close()
                            log_action(st.session_state["username"], f"إضافة مستثمر: {inv_name}")
                            st.success("تم إضافة المستثمر!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"خطأ: {err}")

    elif selected_page == "📦 الموردين":
        st.title("📦 إدارة الموردين")
        tab1, tab2 = st.tabs(["📋 قائمة الموردين", "➕ إضافة مورد"])
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM vendors"), use_container_width=True)
        with tab2:
            with st.form("add_v_form"):
                v_name = st.text_input("اسم المورد")
                v_serv = st.text_input("نوع الخدمة / المواد")
                v_phone = st.text_input("الهاتف")
                v_bal = st.number_input("الرصيد المالي", min_value=0.0)
                if st.form_submit_button("حفظ"):
                    if v_name:
                        conn = get_db_connection()
                        conn.execute("INSERT INTO vendors (name, service_type, phone, balance) VALUES (?, ?, ?, ?)", (v_name, v_serv, v_phone, v_bal))
                        conn.commit()
                        conn.close()
                        st.success("تم الحفظ!")
                        st.rerun()

    elif selected_page == "🎧 IT Support":
        st.title("🎧 IT Support")
        tab1, tab2 = st.tabs(["📋 التذاكر", "➕ تذكرة جديدة"])
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True)
        with tab2:
            with st.form("add_t_form"):
                t_title = st.text_input("عنوان المشكلة")
                t_cat = st.selectbox("الفئة", ["شبكات", "برمجيات", "أجهزة"])
                if st.form_submit_button("إرسال"):
                    if t_title:
                        conn = get_db_connection()
                        conn.execute("INSERT INTO it_tickets (title, category, status, created_at) VALUES (?, ?, ?, ?)",
                                     (t_title, t_cat, "مفتوحة", str(datetime.date.today())))
                        conn.commit()
                        conn.close()
                        st.success("تم الإرسال!")
                        st.rerun()

    elif selected_page == "📁 المستندات":
        st.title("📁 الأرشيف والمستندات")
        st.dataframe(safe_read_sql("SELECT * FROM documents"), use_container_width=True)

    elif selected_page == "📊 التقارير":
        st.title("📊 التقارير العامة")
        st.info("تقارير أداء المشروعات والموارد والمالية.")

    elif selected_page == "⚙️ المستخدمين والصلاحيات":
        st.title("⚙️ إدارة المستخدمين والصلاحيات")
        tab1, tab2 = st.tabs(["📋 الحسابات", "➕ حساب جديد"])
        with tab1:
            st.dataframe(safe_read_sql("SELECT id, username, role, phone FROM users"), use_container_width=True)
        with tab2:
            with st.form("add_u_form"):
                u_n = st.text_input("اسم المستخدم")
                u_p = st.text_input("كلمة المرور", type="password")
                u_ph = st.text_input("الهاتف")
                u_r = st.selectbox("الصلاحية والقسم الخاص به", options=list(ROLE_PERMISSIONS.keys()))
                if st.form_submit_button("إنشاء"):
                    if u_n and u_p:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)", (u_n.strip(), u_p.strip(), u_r, u_ph))
                            conn.commit()
                            conn.close()
                            st.success("تم إنشاء الحساب بأسلوبه المخصص!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مكرر!")

    elif selected_page in ["🛠️ الإعدادات", "⏱️ سجل العمليات"]:
        st.title(selected_page)
        st.dataframe(safe_read_sql("SELECT * FROM audit_logs ORDER BY id DESC"), use_container_width=True)
