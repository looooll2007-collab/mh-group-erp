import streamlit as st
import sqlite3
import pandas as pd
import io

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم CSS المعدل
# ---------------------------------------------------------
st.set_page_config(
    page_title="MH GROUP ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
/* اتجاه الصفحة والألوان الأساسية */
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl;
    text-align: right;
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-left: 1px solid #30363d !important;
}

/* الأزرار الذهبية */
.stButton > button {
    background-color: #d4af37 !important;
    color: #0d1117 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    background-color: #f1c40f !important;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.4) !important;
}

/* إصلاح الإدخالات ومنع كلمة visibili */
div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
    color: #ffffff !important;
    background-color: transparent !important;
}

/* إخفاء وتجميل أيقونة إظهار كلمة المرور */
button[aria-label="Show password"], 
button[aria-label="Hide password"],
[data-aria-label="Show password"] {
    color: #8b949e !important;
    background: transparent !important;
}

button[aria-label="Show password"] *, 
button[aria-label="Hide password"] * {
    font-size: 0 !important;
}

/* جداول البيانات */
[data-testid="stDataFrame"] {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
}

h1, h2, h3, h4 {
    color: #ffffff !important;
    font-weight: 700 !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. إعداد وقواعد البيانات SQLite
# ---------------------------------------------------------
DB_FILE = "mh_group_erp.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. جدول المستخدمين والصلاحيات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        status TEXT DEFAULT 'نشط'
    )
    """)
    
    # 2. جدول الموظفين والمرتبات والسلف
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_code TEXT UNIQUE,
        full_name TEXT NOT NULL,
        department TEXT,
        position TEXT,
        base_salary REAL,
        advances REAL DEFAULT 0,
        deductions REAL DEFAULT 0,
        bonuses REAL DEFAULT 0
    )
    """)
    
    # 3. جدول أسهم المستثمرين والأرباح
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investor_code TEXT UNIQUE,
        full_name TEXT NOT NULL,
        phone TEXT,
        shares_count INTEGER DEFAULT 0,
        share_value REAL DEFAULT 0,
        total_investment REAL DEFAULT 0,
        join_date DATE DEFAULT CURRENT_DATE
    )
    """)

    # 4. جدول توزيع الأرباح على المستثمرين
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profit_distributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investor_id INTEGER,
        payout_date DATE DEFAULT CURRENT_DATE,
        amount_paid REAL,
        notes TEXT,
        FOREIGN KEY(investor_id) REFERENCES investors(id)
    )
    """)
    
    # 5. جدول المالية والتدفقات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trans_date DATE DEFAULT CURRENT_DATE,
        trans_type TEXT,
        category TEXT,
        amount REAL,
        description TEXT
    )
    """)
    
    # 6. جدول المخزون العقاري
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS real_estate_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_code TEXT UNIQUE,
        project_name TEXT,
        unit_type TEXT,
        price REAL,
        status TEXT DEFAULT 'متاحة'
    )
    """)

    # 7. جدول المستندات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_name TEXT,
        file_type TEXT,
        uploaded_by TEXT,
        upload_date DATE DEFAULT CURRENT_DATE
    )
    """)
    
    # إضافة حساب المسؤول الرئيسي افتراضياً
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, email) VALUES ('admin', '123456', 'مدير النظام', 'admin@mhgroup.com')")
        
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. إدارة جلسة التسجيل
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# ---------------------------------------------------------
# 4. صفحة تسجيل الدخول
# ---------------------------------------------------------
def login_page():
    st.markdown("<h1 style='text-align: center;'>MH GROUP للاستثمار والتطوير العقاري</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #8b949e !important;'>نظام إدارة الموارد المؤسسية (ERP)</h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("اسم المستخدم أو البريد الإلكتروني")
        password_input = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول"):
            u = username_input.strip()
            p = password_input.strip()
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE (username=? OR email=?) AND password=?", (u, u, p))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user["username"]
                st.session_state.role = user["role"]
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

# ---------------------------------------------------------
# 5. النظام الرئيسي والتوجيه بين الأقسام
# ---------------------------------------------------------
def main_app():
    st.sidebar.markdown(f"### 🏢 MH GROUP ERP")
    st.sidebar.write(f"مرحباً بك: **{st.session_state.username}**")
    st.sidebar.caption(f"الصلاحية: {st.session_state.role}")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "لوحة التحكم (Dashboard)",
        "أسهم المستثمرين والأرباح",
        "الموارد البشرية (HR)",
        "الحسابات والمالية",
        "حالة المخزون العقاري",
        "إدارة المستخدمين والصلاحيات",
        "مركز رفع المستندات",
        "الملف الشخصي"
    ])
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    st.title(f"قسم: {menu}")
    st.markdown("---")

    conn = get_connection()

    # --- 1. لوحة التحكم (Dashboard) ---
    if menu == "لوحة التحكم (Dashboard)":
        c1, c2, c3, c4 = st.columns(4)
        
        total_emp = pd.read_sql_query("SELECT COUNT(*) as count FROM employees", conn).iloc[0]['count']
        total_investors = pd.read_sql_query("SELECT COUNT(*) as count FROM investors", conn).iloc[0]['count']
        total_shares = pd.read_sql_query("SELECT SUM(shares_count) as total FROM investors", conn).iloc[0]['total'] or 0
        total_capital = pd.read_sql_query("SELECT SUM(total_investment) as total FROM investors", conn).iloc[0]['total'] or 0
        
        c1.metric("عدد الموظفين", total_emp)
        c2.metric("عدد المستثمرين", total_investors)
        c3.metric("إجمالي الأسهم", total_shares)
        c4.metric("رأس المال المستثمر", f"{total_capital:,.0f} ج.م")
        
        st.markdown("### ملخص أحدث العمليات المالية")
        df_fin = pd.read_sql_query("SELECT trans_date as التاريخ, trans_type as النوع, category as التصنيف, amount as المبلغ, description as البيان FROM financial_transactions ORDER BY id DESC LIMIT 5", conn)
        st.dataframe(df_fin, use_container_width=True)

    # --- 2. قسم أسهم المستثمرين والأرباح ---
    elif menu == "أسهم المستثمرين والأرباح":
        st.subheader("إدارة المستثمرين ورأس المال والأرباح")
        
        tab_inv1, tab_inv2, tab_inv3 = st.tabs(["قائمة المستثمرين", "إضافة مستثمر جديد", "تسجيل توزيع أرباح"])
        
        with tab_inv1:
            df_inv = pd.read_sql_query("""
                SELECT 
                    investor_code as كود_المستثمر,
                    full_name as اسم_المستثمر,
                    phone as الهاتف,
                    shares_count as عدد_الأسهم,
                    share_value as قيمة_السهم,
                    total_investment as إجمالي_الاستثمار,
                    join_date as تاريخ_الانضمام
                FROM investors
            """, conn)
            st.dataframe(df_inv, use_container_width=True)
            
            if not df_inv.empty:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_inv.to_excel(writer, index=False, sheet_name='Investors')
                st.download_button("تصدير سجل المستثمرين Excel 📊", data=buffer.getvalue(), file_name="investors_report.xlsx", mime="application/vnd.ms-excel")

        with tab_inv2:
            with st.form("add_investor_form"):
                inv_code = st.text_input("كود المستثمر (مثال: INV-01)")
                inv_name = st.text_input("اسم المستثمر بالكامل")
                inv_phone = st.text_input("رقم الهاتف")
                shares_cnt = st.number_input("عدد الأسهم", min_value=1, value=1, step=1)
                sh_val = st.number_input("قيمة السهم الواحد (ج.م)", min_value=0.0, value=10000.0)
                
                total_inv_calc = shares_cnt * sh_val
                st.info(f"إجمالي قيمة الاستثمار المحسوبة: **{total_inv_calc:,.2f} ج.م**")
                
                if st.form_submit_button("حفظ المستثمر"):
                    if inv_code and inv_name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                INSERT INTO investors (investor_code, full_name, phone, shares_count, share_value, total_investment)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (inv_code, inv_name, inv_phone, shares_cnt, sh_val, total_inv_calc))
                            
                            # تسجيل الحركة كمصدر إيراد مالي
                            cursor.execute("""
                                INSERT INTO financial_transactions (trans_type, category, amount, description)
                                VALUES ('إيراد', 'رأس مال مستثمر', ?, ?)
                            """, (total_inv_calc, f"استثمار جديد للمستثمر {inv_name} ({shares_cnt} سهم)"))
                            
                            conn.commit()
                            st.success("تم تسجيل المستثمر وإضافة المبلغ للمالية بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("كود المستثمر مسجل مسبقاً!")
                    else:
                        st.warning("يرجى إدخال كافة البيانات الأساسية")

        with tab_inv3:
            st.markdown("#### تسجيل صرف أرباح لمستثمر")
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name, investor_code FROM investors")
            all_invs = cursor.fetchall()
            
            if all_invs:
                inv_options = {f"{inv['full_name']} ({inv['investor_code']})": inv['id'] for inv in all_invs}
                selected_inv = st.selectbox("اختر المستثمر", list(inv_options.keys()))
                payout_amt = st.number_input("مبلغ الأرباح الموزعة (ج.م)", min_value=0.0)
                payout_notes = st.text_input("ملاحظات / الربع السنوي")
                
                if st.button("تسجيل صرف الأرباح"):
                    if payout_amt > 0:
                        inv_id = inv_options[selected_inv]
                        cursor.execute("INSERT INTO profit_distributions (investor_id, amount_paid, notes) VALUES (?,?,?)", (inv_id, payout_amt, payout_notes))
                        
                        # تسجيل الخصم المالي في الحسابات
                        cursor.execute("INSERT INTO financial_transactions (trans_type, category, amount, description) VALUES ('مصروف', 'توزيع أرباح مستثمرين', ?, ?)", (payout_amt, f"صرف أرباح للمستثمر {selected_inv} - {payout_notes}"))
                        
                        conn.commit()
                        st.success("تم تسجيل توزيع الأرباح وخصمها من الحسابات المالية!")
                        st.rerun()
            else:
                st.info("لا يوجد مستثمرون مسجلون حالياً")

            st.markdown("---")
            st.markdown("#### سجل توزيع الأرباح السابق")
            df_payouts = pd.read_sql_query("""
                SELECT 
                    i.full_name as اسم_المستثمر,
                    p.payout_date as تاريخ_الصرف,
                    p.amount_paid as المبلغ_المدفوع,
                    p.notes as ملاحظات
                FROM profit_distributions p
                JOIN investors i ON p.investor_id = i.id
                ORDER BY p.id DESC
            """, conn)
            st.dataframe(df_payouts, use_container_width=True)

    # --- 3. الموارد البشرية (HR) ---
    elif menu == "الموارد البشرية (HR)":
        st.subheader("إدارة الموظفين والرواتب والسُلف")
        
        tab1, tab2 = st.tabs(["قائمة الموظفين والرواتب", "إضافة موظف جديد"])
        
        with tab1:
            df_emp = pd.read_sql_query("SELECT emp_code as الكود, full_name as الاسم, department as القسم, position as الوظيفة, base_salary as الراتب_الأساسي, bonuses as المكافآت, deductions as الخصومات, advances as السُلف FROM employees", conn)
            st.dataframe(df_emp, use_container_width=True)
            
            if not df_emp.empty:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_emp.to_excel(writer, index=False, sheet_name='Employees')
                st.download_button("تصدير تقرير الموظفين Excel 📊", data=buffer.getvalue(), file_name="employees_report.xlsx", mime="application/vnd.ms-excel")

        with tab2:
            with st.form("add_emp_form"):
                code = st.text_input("كود الموظف")
                name = st.text_input("الاسم بالكامل")
                dept = st.text_input("القسم")
                pos = st.text_input("المسمى الوظيفي")
                salary = st.number_input("الراتب الأساسي", min_value=0.0)
                
                if st.form_submit_button("حفظ الموظف"):
                    if code and name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO employees (emp_code, full_name, department, position, base_salary) VALUES (?,?,?,?,?)", (code, name, dept, pos, salary))
                            conn.commit()
                            st.success("تم إضافة الموظف بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("كود الموظف مسجل مسبقاً!")
                    else:
                        st.warning("يرجى ملء كافة البيانات الأساسية")

    # --- 4. الحسابات والمالية ---
    elif menu == "الحسابات والمالية":
        st.subheader("إدارة الحركة المالية والتسجيل")
        
        col_f1, col_f2 = st.columns([1, 2])
        
        with col_f1:
            st.markdown("#### إضافة قيد جديد")
            t_type = st.selectbox("نوع الحركة", ["إيراد", "مصروف"])
            cat = st.text_input("التصنيف (مثال: مبيعات, صيانة, رواتب)")
            amt = st.number_input("المبلغ (ج.م)", min_value=0.0)
            desc = st.text_area("البيان / الوصف")
            
            if st.button("تسجيل القيد"):
                if amt > 0:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO financial_transactions (trans_type, category, amount, description) VALUES (?,?,?,?)", (t_type, cat, amt, desc))
                    conn.commit()
                    st.success("تم تسجيل القيد بنجاح!")
                    st.rerun()
                else:
                    st.warning("يرجى إدخال مبلغ صحيح")
                    
        with col_f2:
            st.markdown("#### سجل الحركات المالية")
            df_trans = pd.read_sql_query("SELECT id as الرقم, trans_date as التاريخ, trans_type as النوع, category as التصنيف, amount as المبلغ, description as الوصف FROM financial_transactions ORDER BY id DESC", conn)
            st.dataframe(df_trans, use_container_width=True)

    # --- 5. حالة المخزون العقاري ---
    elif menu == "حالة المخزون العقاري":
        st.subheader("إدارة الوحدات والعقارات")
        
        t_u1, t_u2 = st.tabs(["سجل الوحدات العقارية", "إضافة وحدة جديدة"])
        
        with t_u1:
            df_units = pd.read_sql_query("SELECT unit_code as كود_الوحدة, project_name as اسم_المشروع, unit_type as النوع, price as السعر, status as الحالة FROM real_estate_inventory", conn)
            st.dataframe(df_units, use_container_width=True)
            
        with t_u2:
            with st.form("add_unit_form"):
                u_code = st.text_input("كود الوحدة")
                p_name = st.text_input("اسم المشروع")
                u_type = st.selectbox("نوع الوحدة", ["سكني", "تجاري", "إداري", "أرض"])
                price = st.number_input("سعر الوحدة", min_value=0.0)
                status = st.selectbox("الحالة", ["متاحة", "محجوزة", "تم البيع"])
                
                if st.form_submit_button("حفظ الوحدة"):
                    if u_code and p_name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("INSERT INTO real_estate_inventory (unit_code, project_name, unit_type, price, status) VALUES (?,?,?,?,?)", (u_code, p_name, u_type, price, status))
                            conn.commit()
                            st.success("تم حفظ الوحدة بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("كود الوحدة مسجل بالفعل!")

    # --- 6. إدارة المستخدمين والصلاحيات ---
    elif menu == "إدارة المستخدمين والصلاحيات":
        st.subheader("سجل مستخدمي النظام والصلاحيات")
        
        df_users = pd.read_sql_query("SELECT id, username as اسم_المستخدم, role as الصلاحية, email as البريد_الإلكتروني, status as الحالة FROM users", conn)
        st.dataframe(df_users, use_container_width=True)
        
        st.markdown("### إضافة مستخدم جديد")
        with st.form("add_user"):
            u_name = st.text_input("اسم المستخدم")
            u_pass = st.text_input("كلمة المرور", type="password")
            u_role = st.selectbox("الصلاحية", ["مدير النظام", "موارد بشرية", "محاسب", "مبيعات"])
            u_email = st.text_input("البريد الإلكتروني")
            
            if st.form_submit_button("إضافة"):
                if u_name and u_pass:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO users (username, password, role, email) VALUES (?,?,?,?)", (u_name, u_pass, u_role, u_email))
                        conn.commit()
                        st.success("تمت إضافة المستخدم بنجاح!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم مسجل مسبقاً!")

    # --- 7. مركز رفع المستندات ---
    elif menu == "مركز رفع المستندات":
        st.subheader("رفع وأرشفة المستندات والتقارير")
        uploaded_file = st.file_uploader("اختر ملفاً لرفعه إلى النظام", type=["pdf", "xlsx", "docx", "jpg", "png"])
        if uploaded_file is not None:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO documents (doc_name, file_type, uploaded_by) VALUES (?,?,?)", (uploaded_file.name, uploaded_file.type, st.session_state.username))
            conn.commit()
            st.success(f"تم رفع وأرشفة الملف: **{uploaded_file.name}** بنجاح!")
            
        st.markdown("### المستندات المؤرشفة مؤخراً")
        df_docs = pd.read_sql_query("SELECT doc_name as اسم_الملف, file_type as النوع, uploaded_by as بواسطة, upload_date as تاريخ_الرفع FROM documents ORDER BY id DESC", conn)
        st.dataframe(df_docs, use_container_width=True)

    # --- 8. الملف الشخصي ---
    elif menu == "الملف الشخصي":
        st.subheader("إعدادات الحساب الشخصي")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (st.session_state.username,))
        curr_user = cursor.fetchone()
        
        if curr_user:
            st.text_input("اسم المستخدم", value=curr_user["username"], disabled=True)
            st.text_input("الصلاحية", value=curr_user["role"], disabled=True)
            new_email = st.text_input("البريد الإلكتروني", value=curr_user["email"] or "")
            new_pass = st.text_input("تحديث كلمة المرور", type="password", value=curr_user["password"])
            
            if st.button("تحديث البيانات"):
                cursor.execute("UPDATE users SET email=?, password=? WHERE username=?", (new_email, new_pass, st.session_state.username))
                conn.commit()
                st.success("تم تحديث بياناتك بنجاح!")

    conn.close()

# ---------------------------------------------------------
# 6. التوجيه النهائي
# ---------------------------------------------------------
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
