import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- Session State Initialization ---
if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "أزرق نيلي احترافي (Modern Indigo)"

if "is_developer" not in st.session_state:
    st.session_state["is_developer"] = False

# --- Modern & High-Contrast Theme Palette ---
THEMES = {
    "أزرق نيلي احترافي (Modern Indigo)": {
        "primary": "#4F46E5",
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "text": "#1E293B",
        "accent": "#6366F1",
        "border": "#E2E8F0"
    },
    "الداكن الملكي والذهبي (Royal Dark & Gold)": {
        "primary": "#D97706",
        "bg": "#0F172A",
        "card": "#1E293B",
        "text": "#F8FAFC",
        "accent": "#F59E0B",
        "border": "#334155"
    },
    "أخضر زمردي فخم (Emerald Slate)": {
        "primary": "#059669",
        "bg": "#F4FBF7",
        "card": "#FFFFFF",
        "text": "#064E3B",
        "accent": "#10B981",
        "border": "#D1FAE5"
    },
    "عنابي فاخر (Burgundy Premium)": {
        "primary": "#881337",
        "bg": "#FFF1F2",
        "card": "#FFFFFF",
        "text": "#4C0519",
        "accent": "#E11D48",
        "border": "#FFE4E6"
    }
}

current_theme = THEMES[st.session_state["selected_theme"]]

# --- Page Configuration ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Dynamic Inject Styles ---
st.markdown(f"""
<style>
    /* Hide Keyboard Badges & Hover Tooltips */
    [title*="keyboard"], [title*="Keyboard"], [data-testid="stHeader"] button title {{
        display: none !important;
    }}
    
    /* Global Styles */
    .stApp {{
        background-color: {current_theme["bg"]} !important;
        color: {current_theme["text"]} !important;
    }}
    
    .main-header {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {current_theme["primary"]} !important;
        text-align: center;
        margin-bottom: 25px;
        padding: 15px;
        border-bottom: 3px solid {current_theme["accent"]};
        background-color: {current_theme["card"]};
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important;
        padding: 18px !important;
        border-radius: 12px !important;
        border: 1px solid {current_theme["border"]} !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}

    section[data-testid="stSidebar"] {{
        background-color: {current_theme["card"]} !important;
        border-right: 1px solid {current_theme["border"]} !important;
    }}

    /* Buttons Styling */
    .stButton>button {{
        background-color: {current_theme["primary"]} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
    }}
    .stButton>button:hover {{
        background-color: {current_theme["accent"]} !important;
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect("mh_group_erp.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, location TEXT, price REAL, status TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, position TEXT, salary REAL, hire_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, category TEXT, status TEXT, created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- Session Authentication State ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""

def login_page():
    st.markdown("<h1 class='main-header'>🏢 نظام إدارة MH Group ERP</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 تسجيل الدخول")
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        login_btn = st.button("دخول", use_container_width=True)
        
        if login_btn:
            conn = sqlite3.connect("mh_group_erp.db")
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username_input, password_input))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = username_input
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")

if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(f"**المستخدم:** {st.session_state['username']} ({st.session_state['user_role']})")
    
    dev_toggle = st.sidebar.checkbox("🛠️ وضع المطور (Developer Mode)", value=st.session_state["is_developer"])
    st.session_state["is_developer"] = dev_toggle

    menu_options = [
        "لوحة التحكم الرئيسية",
        "👥 إدارة المستخدمين والصلاحيات",
        "إدارة العقارات والوحدات",
        "إدارة الموارد البشرية (HR)",
        "قسم المستثمرين والمالية",
        "قسم تقنية المعلومات (IT Support)",
        "التقارير والمستندات"
    ]

    if st.session_state["is_developer"]:
        menu_options.append("⚙️ إعدادات المطور والثيمات")

    page = st.sidebar.radio("القائمة الرئيسية", menu_options)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- Pages ---
    if page == "لوحة التحكم الرئيسية":
        st.title("📊 لوحة التحكم والملخص العام")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("إجمالي العقارات", "24 وحدة")
        with c2:
            st.metric("عدد الموظفين", "15 موظف")
        with c3:
            st.metric("إجمالي الاستثمارات", "12.5M EGP")
        with c4:
            st.metric("تذاكر الدعم الفني", "3 مفتوحة")

        st.subheader("📈 الأداء المالي والبيانات")
        df_dummy = pd.DataFrame({
            "الشهر": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو"],
            "المبيعات": [1200000, 1500000, 1800000, 1400000, 2100000, 2500000],
            "المصروفات": [400000, 450000, 500000, 480000, 520000, 600000]
        })
        st.line_chart(df_dummy.set_index("الشهر"))

    elif page == "👥 إدارة المستخدمين والصلاحيات":
        st.title("👥 إدارة حسابات المستخدمين والصلاحيات")
        
        tab1, tab2 = st.tabs(["➕ إضافة مستخدم جديد", "📋 قائمة المستخدمين الحاليين"])
        
        with tab1:
            with st.form("add_user_form"):
                new_username = st.text_input("اسم المستخدم الجديد")
                new_password = st.text_input("كلمة المرور", type="password")
                new_role = st.selectbox("الصلاحية / الدور", ["Admin", "Manager", "HR", "IT", "Accountant"])
                submit_user = st.form_submit_button("إنشاء الحساب")
                
                if submit_user and new_username and new_password:
                    conn = sqlite3.connect("mh_group_erp.db")
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                       (new_username, new_password, new_role))
                        conn.commit()
                        st.success(f"تم إنشاء حساب {new_username} بنجاح!")
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم هذا موجود بالفعل، يرجى اختيار اسم آخر.")
                    finally:
                        conn.close()

        with tab2:
            conn = sqlite3.connect("mh_group_erp.db")
            users_df = pd.read_sql_query("SELECT id, username, role FROM users", conn)
            conn.close()
            st.dataframe(users_df, use_container_width=True)

    elif page == "إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات")
        with st.form("add_prop_form"):
            name = st.text_input("اسم العقار / رقم الوحدة")
            location = st.text_input("الموقع")
            price = st.number_input("السعر", min_value=0.0, step=50000.0)
            status = st.selectbox("الحالة", ["متاح", "تم البيع", "تحت الإنشاء", "محجوز"])
            submitted = st.form_submit_button("إضافة العقار")
            
            if submitted and name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO properties (name, location, price, status) VALUES (?, ?, ?, ?)",
                               (name, location, price, status))
                conn.commit()
                conn.close()
                st.success("تمت إضافة العقار بنجاح!")

        conn = sqlite3.connect("mh_group_erp.db")
        props_df = pd.read_sql_query("SELECT * FROM properties", conn)
        conn.close()
        st.dataframe(props_df, use_container_width=True)

    elif page == "إدارة الموارد البشرية (HR)":
        st.title("👥 إدارة الموارد البشرية والعمالة")
        with st.form("add_emp_form"):
            emp_name = st.text_input("اسم الموظف")
            position = st.text_input("المسمى الوظيفي")
            salary = st.number_input("الراتب", min_value=0.0, step=1000.0)
            hire_date = st.date_input("تاريخ التعيين")
            submitted_emp = st.form_submit_button("حفظ الموظف")
            
            if submitted_emp and emp_name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO employees (name, position, salary, hire_date) VALUES (?, ?, ?, ?)",
                               (emp_name, position, salary, str(hire_date)))
                conn.commit()
                conn.close()
                st.success("تم تسجيل الموظف بنجاح!")

        conn = sqlite3.connect("mh_group_erp.db")
        emp_df = pd.read_sql_query("SELECT * FROM employees", conn)
        conn.close()
        st.dataframe(emp_df, use_container_width=True)

    elif page == "قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين والمؤشرات المالية")
        with st.form("add_investor_form"):
            inv_name = st.text_input("اسم المستثمر")
            inv_amount = st.number_input("مبلغ الاستثمار", min_value=0.0, step=100000.0)
            inv_rate = st.number_input("نسبة العائد المتوقعة (%)", min_value=0.0, max_value=100.0, step=1.0)
            start_d = st.date_input("تاريخ بداية الاستثمار")
            submit_inv = st.form_submit_button("إضافة المستثمر")
            
            if submit_inv and inv_name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                               (inv_name, inv_amount, inv_rate, str(start_d)))
                conn.commit()
                conn.close()
                st.success("تم تسجيل المستثمر بنجاح!")

        conn = sqlite3.connect("mh_group_erp.db")
        inv_df = pd.read_sql_query("SELECT * FROM investors", conn)
        conn.close()
        st.dataframe(inv_df, use_container_width=True)

    elif page == "قسم تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات والدعم الفني")
        with st.form("add_ticket_form"):
            t_title = st.text_input("عنوان المشكلة")
            t_cat = st.selectbox("التصنيف", ["شبكات وأنظمة", "برمجيات ERP", "أجهزة ومعدات", "صلاحيات مستخدمين"])
            t_status = st.selectbox("الحالة", ["جديد", "قيد المعالجة", "مغلق"])
            submit_t = st.form_submit_button("إرسال التذكرة")
            
            if submit_t and t_title:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute("INSERT INTO it_tickets (title, category, status, created_at) VALUES (?, ?, ?, ?)",
                               (t_title, t_cat, t_status, now_str))
                conn.commit()
                conn.close()
                st.success("تم إرسال تذكرة الدعم بنجاح!")

        conn = sqlite3.connect("mh_group_erp.db")
        it_df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
        conn.close()
        st.dataframe(it_df, use_container_width=True)

    elif page == "التقارير والمستندات":
        st.title("📑 التقارير والطباعة")
        report_type = st.selectbox("اختر نوع التقرير", ["تقرير العقارات", "تقرير الموظفين", "تقرير المستثمرين", "تقرير المستخدمين"])
        
        conn = sqlite3.connect("mh_group_erp.db")
        if report_type == "تقرير العقارات":
            rep_df = pd.read_sql_query("SELECT * FROM properties", conn)
        elif report_type == "تقرير الموظفين":
            rep_df = pd.read_sql_query("SELECT * FROM employees", conn)
        elif report_type == "تقرير المستثمرين":
            rep_df = pd.read_sql_query("SELECT * FROM investors", conn)
        else:
            rep_df = pd.read_sql_query("SELECT id, username, role FROM users", conn)
        conn.close()
        
        st.dataframe(rep_df, use_container_width=True)

    # --- Developer Section ---
    elif page == "⚙️ إعدادات المطور والثيمات":
        st.title("⚙️ قسم المطور والتحكم بالثيمات")
        st.subheader("🎨 اختيارات الثيمات المحدثة")
        
        selected_theme_name = st.selectbox(
            "اختر ثيم لوحة التحكم الجديدة:",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["selected_theme"])
        )
        
        if selected_theme_name != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = selected_theme_name
            st.success(f"تم تطبيق الثيم: {selected_theme_name}")
            st.rerun()
