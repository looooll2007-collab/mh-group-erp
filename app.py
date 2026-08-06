import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import datetime
import uuid

# مكتبة إنشاء ملفات PDF
try:
    from fpdf import FPDF
except ImportError:
    st.error("يرجى تثبيت مكتبة fpdf عبر الأمر: pip install fpdf2")

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتصميم (Luxury Theme & CSS)
# ---------------------------------------------------------
st.set_page_config(page_title="MH GROUP ERP", layout="wide", page_icon="🏢")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    h1, h2, h3 { color: #d4af37 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: bold; }
    h1 { font-size: 2.2rem !important; }
    h2 { font-size: 1.8rem !important; border-bottom: 2px solid #d4af37; padding-bottom: 8px; }
    h3 { font-size: 1.4rem !important; }
    section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 1.15rem !important; font-weight: 600 !important; color: #c9d1d9 !important; padding: 5px 0; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, #1f242d 0%, #161b22 100%); border: 1px solid #d4af37; border-radius: 10px; padding: 15px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4); }
    div[data-testid="stMetricValue"] { color: #ffd700 !important; font-size: 1.8rem !important; }
    .stButton>button { background: linear-gradient(45deg, #d4af37, #aa7c11) !important; color: #000000 !important; font-weight: bold !important; font-size: 1rem !important; border-radius: 8px !important; border: none !important; transition: all 0.3s ease; }
    .stButton>button:hover { background: linear-gradient(45deg, #ffd700, #c59b27) !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.6); }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. إدارة قاعدة البيانات
# ---------------------------------------------------------
DB_FILE = "mh_group_erp.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            avatar_path TEXT,
            role TEXT DEFAULT 'ادمن'
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'ادمن'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT * FROM users WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (id, username, password, full_name, email, phone, avatar_path, role)
            VALUES (1, 'admin', 'mh123456', 'مدير النظام - MH GROUP', 'admin@mhgroup.com', '01000000000', '', 'ادمن')
        ''')

    # جدول الجلسات النشطة للتأكد من حفظ الدخول عبر الـ URL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول HR
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT UNIQUE,
            name TEXT,
            type TEXT,
            worker_category TEXT,
            grade TEXT,
            work_hours REAL,
            hourly_rate REAL,
            daily_rate REAL,
            workers_count INTEGER DEFAULT 0
        )
    ''')

    for col in ["emp_code TEXT", "worker_category TEXT", "daily_rate REAL"]:
        try:
            cursor.execute(f"ALTER TABLE hr ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass

    # جدول المالية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            category TEXT,
            description TEXT
        )
    ''')

    # جدول السلف
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS advances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT,
            person_name TEXT,
            amount REAL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    try:
        cursor.execute("ALTER TABLE advances ADD COLUMN emp_code TEXT")
    except sqlite3.OperationalError:
        pass

    # جدول العقارات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prop_code TEXT UNIQUE,
            prop_type TEXT,
            base_price REAL,
            expenses REAL,
            total_price REAL,
            selling_price REAL DEFAULT 0,
            status TEXT DEFAULT 'متاح'
        )
    ''')

    # جدول الـ IT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS it_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name TEXT,
            work_hours REAL,
            hourly_rate REAL
        )
    ''')

    # جدول المستثمرين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_name TEXT,
            prop_code TEXT,
            share_percentage REAL,
            invested_amount REAL
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. دالة إنشاء ملف PDF للأجور
# ---------------------------------------------------------
def generate_payroll_pdf(df_payroll):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="MH GROUP ERP - Payroll Summary Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(25, 8, "Code", 1)
    pdf.cell(45, 8, "Name", 1)
    pdf.cell(30, 8, "Category", 1)
    pdf.cell(25, 8, "Daily Rate", 1)
    pdf.cell(25, 8, "Advances", 1)
    pdf.cell(30, 8, "Net Salary", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 9)
    for idx, row in df_payroll.iterrows():
        def safe_txt(val):
            s = str(val if val is not None else '')
            return s.encode('latin-1', 'replace').decode('latin-1')

        pdf.cell(25, 8, safe_txt(row['الكود الوظيفي']), 1)
        pdf.cell(45, 8, safe_txt(row['اسم الموظف/المورد'])[:20], 1)
        pdf.cell(30, 8, safe_txt(row['نوع العامل']), 1)
        pdf.cell(25, 8, f"{float(row['اليومية'] or 0):.1f}", 1)
        pdf.cell(25, 8, f"{float(row['إجمالي السلف'] or 0):.1f}", 1)
        pdf.cell(30, 8, f"{float(row['الصافي المستحق'] or 0):.1f}", 1)
        pdf.ln()
        
    pdf_file_path = "payroll_report.pdf"
    pdf.output(pdf_file_path)
    return pdf_file_path

# ---------------------------------------------------------
# 4. نظام الجلسة وتثبيت الدخول عبر URL (Query Params)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

query_params = st.query_params
if "session" in query_params and not st.session_state['logged_in']:
    session_token = query_params["session"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role FROM active_sessions WHERE token = ?", (session_token,))
    sess_data = cursor.fetchone()
    conn.close()
    
    if sess_data:
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = sess_data[0]
        st.session_state['user_role'] = sess_data[1]

def login():
    st.markdown("<h1 style='text-align: center; color: #ffd700;'>MH GROUP للاستثمار والتطوير العقاري</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>نظام إدارة الموارد ERP</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username_input, password_input))
            user = cursor.fetchone()
            
            if user:
                token = str(uuid.uuid4())
                cursor.execute("INSERT INTO active_sessions (token, user_id, role) VALUES (?, ?, ?)", (token, user[0], user[1]))
                conn.commit()
                conn.close()
                
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['user_role'] = user[1]
                
                st.query_params["session"] = token
                st.rerun()
            else:
                conn.close()
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

if not st.session_state['logged_in']:
    login()
    st.stop()

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT full_name, avatar_path, role FROM users WHERE id = ?", (st.session_state['user_id'],))
current_user = cursor.fetchone()
conn.close()

st.sidebar.title("🏢 MH GROUP ERP")
if current_user:
    if current_user[1] and os.path.exists(current_user[1]):
        st.sidebar.image(current_user[1], width=100)
    st.sidebar.markdown(f"**أهلاً بك، {current_user[0]}**")
    st.sidebar.caption(f"الصلاحية الحالية: `{current_user[2]}`")

st.sidebar.markdown("---")

user_role = st.session_state['user_role']
allowed_menu = ["الملف الشخصي"]

if user_role == "ادمن":
    allowed_menu = [
        "الرئيسية (Dashboard)",
        "الملف الشخصي",
        "إدارة المستخدمين والصلاحيات",
        "رفع المستندات",
        "الموارد البشرية (HR)",
        "المالية والأجور",
        "المخزون العقاري",
        "قسم تكنولوجيا المعلومات (IT)",
        "أسهم المستثمرين"
    ]
elif user_role == "HR":
    allowed_menu.insert(0, "الموارد البشرية (HR)")
elif user_role == "محاسب":
    allowed_menu.insert(0, "المالية والأجور")
    allowed_menu.append("رفع المستندات")
elif user_role == "IT":
    allowed_menu.insert(0, "قسم تكنولوجيا المعلومات (IT)")
elif user_role == "عقارات":
    allowed_menu.insert(0, "المخزون العقاري")
    allowed_menu.append("أسهم المستثمرين")

menu = st.sidebar.radio("📋 الأقسام المتاحة:", allowed_menu)

if st.sidebar.button("🚪 تسجيل الخروج"):
    if "session" in st.query_params:
        token_to_del = st.query_params["session"]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_sessions WHERE token = ?", (token_to_del,))
        conn.commit()
        conn.close()
        st.query_params.clear()
        
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['user_role'] = None
    st.rerun()

# ---------------------------------------------------------
# 5. Dashboard
# ---------------------------------------------------------
if menu == "الرئيسية (Dashboard)":
    st.header("📊 لوحة التحكم والأداء العام")
    
    conn = get_connection()
    df_fin = pd.read_sql_query("SELECT * FROM finance", conn)
    df_prop = pd.read_sql_query("SELECT * FROM properties", conn)
    df_hr = pd.read_sql_query("SELECT * FROM hr", conn)
    conn.close()
    
    total_rev = df_fin[df_fin['type'] == 'إيراد']['amount'].sum() if not df_fin.empty else 0
    total_exp = df_fin[df_fin['type'] == 'مصروف']['amount'].sum() if not df_fin.empty else 0
    net_profit = total_rev - total_exp
    total_props = len(df_prop)
    total_employees = len(df_hr)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي الإيرادات", f"{total_rev:,.2f} ج.م")
    c2.metric("إجمالي المصروفات", f"{total_exp:,.2f} ج.م")
    c3.metric("صافي الأرباح", f"{net_profit:,.2f} ج.م")
    c4.metric("العقارات / القوة البشرية", f"{total_props} عقار / {total_employees} فرد")
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📈 توزيع التدفقات المالية")
        if not df_fin.empty:
            fig1 = px.pie(df_fin, values='amount', names='type', title="نسب الإيرادات والمصروفات", hole=0.4, color_discrete_sequence=['#d4af37', '#e74c3c'])
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("لا توجد بيانات مالية مسجلة بعد.")
            
    with col_chart2:
        st.subheader("🏠 حالة المخزون العقاري")
        if not df_prop.empty:
            fig2 = px.pie(df_prop, names='status', title="حالة العقارات", hole=0.4, color_discrete_sequence=['#2ecc71', '#f39c12'])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("لا توجد عقارات مسجلة بالمخزون بعد.")

# ---------------------------------------------------------
# 6. قسم الموارد البشرية (HR)
# ---------------------------------------------------------
elif menu == "الموارد البشرية (HR)":
    st.header("👥 قسم الموارد البشرية والعمالة")
    
    tab1, tab2, tab3 = st.tabs(["➕ إضافة جديد", "📋 عرض وحذف السجلات", "✏️ تعديل بيانات"])
    
    with tab1:
        with st.form("hr_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                emp_code = st.text_input("الكود الوظيفي (مثال: EMP-101)")
                name = st.text_input("الاسم الكامل")
                entry_type = st.selectbox("نوع القيد", ["موظف", "مورد", "عامل عادية"])
                worker_category = st.selectbox("نوع العامل / التخصص", ["نحات", "مبيض", "عامل", "سباك", "كهربائي", "إداري", "أخرى"])
            with col_b:
                grade = st.text_input("الدرجة الوظيفية / الوصف")
                daily_rate = st.number_input("اليومية (ج.م)", min_value=0.0, step=50.0)
                hourly_rate = st.number_input("سعر الساعة (ج.م)", min_value=0.0, step=5.0)
                work_hours = st.number_input("ساعات العمل المسجلة", min_value=0.0, step=0.5)
                workers_count = st.number_input("عدد العمال التابعين (للموردين)", min_value=0, step=1)
            
            submit = st.form_submit_button("حفظ البيانات")
            if submit:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO hr (emp_code, name, type, worker_category, grade, work_hours, hourly_rate, daily_rate, workers_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (emp_code, name, entry_type, worker_category, grade, work_hours, hourly_rate, daily_rate, workers_count))
                    conn.commit()
                    st.success("تم الحفظ بنجاح!")
                except Exception as e:
                    st.error("الكود الوظيفي مكرر أو حدث خطأ!")
                finally:
                    conn.close()
                st.rerun()

    with tab2:
        conn = get_connection()
        df_hr = pd.read_sql_query("SELECT id, emp_code as 'الكود الوظيفي', name as 'الاسم', type as 'النوع', worker_category as 'نوع العامل', daily_rate as 'اليومية', hourly_rate as 'سعر الساعة', work_hours as 'ساعات العمل' FROM hr", conn)
        st.dataframe(df_hr, use_container_width=True)
        
        if not df_hr.empty:
            st.subheader("🗑️ حذف سجل من HR")
            hr_to_delete = st.selectbox("اختر السجل المراد حذفه (ID)", df_hr['id'].tolist())
            if st.button("حذف السجل المحدد"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM hr WHERE id = ?", (hr_to_delete,))
                conn.commit()
                st.success("تم الحذف!")
                conn.close()
                st.rerun()
        conn.close()

    with tab3:
        conn = get_connection()
        df_hr_raw = pd.read_sql_query("SELECT * FROM hr", conn)
        if not df_hr_raw.empty:
            selected_hr_id = st.selectbox("اختر للتعديل", df_hr_raw['id'].tolist())
            hr_row = df_hr_raw[df_hr_raw['id'] == selected_hr_id].iloc[0]
            
            with st.form("hr_edit_form"):
                e_code = st.text_input("الكود الوظيفي", value=str(hr_row['emp_code'] or ''))
                e_name = st.text_input("الاسم", value=str(hr_row['name']))
                e_cat = st.selectbox("نوع العامل", ["نحات", "مبيض", "عامل", "سباك", "كهربائي", "إداري", "أخرى"], index=0)
                e_daily = st.number_input("اليومية", value=float(hr_row['daily_rate'] or 0.0))
                e_hours = st.number_input("ساعات العمل", value=float(hr_row['work_hours'] or 0.0))
                e_rate = st.number_input("سعر الساعة", value=float(hr_row['hourly_rate'] or 0.0))
                
                edit_sub = st.form_submit_button("حفظ التعديل")
                if edit_sub:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE hr SET emp_code=?, name=?, worker_category=?, daily_rate=?, work_hours=?, hourly_rate=? WHERE id=?
                    """, (e_code, e_name, e_cat, e_daily, e_hours, e_rate, selected_hr_id))
                    conn.commit()
                    st.success("تم التعديل بنجاح!")
                    conn.close()
                    st.rerun()
        conn.close()

# ---------------------------------------------------------
# 7. قسم المالية والأجور (Payroll & Finance)
# ---------------------------------------------------------
elif menu == "المالية والأجور":
    st.header("💰 قسم المالية وحساب الأجور والسُلف")
    
    tab1, tab2, tab3 = st.tabs(["📊 كشف الأجور والتصدير PDF/Excel", "💸 تسجيل السُلف", "🧾 الخزينة والمعاملات المالية"])
    
    with tab1:
        st.subheader("📑 كشف الأجور والصافي لكل العاملين")
        conn = get_connection()
        df_hr_all = pd.read_sql_query("SELECT * FROM hr", conn)
        df_adv_all = pd.read_sql_query("SELECT emp_code, SUM(amount) as total_adv FROM advances GROUP BY emp_code", conn)
        conn.close()
        
        if not df_hr_all.empty:
            payroll_data = []
            for _, emp in df_hr_all.iterrows():
                code = emp['emp_code'] or '---'
                name = emp['name']
                cat = emp['worker_category'] or 'عامل'
                daily = emp['daily_rate'] or 0.0
                h_rate = emp['hourly_rate'] or 0.0
                h_worked = emp['work_hours'] or 0.0
                
                earned = (daily) + (h_rate * h_worked)
                adv_row = df_adv_all[df_adv_all['emp_code'] == code] if not df_adv_all.empty else pd.DataFrame()
                adv_amt = adv_row['total_adv'].values[0] if not adv_row.empty else 0.0
                net = earned - adv_amt
                
                payroll_data.append({
                    "الكود الوظيفي": code,
                    "اسم الموظف/المورد": name,
                    "نوع العامل": cat,
                    "اليومية": daily,
                    "سعر الساعة": h_rate,
                    "ساعات العمل": h_worked,
                    "إجمالي المستحق": earned,
                    "إجمالي السلف": adv_amt,
                    "الصافي المستحق": net
                })
            
            df_payroll = pd.DataFrame(payroll_data)
            st.dataframe(df_payroll, use_container_width=True)
            
            st.markdown("---")
            col_pdf1, col_pdf2 = st.columns(2)
            
            with col_pdf1:
                if st.button("📥 إنشاء وتنزيل كشف الأجور PDF"):
                    try:
                        pdf_path = generate_payroll_pdf(df_payroll)
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="💾 اضغط هنا لتحميل ملف الـ PDF",
                                data=f,
                                file_name="MH_GROUP_Payroll_Report.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء تصدير PDF: {e}")

            with col_pdf2:
                csv_data = df_payroll.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📊 تنزيل كشف الأجور كملف Excel (عربي)",
                    data=csv_data,
                    file_name="MH_GROUP_Payroll_Report.csv",
                    mime="text/csv"
                )
        else:
            st.info("لا توجد بيانات موظفين أو عمال مسجلة بعد في قسم HR.")

    with tab2:
        st.subheader("💵 تسجيل سلفة جديدة")
        conn = get_connection()
        df_hr_list = pd.read_sql_query("SELECT emp_code, name FROM hr", conn)
        
        if not df_hr_list.empty:
            with st.form("adv_form"):
                emp_choice = st.selectbox("اختر الموظف / العامل", df_hr_list['emp_code'] + " - " + df_hr_list['name'])
                selected_code = emp_choice.split(" - ")[0]
                selected_name = emp_choice.split(" - ")[1]
                
                adv_amount = st.number_input("مبلغ السلفة (ج.م)", min_value=0.0, step=50.0)
                submit_adv = st.form_submit_button("تسجيل السلفة")
                if submit_adv:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO advances (emp_code, person_name, amount) VALUES (?, ?, ?)",
                                   (selected_code, selected_name, adv_amount))
                    conn.commit()
                    st.success(f"تم تسجيل سلفة بمبلغ {adv_amount} ج.م لـ {selected_name}")
                    conn.close()
                    st.rerun()
                    
            st.subheader("📜 سجل السُلف المسجلة")
            df_adv_logs = pd.read_sql_query("SELECT id, emp_code as 'الكود', person_name as 'الاسم', amount as 'المبلغ', date_added as 'التاريخ' FROM advances", conn)
            st.dataframe(df_adv_logs, use_container_width=True)
            if not df_adv_logs.empty:
                adv_del_id = st.selectbox("حذف سلفة (ID)", df_adv_logs['id'].tolist())
                if st.button("حذف السلفة"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM advances WHERE id = ?", (adv_del_id,))
                    conn.commit()
                    st.success("تم الحذف!")
                    conn.close()
                    st.rerun()
        conn.close()

    with tab3:
        st.subheader("💳 الخزينة العامة والإيرادات / المصروفات")
        with st.form("fin_form"):
            fin_type = st.selectbox("نوع المعاملة", ["إيراد", "مصروف"])
            amount = st.number_input("المبلغ (ج.م)", min_value=0.0, step=100.0)
            category = st.text_input("التصنيف (مثال: صيانة, توريدات, بيع عقار)")
            description = st.text_area("تفاصيل المعاملة")
            
            submit = st.form_submit_button("تسجيل المعاملة")
            if submit:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO finance (type, amount, category, description) VALUES (?, ?, ?, ?)",
                               (fin_type, amount, category, description))
                conn.commit()
                conn.close()
                st.success("تم تسجيل المعاملة المالية!")
                st.rerun()

        conn = get_connection()
        df_fin = pd.read_sql_query("SELECT * FROM finance", conn)
        st.dataframe(df_fin, use_container_width=True)
        if not df_fin.empty:
            fin_to_delete = st.selectbox("اختر ID معاملة لحذفها", df_fin['id'].tolist())
            if st.button("حذف المعاملة المالية"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM finance WHERE id = ?", (fin_to_delete,))
                conn.commit()
                st.success("تم الحذف!")
                conn.close()
                st.rerun()
        conn.close()

# ---------------------------------------------------------
# 8. قسم المخزون العقاري
# ---------------------------------------------------------
elif menu == "المخزون العقاري":
    st.header("🏠 إدارة المخزون العقاري والتكاليف")
    
    tab1, tab2, tab3 = st.tabs(["➕ إضافة عقار جديد", "📋 قائمة العقارات وحذفها", "✏️ تعديل عقار"])
    
    with tab1:
        with st.form("prop_form"):
            prop_code = st.text_input("كود العقار")
            prop_type = st.selectbox("نوع العقار", ["شقة", "فيلا", "محل تجاري", "أرض", "مبنى كامل"])
            base_price = st.number_input("سعر الشراء", min_value=0.0, step=1000.0)
            expenses = st.number_input("المصاريف والتطوير", min_value=0.0, step=500.0)
            selling_price = st.number_input("سعر البيع المستهدف", min_value=0.0, step=1000.0)
            status = st.selectbox("حالة العقار", ["متاح", "مباع"])
            
            submit = st.form_submit_button("حفظ العقار")
            if submit:
                total_price = base_price + expenses
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO properties (prop_code, prop_type, base_price, expenses, total_price, selling_price, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (prop_code, prop_type, base_price, expenses, total_price, selling_price, status))
                    conn.commit()
                    st.success("تم إضافة العقار بنجاح!")
                except Exception as e:
                    st.error("كود العقار مكرر!")
                finally:
                    conn.close()
                st.rerun()

    with tab2:
        conn = get_connection()
        df_prop = pd.read_sql_query("SELECT * FROM properties", conn)
        if not df_prop.empty:
            st.dataframe(df_prop, use_container_width=True)
            prop_to_delete = st.selectbox("اختر كود العقار للحذف", df_prop['prop_code'].unique())
            if st.button("حذف العقار المحدد"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM properties WHERE prop_code = ?", (prop_to_delete,))
                cursor.execute("DELETE FROM investors WHERE prop_code = ?", (prop_to_delete,))
                conn.commit()
                st.success("تم حذف العقار!")
                conn.close()
                st.rerun()
        conn.close()

    with tab3:
        conn = get_connection()
        df_prop = pd.read_sql_query("SELECT * FROM properties", conn)
        if not df_prop.empty:
            selected_code = st.selectbox("اختر العقار للتعديل", df_prop['prop_code'].unique())
            p_row = df_prop[df_prop['prop_code'] == selected_code].iloc[0]
            
            with st.form("prop_edit_form"):
                e_base = st.number_input("السعر الأساسي", value=float(p_row['base_price']))
                e_exp = st.number_input("المصاريف", value=float(p_row['expenses']))
                e_sell = st.number_input("سعر البيع", value=float(p_row['selling_price']))
                e_status = st.selectbox("الحالة", ["متاح", "مباع"], index=0 if p_row['status'] == 'متاح' else 1)
                
                edit_prop_btn = st.form_submit_button("حفظ تعديل العقار")
                if edit_prop_btn:
                    e_total = e_base + e_exp
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE properties 
                        SET base_price=?, expenses=?, total_price=?, selling_price=?, status=? 
                        WHERE prop_code=?
                    """, (e_base, e_exp, e_total, e_sell, e_status, selected_code))
                    conn.commit()
                    st.success("تم التحديث!")
                    conn.close()
                    st.rerun()
        conn.close()

# ---------------------------------------------------------
# 9. قسم تكنولوجيا المعلومات (IT)
# ---------------------------------------------------------
elif menu == "قسم تكنولوجيا المعلومات (IT)":
    st.header("💻 قسم تكنولوجيا المعلومات (IT)")
    
    tab_it1, tab_it2 = st.tabs(["➕ تسجيل ساعات ودعم IT", "📋 سجلات IT المسجلة"])
    
    with tab_it1:
        with st.form("it_form"):
            emp_name = st.text_input("اسم المهندس / تقني الـ IT")
            work_hours = st.number_input("عدد ساعات العمل المسجلة", min_value=0.0, step=0.5)
            hourly_rate = st.number_input("سعر الساعة (ج.م)", min_value=0.0, step=10.0)
            
            submit_it = st.form_submit_button("حفظ البيانات")
            if submit_it:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO it_logs (emp_name, work_hours, hourly_rate)
                    VALUES (?, ?, ?)
                """, (emp_name, work_hours, hourly_rate))
                conn.commit()
                conn.close()
                st.success("تم تسجيل البيانات بنجاح!")
                st.rerun()
                
    with tab_it2:
        conn = get_connection()
        df_it = pd.read_sql_query("SELECT id, emp_name as 'اسم المهندس', work_hours as 'ساعات العمل', hourly_rate as 'سعر الساعة', (work_hours * hourly_rate) as 'إجمالي الإستحقاق' FROM it_logs", conn)
        st.dataframe(df_it, use_container_width=True)
        if not df_it.empty:
            it_to_del = st.selectbox("حذف سجل IT (ID)", df_it['id'].tolist())
            if st.button("حذف السجل"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM it_logs WHERE id = ?", (it_to_del,))
                conn.commit()
                st.success("تم الحذف!")
                conn.close()
                st.rerun()
        conn.close()

# ---------------------------------------------------------
# 10. قسم أسهم المستثمرين
# ---------------------------------------------------------
elif menu == "أسهم المستثمرين":
    st.header("📈 إدارة أسهم الشركاء والمستثمرين")
    
    tab_inv1, tab_inv2 = st.tabs(["➕ ربط مستثمر بعقار", "📋 جدول توزيع الحصص والأسهم"])
    
    with tab_inv1:
        conn = get_connection()
        df_props_list = pd.read_sql_query("SELECT prop_code, prop_type, total_price FROM properties", conn)
        conn.close()
        
        if not df_props_list.empty:
            with st.form("investor_form"):
                investor_name = st.text_input("اسم المستثمر / الشريك")
                selected_prop = st.selectbox("اختر العقار", df_props_list['prop_code'])
                share_percentage = st.number_input("نسبة الشراكة (%)", min_value=0.0, max_value=100.0, step=1.0)
                invested_amount = st.number_input("المبلغ المستثمر (ج.م)", min_value=0.0, step=1000.0)
                
                submit_inv = st.form_submit_button("حفظ بيانات المستثمر")
                if submit_inv:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO investors (investor_name, prop_code, share_percentage, invested_amount)
                        VALUES (?, ?, ?, ?)
                    """, (investor_name, selected_prop, share_percentage, invested_amount))
                    conn.commit()
                    conn.close()
                    st.success("تمت إضافة المستثمر بنجاح!")
                    st.rerun()
        else:
            st.info("قم بإضافة عقارات في المخزون العقاري أولاً لتتمكن من إضافة مستثمرين عليها.")

    with tab_inv2:
        conn = get_connection()
        df_inv = pd.read_sql_query("""
            SELECT i.id, i.investor_name as 'اسم المستثمر', i.prop_code as 'كود العقار', 
                   p.prop_type as 'نوع العقار', i.share_percentage as 'النسبة (%)', 
                   i.invested_amount as 'المبلغ المستثمر'
            FROM investors i
            LEFT JOIN properties p ON i.prop_code = p.prop_code
        """, conn)
        st.dataframe(df_inv, use_container_width=True)
        if not df_inv.empty:
            inv_to_del = st.selectbox("حذف مستثمر (ID)", df_inv['id'].tolist())
            if st.button("حذف الشريك/المستثمر"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM investors WHERE id = ?", (inv_to_del,))
                conn.commit()
                st.success("تم الحذف!")
                conn.close()
                st.rerun()
        conn.close()

# ---------------------------------------------------------
# 11. إدارة المستخدمين
# ---------------------------------------------------------
elif menu == "إدارة المستخدمين والصلاحيات":
    st.header("🔐 إدارة المستخدمين والصلاحيات")
    
    tab_u1, tab_u2 = st.tabs(["إضافة مستخدم جديد", "عرض المستخدمين وحذفهم"])
    
    with tab_u1:
        with st.form("add_user_form"):
            new_username = st.text_input("اسم المستخدم")
            new_password = st.text_input("كلمة المرور", type="password")
            new_fullname = st.text_input("الاسم الكامل")
            new_email = st.text_input("البريد الإلكتروني")
            new_phone = st.text_input("رقم الهاتف")
            new_role = st.selectbox("الصلاحية", ["ادمن", "HR", "محاسب", "IT", "عقارات"])
            
            submit_user = st.form_submit_button("إضافة المستخدم")
            if submit_user:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, email, phone, avatar_path, role)
                        VALUES (?, ?, ?, ?, ?, '', ?)
                    """, (new_username, new_password, new_fullname, new_email, new_phone, new_role))
                    conn.commit()
                    st.success("تم إضافته بنجاح!")
                except Exception as e:
                    st.error("اسم المستخدم مكرر!")
                finally:
                    conn.close()
                st.rerun()

    with tab_u2:
        conn = get_connection()
        df_users = pd.read_sql_query("SELECT id, username, full_name, email, phone, role FROM users", conn)
        st.dataframe(df_users, use_container_width=True)
        deletable_users = df_users[df_users['id'] != 1]['username'].tolist()
        if deletable_users:
            user_to_del = st.selectbox("حذف مستخدم", deletable_users)
            if st.button("حذف المستخدم"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                conn.commit()
                st.success("تم الحذف!")
                conn.close()
                st.rerun()
        conn.close()

# ---------------------------------------------------------
# 12. الملف الشخصي
# ---------------------------------------------------------
elif menu == "الملف الشخصي":
    st.header("👤 الملف الشخصي وإدارة الحساب")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, full_name, email, phone, avatar_path FROM users WHERE id = ?", (st.session_state['user_id'],))
    u_data = cursor.fetchone()
    conn.close()
    
    col_prof1, col_prof2 = st.columns([1, 2])
    
    with col_prof1:
        st.subheader("الصورة الشخصية")
        if u_data[5] and os.path.exists(u_data[5]):
            st.image(u_data[5], width=180)
        else:
            st.info("لا توجد صورة مضافة.")
            
        avatar_file = st.file_uploader("تحديث الصورة", type=['png', 'jpg', 'jpeg'])
        if avatar_file is not None:
            if not os.path.exists("avatars"):
                os.makedirs("avatars")
            avatar_path = os.path.join("avatars", f"user_{st.session_state['user_id']}_{avatar_file.name}")
            with open(avatar_path, "wb") as f:
                f.write(avatar_file.getbuffer())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET avatar_path = ? WHERE id = ?", (avatar_path, st.session_state['user_id']))
            conn.commit()
            conn.close()
            st.success("تم تحديث الصورة!")
            st.rerun()

    with col_prof2:
        st.subheader("تعديل بيانات الحساب")
        with st.form("profile_form"):
            full_name_val = st.text_input("الاسم الكامل", value=u_data[2] if u_data[2] else "")
            email_val = st.text_input("البريد الإلكتروني", value=u_data[3] if u_data[3] else "")
            phone_val = st.text_input("رقم الهاتف", value=u_data[4] if u_data[4] else "")
            username_val = st.text_input("اسم المستخدم (Username)", value=u_data[0])
            password_val = st.text_input("كلمة المرور جديدة (Password)", value=u_data[1], type="password")
            
            save_profile = st.form_submit_button("حفظ التعديلات")
            if save_profile:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        UPDATE users 
                        SET full_name = ?, email = ?, phone = ?, username = ?, password = ?
                        WHERE id = ?
                    """, (full_name_val, email_val, phone_val, username_val, password_val, st.session_state['user_id']))
                    conn.commit()
                    st.success("تم تحديث الحساب بنجاح!")
                except Exception as e:
                    st.error("اسم المستخدم هذا مستخدم بالفعل!")
                finally:
                    conn.close()
                st.rerun()

# ---------------------------------------------------------
# 13. رفع وإدارة المستندات والعقود
# ---------------------------------------------------------
elif menu == "رفع المستندات":
    st.header("📁 مركز أرشفة وإدارة المستندات والعقود")
    
    with st.form("upload_doc_form", clear_on_submit=True):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            uploaded_file = st.file_uploader("اختر المستند لرفعه", type=['pdf', 'png', 'jpg', 'jpeg'])
        with col_u2:
            doc_type = st.selectbox("نوع المستند / التصنيف", [
                "عقد أرض",
                "عقد استثمار",
                "عقد إيجار",
                "ملف تحويل أموال",
                "أخرى"
            ])
            doc_description = st.text_input("ملاحظات / وصف مختصر للمستند")
            
        submit_upload = st.form_submit_button("📤 رفع وحفظ المستند")
        
        if submit_upload:
            if uploaded_file is not None:
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                
                file_path = os.path.join("uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if 'docs_meta' not in st.session_state:
                    st.session_state['docs_meta'] = {}
                
                st.session_state['docs_meta'][uploaded_file.name] = {
                    "type": doc_type,
                    "desc": doc_description
                }
                
                st.success(f"تم رفع الملف `{uploaded_file.name}` بنجاح وتصنيفه كـ ({doc_type})!")
                st.rerun()
            else:
                st.warning("يرجى اختيار ملف أولاً قبل الضغط على حفظ.")

    st.divider()
    st.subheader("📄 المستندات والعقود المرفوعة")
    
    if os.path.exists("uploads"):
        files = os.listdir("uploads")
        if files:
            for file in files:
                file_path = os.path.join("uploads", file)
                file_ext = os.path.splitext(file)[1].lower()
                
                meta = st.session_state.get('docs_meta', {}).get(file, {"type": "غير محدد", "desc": "-"})
                
                with st.expander(f"📁 {file}  |  🏷️ **التصنيف:** {meta['type']}"):
                    col_info, col_actions = st.columns([2, 1])
                    
                    with col_info:
                        st.write(f"**اسم الملف:** `{file}`")
                        st.write(f"**نوع المستند:** {meta['type']}")
                        st.write(f"**الوصف/الملاحظات:** {meta['desc']}")
                    
                    with col_actions:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="💾 تنزيل المستند",
                                data=f,
                                file_name=file,
                                mime="application/octet-stream",
                                key=f"down_{file}"
                            )
                        
                        if st.button("🗑️ حذف المستند", key=f"del_file_{file}"):
                            os.remove(file_path)
                            if 'docs_meta' in st.session_state and file in st.session_state['docs_meta']:
                                del st.session_state['docs_meta'][file]
                            st.success("تم حذف الملف!")
                            st.rerun()

                    st.markdown("---")
                    st.caption("🔍 **معاينة المستند:**")
                    if file_ext in ['.png', '.jpg', '.jpeg']:
                        st.image(file_path, use_container_width=True)
                    elif file_ext == '.pdf':
                        st.info("📄 ملف PDF جاهز للتحميل عبر الزر أعلاه (أو يمكنك معاينته عبر المتصفح).")
        else:
            st.info("لا توجد مستندات مرفوعة حالياً.")
    else:
        st.info("مجلد المستندات فارغ.")
