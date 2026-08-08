import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- 1. إعدادات الصفحة والتصاميم لمود النهار والليل ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تحسين رؤية النصوص داخل النمطين (Dark / Light Theme)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .stMetric {
        background-color: rgba(30, 58, 138, 0.08);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(30, 58, 138, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. تهيئة قاعدة البيانات المحلية ---
def init_db():
    conn = sqlite3.connect("mh_group_erp.db")
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    # إضافة حساب المسؤول الافتراضي في حال عدم وجوده
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        
    # جدول العقارات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            location TEXT,
            price REAL,
            status TEXT
        )
    ''')
    
    # جدول الموظفين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            position TEXT,
            salary REAL,
            hire_date TEXT
        )
    ''')
    
    # جدول المستثمرين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            investment_amount REAL,
            return_rate REAL,
            start_date TEXT
        )
    ''')

    # جدول الدعم الفني IT
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

# --- 3. إدارة الجلسة والدخول ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""

def login_page():
    st.markdown("<h1 class='main-header'>🏢 نظام إدارة MH Group ERP</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 تسجيل الدخول")
        username = st.text_input("اسم المستخدم", value="admin")
        password = st.text_input("كلمة المرور", type="password", value="admin123")
        login_btn = st.button("دخول إلى النظام", use_container_width=True)
        
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
                st.error("بيانات الدخول غير صحيحة! استخدم: (admin / admin123)")

# --- 4. التوجيه وحالة الجلسة ---
if not st.session_state["logged_in"]:
    login_page()
else:
    # القائمة الجانبية
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown("**المستخدم الحالي:** Administrator")
    
    page = st.sidebar.radio("القطاعات والأقسام", [
        "لوحة التحكم الرئيسية",
        "إدارة العقارات والوحدات",
        "الموارد البشرية والعمالة (HR)",
        "قسم المستثمرين والمالية",
        "تقنية المعلومات (IT Support)",
        "التقارير والمستندات"
    ])
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- الصفحة الرئيسية ---
    if page == "لوحة التحكم الرئيسية":
        st.title("📊 لوحة التحكم والإحصائيات")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("إجمالي الوحدات", "24 وحدة")
        with c2:
            st.metric("عدد الموظفين", "15 موظف")
        with c3:
            st.metric("حجم الاستثمارات", "12.5M EGP")
        with c4:
            st.metric("تذاكر IT مفتوحة", "3 تذاكر")

        st.subheader("📈 نظرة عامة على الأداء المالي")
        df_dummy = pd.DataFrame({
            "الشهر": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو"],
            "المبيعات": [1200000, 1500000, 1800000, 1400000, 2100000, 2500000],
            "المصروفات": [400000, 450000, 500000, 480000, 520000, 600000]
        })
        st.line_chart(df_dummy.set_index("الشهر"))

    # --- إدارة العقارات ---
    elif page == "إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات")
        
        st.subheader("إضافة وحدة جديدة")
        with st.form("add_prop_form"):
            name = st.text_input("اسم العقار / رقم الوحدة")
            location = st.text_input("الموقع")
            price = st.number_input("السعر المقدر", min_value=0.0, step=50000.0)
            status = st.selectbox("الحالة", ["متاح", "تم البيع", "تحت الإنشاء", "محجوز"])
            submitted = st.form_submit_button("حفظ العقار")
            
            if submitted and name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO properties (name, location, price, status) VALUES (?, ?, ?, ?)",
                               (name, location, price, status))
                conn.commit()
                conn.close()
                st.success("تم تسجيل العقار بنجاح!")

        st.subheader("سجل الوحدات المسجلة")
        conn = sqlite3.connect("mh_group_erp.db")
        props_df = pd.read_sql_query("SELECT * FROM properties", conn)
        conn.close()
        st.dataframe(props_df, use_container_width=True)

    # --- إدارة الموارد البشرية ---
    elif page == "الموارد البشرية والعمالة (HR)":
        st.title("👥 إدارة الموارد البشرية والعمالة")
        
        st.subheader("تسجيل موظف جديد")
        with st.form("add_emp_form"):
            emp_name = st.text_input("اسم الموظف")
            position = st.text_input("الوظيفة")
            salary = st.number_input("الراتب الشهرى", min_value=0.0, step=1000.0)
            hire_date = st.date_input("تاريخ التعيين")
            submitted_emp = st.form_submit_button("إضافة الموظف")
            
            if submitted_emp and emp_name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO employees (name, position, salary, hire_date) VALUES (?, ?, ?, ?)",
                               (emp_name, position, salary, str(hire_date)))
                conn.commit()
                conn.close()
                st.success("تمت إضافة الموظف بنجاح!")

        st.subheader("سجل الموظفين الحاليين")
        conn = sqlite3.connect("mh_group_erp.db")
        emp_df = pd.read_sql_query("SELECT * FROM employees", conn)
        conn.close()
        st.dataframe(emp_df, use_container_width=True)

    # --- قسم المستثمرين ---
    elif page == "قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين والمؤشرات المالية")
        
        st.subheader("إضافة بيانات مستثمر")
        with st.form("add_investor_form"):
            inv_name = st.text_input("اسم المستثمر")
            inv_amount = st.number_input("مبلغ الاستثمار", min_value=0.0, step=100000.0)
            inv_rate = st.number_input("نسبة العائد (%)", min_value=0.0, max_value=100.0, step=1.0)
            start_d = st.date_input("تاريخ البداية")
            submit_inv = st.form_submit_button("حفظ المستثمر")
            
            if submit_inv and inv_name:
                conn = sqlite3.connect("mh_group_erp.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                               (inv_name, inv_amount, inv_rate, str(start_d)))
                conn.commit()
                conn.close()
                st.success("تم تسجيل المستثمر بنجاح!")

        st.subheader("قائمة المستثمرين")
        conn = sqlite3.connect("mh_group_erp.db")
        inv_df = pd.read_sql_query("SELECT * FROM investors", conn)
        conn.close()
        st.dataframe(inv_df, use_container_width=True)

    # --- قسم IT Support ---
    elif page == "تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات والدعم الفني")
        
        st.subheader("فتح تذكرة دعم فني جديدة")
        with st.form("add_ticket_form"):
            t_title = st.text_input("عنوان الطلب / المشكلة")
            t_cat = st.selectbox("التصنيف", ["شبكات وأنظمة", "برمجيات ERP", "أجهزة ومعدات", "صلاحيات"])
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
                st.success("تم إرسال تذكرة IT بنجاح!")

        st.subheader("سجل التذاكر والدعم الفني")
        conn = sqlite3.connect("mh_group_erp.db")
        it_df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
        conn.close()
        st.dataframe(it_df, use_container_width=True)

    # --- التقارير والتصدير ---
    elif page == "التقارير والمستندات":
        st.title("📑 التقارير وتصدير البيانات")
        report_type = st.selectbox("اختر التقرير المطلوب", ["العقارات", "الموظفين", "المستثمرين", "الدعم الفني IT"])
        
        conn = sqlite3.connect("mh_group_erp.db")
        if report_type == "العقارات":
            rep_df = pd.read_sql_query("SELECT * FROM properties", conn)
        elif report_type == "الموظفين":
            rep_df = pd.read_sql_query("SELECT * FROM employees", conn)
        elif report_type == "المستثمرين":
            rep_df = pd.read_sql_query("SELECT * FROM investors", conn)
        else:
            rep_df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
        conn.close()
        
        st.dataframe(rep_df, use_container_width=True)
        csv_data = rep_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 تحميل التقرير بصيغة (CSV)",
            data=csv_data,
            file_name=f"{report_type}.csv",
            mime="text/csv"
        )
