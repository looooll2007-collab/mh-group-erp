import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. تهيئة الصفحة والمظهر (Dark & Gold Theme)
# ==========================================
st.set_page_config(
    page_title="MH GROUP ERP SYSTEM",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0B0F17 !important;
        color: #F3F4F6 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937 !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #B45309 0%, #D97706 50%, #F59E0B 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold !important;
        height: 45px !important;
    }
    .stTextInput input, .stSelectbox select {
        background-color: #1A202C !important;
        color: #FFFFFF !important;
        border: 1px solid #2D3748 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إدارة قاعدة البيانات والبيانات الدائمة
# ==========================================
DB_NAME = "mh_group_erp_production.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. جدول المستخدمين والصلاحيات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                department TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. جدول العقارات والمشروعات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                price REAL,
                status TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. جدول المعاملات المالية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trans_type TEXT,
                amount REAL,
                party TEXT,
                date TEXT,
                created_by TEXT
            )
        """)

        # 4. جدول الموظفين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_name TEXT NOT NULL,
                position TEXT,
                salary REAL,
                hire_date TEXT
            )
        """)

        # إنشاء حساب المدير العام الافتراضي إذا لم يكن موجوداً
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, email, phone, password, department)
                VALUES ('admin', 'admin@mhgroup.com', '01000000000', 'admin123', 'المدير العام')
            """)
        conn.commit()

init_db()

# ==========================================
# 3. إدارة الجلسة (Session State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}

# ==========================================
# 4. شاشة تسجيل الدخول
# ==========================================
def render_login_screen():
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, _, col_right = st.columns([1.1, 0.1, 1])

    with col_left:
        st.markdown("""
        <div style="font-size: 2.2rem; color: #D97706; font-weight: bold;">M MH GROUP</div>
        <h1 style="font-size: 2.5rem; color: #FFFFFF; margin-top: 20px;">نظام إدارة الشركة ERP</h1>
        <p style="color: #94A3B8; font-size: 1.1rem;">منصة معالجة البيانات وإدارة الموارد وفق صلاحيات الأقسام.</p>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>تسجيل الدخول</h2>", unsafe_allow_html=True)
        
        login_input = st.text_input("اسم المستخدم أو البريد الإلكتروني", placeholder="admin@mhgroup.com")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button("تسجيل الدخول ➔", use_container_width=True):
            if not login_input or not password_input:
                st.error("يرجى إدخال جميع البيانات!")
            else:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT username, email, phone, department FROM users 
                        WHERE (username = ? OR email = ?) AND password = ?
                    """, (login_input, login_input, password_input))
                    user = cursor.fetchone()

                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = {
                        "username": user[0],
                        "email": user[1],
                        "phone": user[2],
                        "department": user[3]
                    }
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة!")

# ==========================================
# 5. التطبيق الرئيسي وخريطة الصلاحيات
# ==========================================
if not st.session_state["logged_in"]:
    render_login_screen()
else:
    user_dept = st.session_state["user_info"]["department"]
    username = st.session_state["user_info"]["username"]

    # الشريط الجانبي وتفاصيل الموظف
    st.sidebar.title("MH GROUP ERP")
    st.sidebar.markdown(f"👤 **المستخدم:** {username}")
    st.sidebar.markdown(f"🏢 **القسم:** `{user_dept}`")
    st.sidebar.markdown("---")

    # تحديد الأقسام المتاحة بناءً على نوع الحساب
    DEPARTMENTS_MAP = {
        "العقارات والمشروعات": ["العقارات والمشروعات"],
        "الإدارة المالية": ["الإدارة المالية"],
        "الموارد البشرية": ["الموارد البشرية"],
        "المستثمرين": ["المستثمرين"],
        "IT Support": ["IT Support"],
    }

    if user_dept == "المدير العام":
        available_pages = ["لوحة التحكم", "العقارات والمشروعات", "الإدارة المالية", "الموارد البشرية", "المستثمرين", "IT Support", "إدارة المستخدمين والصلاحيات"]
    else:
        # يظهر للموظف قسمه المخصص بالإضافة إلى لوحة تحكم مصغرة
        available_pages = ["لوحة التحكم"] + DEPARTMENTS_MAP.get(user_dept, [])

    page = st.sidebar.radio("التنقل بين الأقسام", available_pages)

    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.session_state["user_info"] = {}
        st.rerun()

    # ------------------ 1. قسم لوحة التحكم ------------------
    if page == "لوحة التحكم":
        st.title("📌 ملخص العمليات الحية")
        st.info(f"أهلاً بك **{username}**، المعروض أدناه هي البيانات المسجلة فعلياً في النظام.")
        
        with sqlite3.connect(DB_NAME) as conn:
            props_count = pd.read_sql_query("SELECT COUNT(*) as c FROM properties", conn).iloc[0]['c']
            trans_count = pd.read_sql_query("SELECT COUNT(*) as c FROM transactions", conn).iloc[0]['c']
            emp_count = pd.read_sql_query("SELECT COUNT(*) as c FROM employees", conn).iloc[0]['c']

        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي العقارات المسجلة", props_count)
        c2.metric("إجمالي المعاملات المالية", trans_count)
        c3.metric("إجمالي الموظفين", emp_count)

    # ------------------ 2. قسم العقارات والمشروعات ------------------
    elif page == "العقارات والمشروعات":
        st.title("🏡 قسم العقارات والمشروعات")
        
        st.subheader("إضافة عقار جديد")
        with st.form("add_prop_form", clear_on_submit=True):
            p_name = st.text_input("اسم العقار / المشروع")
            p_loc = st.text_input("الموقع")
            p_price = st.number_input("السعر (ج.م)", min_value=0.0, step=50000.0)
            p_status = st.selectbox("الحالة", ["متاح", "تحت التطوير", "مباع"])
            submit_prop = st.form_submit_button("حفظ العقار في قاعدة البيانات")

            if submit_prop and p_name:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO properties (name, location, price, status, created_by)
                        VALUES (?, ?, ?, ?, ?)
                    """, (p_name, p_loc, p_price, p_status, username))
                    conn.commit()
                st.success("تم حفظ العقار بنجاح!")

        st.subheader("قائمة العقارات المسجلة حالياً")
        with sqlite3.connect(DB_NAME) as conn:
            df_props = pd.read_sql_query("SELECT id, name AS 'اسم العقار', location AS 'الموقع', price AS 'السعر', status AS 'الحالة', created_by AS 'تمت الإضافة بواسطة', created_at AS 'التاريخ' FROM properties", conn)
        st.dataframe(df_props, use_container_width=True)

    # ------------------ 3. قسم الإدارة المالية ------------------
    elif page == "الإدارة المالية":
        st.title("💼 قسم الإدارة المالية")
        
        st.subheader("تسجيل معاملة مالية حقيقية")
        with st.form("add_trans_form", clear_on_submit=True):
            t_type = st.selectbox("نوع المعاملة", ["إيراد", "مصروف"])
            t_amount = st.number_input("المبلغ (ج.م)", min_value=0.0)
            t_party = st.text_input("الجهة / العميل / المورد")
            t_date = st.date_input("تاريخ المعاملة")
            submit_trans = st.form_submit_button("تسجيل المعاملة")

            if submit_trans and t_amount > 0:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO transactions (trans_type, amount, party, date, created_by)
                        VALUES (?, ?, ?, ?, ?)
                    """, (t_type, t_amount, t_party, str(t_date), username))
                    conn.commit()
                st.success("تم تسجيل المعاملة المالية بنجاح!")

        st.subheader("سجل المعاملات المالية")
        with sqlite3.connect(DB_NAME) as conn:
            df_trans = pd.read_sql_query("SELECT id, trans_type AS 'النوع', amount AS 'المبلغ', party AS 'الجهة', date AS 'التاريخ', created_by AS 'المسؤول' FROM transactions", conn)
        st.dataframe(df_trans, use_container_width=True)

    # ------------------ 4. قسم الموارد البشرية ------------------
    elif page == "الموارد البشرية":
        st.title("👥 قسم الموارد البشرية (HR)")
        
        st.subheader("تسجيل موظف جديد")
        with st.form("add_emp_form", clear_on_submit=True):
            e_name = st.text_input("اسم الموظف الثلاثي")
            e_pos = st.text_input("المسمى الوظيفي")
            e_sal = st.number_input("الراتب", min_value=0.0)
            e_date = st.date_input("تاريخ التعيين")
            submit_emp = st.form_submit_button("إضافة الموظف")

            if submit_emp and e_name:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO employees (emp_name, position, salary, hire_date)
                        VALUES (?, ?, ?, ?)
                    """, (e_name, e_pos, e_sal, str(e_date)))
                    conn.commit()
                st.success("تم إضافة الموظف بنجاح!")

        st.subheader("سجل الموظفين الحاليين")
        with sqlite3.connect(DB_NAME) as conn:
            df_emp = pd.read_sql_query("SELECT id, emp_name AS 'اسم الموظف', position AS 'الوظيفة', salary AS 'الراتب', hire_date AS 'تاريخ التعيين' FROM employees", conn)
        st.dataframe(df_emp, use_container_width=True)

    # ------------------ 5. إدارة المستخدمين والصلاحيات (للمدير فقط) ------------------
    elif page == "إدارة المستخدمين والصلاحيات":
        st.title("🔐 إدارة صلاحيات موظفي الشركة")
        
        st.subheader("إنشاء حساب جديد لموظف قسم")
        with st.form("add_user_form", clear_on_submit=True):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_username = st.text_input("اسم المستخدم (Username)")
                new_email = st.text_input("البريد الإلكتروني")
                new_phone = st.text_input("رقم الهاتف")
            with col_u2:
                new_password = st.text_input("كلمة السر", type="password")
                new_dept = st.selectbox("القسم / الصلاحية", [
                    "العقارات والمشروعات",
                    "الإدارة المالية",
                    "الموارد البشرية",
                    "المستثمرين",
                    "IT Support",
                    "المدير العام"
                ])
            
            submit_user = st.form_submit_button("إنشاء الحساب وتعيين الصلاحيات")

            if submit_user:
                if not (new_username and new_email and new_password):
                    st.error("يرجى ملء جميع الحقول المطلوب!")
                else:
                    try:
                        with sqlite3.connect(DB_NAME) as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO users (username, email, phone, password, department)
                                VALUES (?, ?, ?, ?, ?)
                            """, (new_username, new_email, new_phone, new_password, new_dept))
                            conn.commit()
                        st.success(f"تم إنشاء حساب الموظف '{new_username}' وتعيينه لقسم '{new_dept}' بنجاح!")
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم أو البريد الإلكتروني مسجل بالفعل!")

        st.subheader("قائمة حسابات الموظفين المسجلة")
        with sqlite3.connect(DB_NAME) as conn:
            df_users = pd.read_sql_query("SELECT id, username AS 'اسم المستخدم', email AS 'البريد الإلكتروني', phone AS 'رقم الهاتف', department AS 'القسم المخصص', created_at AS 'تاريخ الإنشاء' FROM users", conn)
        st.dataframe(df_users, use_container_width=True)
