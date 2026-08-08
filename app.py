import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization for Themes and Dev Mode ---
if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الأزرق الكلاسيكي"

if "is_developer" not in st.session_state:
    st.session_state["is_developer"] = False

# --- Theme Presets ---
THEMES = {
    "الأزرق الكلاسيكي": {
        "primary": "#1E3A8A",
        "bg_gradient": "linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%)",
        "card_bg": "#ffffff",
        "text_color": "#0f172a",
        "accent": "#2563eb"
    },
    "الداكن الفخم (Dark Mode)": {
        "primary": "#3b82f6",
        "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        "card_bg": "#1e293b",
        "text_color": "#f8fafc",
        "accent": "#60a5fa"
    },
    "الأخضر الزمردي": {
        "primary": "#065f46",
        "bg_gradient": "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)",
        "card_bg": "#ffffff",
        "text_color": "#064e3b",
        "accent": "#059669"
    },
    "البنفسجي العصري": {
        "primary": "#581c87",
        "bg_gradient": "linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)",
        "card_bg": "#ffffff",
        "text_color": "#3b0764",
        "accent": "#7e22ce"
    },
    "الذهبي الملكي": {
        "primary": "#78350f",
        "bg_gradient": "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)",
        "card_bg": "#ffffff",
        "text_color": "#451a03",
        "accent": "#b45309"
    }
}

theme = THEMES[st.session_state["selected_theme"]]

# --- Custom Styling & Hide Extra Tooltips / Keyboard Badges ---
st.markdown(f"""
<style>
    /* Hide keyboard shortcuts tooltips and unwanted hover text */
    [title*="keyboard"], [title*="Keyboard"], [data-testid="stHeader"] button title {{
        display: none !important;
    }}
    
    /* Global Theme Styles */
    .stApp {{
        background: {theme["bg_gradient"]};
        color: {theme["text_color"]};
    }}
    
    .main-header {{
        font-size: 2.2rem;
        font-weight: bold;
        color: {theme["primary"]};
        text-align: center;
        margin-bottom: 25px;
        padding: 10px;
        border-bottom: 2px solid {theme["primary"]};
    }}
    
    .stMetric {{
        background-color: {theme["card_bg"]};
        padding: 15px;
        border-radius: 12px;
        border: 1px solid {theme["accent"]};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    div[data-testid="stSidebar"] {{
        background-color: {theme["card_bg"]};
        border-right: 1px solid {theme["accent"]};
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
            name TEXT,
            location TEXT,
            price REAL,
            status TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            position TEXT,
            salary REAL,
            hire_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            investment_amount REAL,
            return_rate REAL,
            start_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- Authentication ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""

def login_page():
    st.markdown("<h1 class='main-header'>🏢 نظام إدارة MH Group ERP</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 تسجيل الدخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        login_btn = st.button("دخول", use_container_width=True)
        
        if login_btn:
            conn = sqlite3.connect("mh_group_erp.db")
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة! يرجى استخدام (admin / admin123)")

if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown("**المستخدم:** Admin")
    
    # Toggle Developer Mode option in Sidebar
    dev_toggle = st.sidebar.checkbox("🛠️ تفعيل وضع المطور (Developer Mode)", value=st.session_state["is_developer"])
    st.session_state["is_developer"] = dev_toggle

    menu_options = [
        "لوحة التحكم الرئيسية",
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

    # --- Dashboard Page ---
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
            st.metric("تذاكر الدعم الفني مفتوحة", "3 تذاكر")

        st.subheader("📈 الأداء المالي واستعراض البيانات")
        df_dummy = pd.DataFrame({
            "الشهر": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو"],
            "المبيعات": [1200000, 1500000, 1800000, 1400000, 2100000, 2500000],
            "المصروفات": [400000, 450000, 500000, 480000, 520000, 600000]
        })
        st.line_chart(df_dummy.set_index("الشهر"))

    # --- Properties Management ---
    elif page == "إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات")
        
        st.subheader("إضافة وحدة جديدة")
        with st.form("add_prop_form"):
            name = st.text_input("اسم العقار / رقم الوحدة")
            location = st.text_input("الموقع / العنوان")
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

        st.subheader("قائمة العقارات المسجلة")
        conn = sqlite3.connect("mh_group_erp.db")
        props_df = pd.read_sql_query("SELECT * FROM properties", conn)
        conn.close()
        st.dataframe(props_df, use_container_width=True)

    # --- HR Management ---
    elif page == "إدارة الموارد البشرية (HR)":
        st.title("👥 إدارة الموارد البشرية والعمالة")
        
        st.subheader("إضافة موظف جديد")
        with st.form("add_emp_form"):
            emp_name = st.text_input("اسم الموظف")
            position = st.text_input("المسمى الوظيفي")
            salary = st.number_input("الراتب", min_value=0.0, step=1000.0)
            hire_date = st.date_input("تاريخ التعيين")
            submitted_emp = st.form_submit_button("حفظ بيانات الموظف")
            
            if submitted_emp and emp_name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO employees (name, position, salary, hire_date) VALUES (?, ?, ?, ?)",
                               (emp_name, position, salary, str(hire_date)))
                conn.commit()
                conn.close()
                st.success("تم تسجيل الموظف بنجاح!")

        st.subheader("جدول الموظفين")
        conn = sqlite3.connect("mh_group_erp.db")
        emp_df = pd.read_sql_query("SELECT * FROM employees", conn)
        conn.close()
        st.dataframe(emp_df, use_container_width=True)

    # --- Investors & Finance ---
    elif page == "قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين والمؤشرات المالية")
        
        st.subheader("تسجيل مستثمر جديد")
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

        st.subheader("بيانات المستثمرين الحاليين")
        conn = sqlite3.connect("mh_group_erp.db")
        inv_df = pd.read_sql_query("SELECT * FROM investors", conn)
        conn.close()
        st.dataframe(inv_df, use_container_width=True)

    # --- IT Support ---
    elif page == "قسم تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات والدعم الفني")
        
        st.subheader("إنشاء تذكرة دعم فني جديدة")
        with st.form("add_ticket_form"):
            t_title = st.text_input("عنوان المشكلة / الطلب")
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
                st.success("تم إرسال تذكرة الدعم الفني بنجاح!")

        st.subheader("سجل تذاكر الدعم الفني")
        conn = sqlite3.connect("mh_group_erp.db")
        it_df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
        conn.close()
        st.dataframe(it_df, use_container_width=True)

    # --- Reports ---
    elif page == "التقارير والمستندات":
        st.title("📑 التقارير والطباعة")
        st.info("يمكنك تصدير وعرض التقرير الشامل لبيانات الشركة مباشرة بصيغة CSV أو عرض البيانات المباشرة.")
        
        report_type = st.selectbox("اختر نوع التقرير", ["تقرير العقارات", "تقرير الموظفين", "تقرير المستثمرين", "تقرير IT"])
        
        conn = sqlite3.connect("mh_group_erp.db")
        if report_type == "تقرير العقارات":
            rep_df = pd.read_sql_query("SELECT * FROM properties", conn)
        elif report_type == "تقرير الموظفين":
            rep_df = pd.read_sql_query("SELECT * FROM employees", conn)
        elif report_type == "تقرير المستثمرين":
            rep_df = pd.read_sql_query("SELECT * FROM investors", conn)
        else:
            rep_df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
        conn.close()
        
        st.dataframe(rep_df, use_container_width=True)
        
        csv_data = rep_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل التقرير (CSV)",
            data=csv_data,
            file_name=f"{report_type}.csv",
            mime="text/csv"
        )

    # --- Developer Only Page ---
    elif page == "⚙️ إعدادات المطور والثيمات":
        st.title("⚙️ قسم المطور والتحكم بالثيمات")
        st.warning("🔒 هذا القسم ظاهر لك بصفتك المطور فقط.")
        
        st.subheader("🎨 اختيارات ثيمات الموقع")
        
        selected_theme = st.selectbox(
            "اختر ثيم الموقع الحالي:",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["selected_theme"])
        )
        
        if st.button("تطبيق الثيم المحدد"):
            st.session_state["selected_theme"] = selected_theme
            st.success(f"تم تغيير الثيم إلى: {selected_theme}")
            st.rerun()

        st.markdown("---")
        st.subheader("🛠️ أدوات ومعلومات المطور")
        st.json({
            "وضع المطور": "نشط",
            "الثيم الحالي": st.session_state["selected_theme"],
            "قاعدة البيانات": "SQLite3 (mh_group_erp.db)",
            "إصدار Streamlit": st.__version__
        })
