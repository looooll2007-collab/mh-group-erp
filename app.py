import sqlite3
import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والتصميم
# ==========================================
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# الألوان الداكنة والذهبية المطابقة للتصميم
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
# 2. قاعدة البيانات
# ==========================================
def get_db_connection():
    return sqlite3.connect('mh_group_erp.db', timeout=20)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            phone TEXT
        )
    ''')
    
    # الجداول المتبقية
    cursor.execute('''CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, location TEXT, price REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS investors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT, notes TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, emp_type TEXT, position TEXT, pay_type TEXT, total_pay REAL, hire_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, service_type TEXT, phone TEXT, balance REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS it_tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, category TEXT)''')
    
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

# ==========================================
# 3. تعريف القائمة والصلاحيات المباشرة
# ==========================================
# تعريف كافة الأقسام مع الأيقونات كقائمة محددة
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

# خريطة الصلاحيات: ربط كل دور بالأقسام المسموح له برؤيتها
ROLE_PERMISSIONS = {
    "Admin": ALL_PAGES, # المدير يرى كل شيء
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
# 4. جلسة المستخدم وتسجيل الدخول
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""

def login_page():
    st.markdown("<h1 class='main-header'>🏢 نظام إدارة MH GROUP ERP</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 تسجيل الدخول للنظام")
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول", use_container_width=True):
            clean_username = username_input.strip()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT role, username FROM users WHERE LOWER(TRIM(username)) = LOWER(?) AND password = ?", (clean_username, password_input))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = str(res[0]).strip()
                st.session_state["username"] = str(res[1]).strip()
                st.success(f"تم تسجيل الدخول بنجاح! الصلاحية: {res[0]}")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")

# ==========================================
# 5. عرض القائمة حسب الصلاحية
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    # شريط أعلى القائمة الجانبية
    st.sidebar.markdown("""
        <div style="text-align: center; padding-bottom: 5px;">
            <h2 style="color: #D97706; margin:0; font-weight: 900;">👑 MH GROUP</h2>
            <p style="color: #94A3B8; font-size: 0.75rem; margin:0;">ERP SYSTEM</p>
        </div>
        <hr style="border-color: #1E293B; margin-top: 5px; margin-bottom: 15px;">
    """, unsafe_allow_html=True)

    # جلب الصلاحية المسموحة للمستخدم الحالي
    current_role = st.session_state.get("user_role", "")
    
    # تحديد القائمة المتاحة
    if current_role in ROLE_PERMISSIONS:
        visible_pages = ROLE_PERMISSIONS[current_role]
    elif current_role == "Admin":
        visible_pages = ALL_PAGES
    else:
        # افتراضياً للمستخدمين غير المعروفين: لوحة التحكم فقط
        visible_pages = ["🏠 لوحة التحكم"]

    # عرض القائمة الجانبية بالتنقل المفلتر
    selected_page = st.sidebar.radio("التنقل بين الأقسام", visible_pages)

    # الجزء الأسفل من القائمة الجانبية (الشعار وزر الخروج)
    st.sidebar.markdown("""
        <div class="company-card">
            <h4>M H Group</h4>
            <p>للاستثمار والتطوير العقاري</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.write("")
    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = ""
        st.session_state["username"] = ""
        st.rerun()

    # ==========================================
    # 6. الشاشات المحمية
    # ==========================================
    
    if selected_page == "🏠 لوحة التحكم":
        st.markdown("<h1 class='main-header'>🏠 لوحة التحكم الرئيسية</h1>", unsafe_allow_html=True)
        st.info(f"مرحباً بك: **{st.session_state['username']}** | الصلاحية الحالية: **{st.session_state['user_role']}**")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي العقارات", f"{len(safe_read_sql('SELECT id FROM properties'))} وحدة")
        c2.metric("العمالة والموظفين", f"{len(safe_read_sql('SELECT id FROM employees'))} فرد")
        inv_df = safe_read_sql("SELECT investment_amount FROM investors")
        c3.metric("حجم الاستثمارات", f"{inv_df['investment_amount'].sum() if not inv_df.empty else 0:,.0f} EGP")

    elif selected_page == "🏢 العقارات والمشروعات":
        st.title("🏢 العقارات والمشروعات")
        st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)

    elif selected_page == "💰 الإدارة المالية":
        st.title("💰 الإدارة المالية")
        st.info("تفاصيل الحسابات، الميزانية، والمصروفات.")

    elif selected_page == "👥 الموارد البشرية":
        st.title("👥 الموارد البشرية")
        st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)

    elif selected_page == "🤝 المستثمرين":
        st.title("🤝 المستثمرين")
        st.dataframe(safe_read_sql("SELECT * FROM investors"), use_container_width=True)

    elif selected_page == "📦 الموردين":
        st.title("📦 الموردين")
        st.dataframe(safe_read_sql("SELECT * FROM vendors"), use_container_width=True)

    elif selected_page == "👷 الموظفين":
        st.title("👷 الموظفين")
        st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)

    elif selected_page == "🎧 IT Support":
        st.title("🎧 IT Support")
        st.dataframe(safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True)

    elif selected_page == "📁 المستندات":
        st.title("📁 المستندات")
        st.dataframe(safe_read_sql("SELECT * FROM documents"), use_container_width=True)

    elif selected_page == "📊 التقارير":
        st.title("📊 التقارير المجمعة والتحليلات")
        st.info("تقارير أداء العقارات والمالية والموارد البشرية.")

    elif selected_page == "⚙️ المستخدمين والصلاحيات":
        st.title("⚙️ إدارة المستخدمين والصلاحيات")
        tab1, tab2 = st.tabs(["📋 قائمة المستخدمين", "➕ إضافة مستخدم وصلاحية"])
        
        with tab1:
            st.dataframe(safe_read_sql("SELECT id, username, role, phone FROM users"), use_container_width=True)
            
        with tab2:
            with st.form("add_user_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_phone = st.text_input("رقم الهاتف")
                
                # اختيار الصلاحية المحددة
                u_role = st.selectbox("الصلاحية / القسم الخاص به", options=list(ROLE_PERMISSIONS.keys()))
                
                if st.form_submit_button("إنشاء المستخدم"):
                    if u_name and u_pass:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                         (u_name.strip(), u_pass.strip(), u_role, u_phone))
                            conn.commit()
                            conn.close()
                            st.success(f"تم إنشاء حساب '{u_name}' بصلاحية قسم '{u_role}' بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مكرر!")
                    else:
                        st.error("يرجى إدخال اسم المستخدم وكلمة المرور!")

    elif selected_page in ["🛠️ الإعدادات", "⏱️ سجل العمليات"]:
        st.title(selected_page)
        st.info("قسم الإعدادات والسجلات الخاصة بالإدارة.")
