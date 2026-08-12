import datetime
import os
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والثيم والتصميم المطابق للصور
# ==========================================
st.set_page_config(
    page_title="MH GROUP ERP - النظام المتكامل",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* توجيه الصفحة من اليمين ليسار (RTL) وتطبيق الخطوط العصرية */
    .stApp {
        background-color: #F8FAFC !important;
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تخصيص القائمة الجانبية لتطابق التصميم الداكن الفاخر */
    section[data-testid="stSidebar"] {
        background-color: #0A1128 !important;
        border-left: 1px solid #1E293B !important;
    }
    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    
    /* الهيدر والعناوين الرئيسية */
    .main-header {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0A1128;
        margin-bottom: 15px;
    }
    
    /* بطاقات المترك (Metrics) البيضاء المطابقة للصورة */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] label {
        color: #64748B !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0A1128 !important;
        font-weight: 800;
    }

    /* الكاردات التنفيذية والبيضاء */
    .executive-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* الأزرار المخصصة */
    .stButton>button {
        background-color: #0A1128 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
    }
    .stButton>button:hover {
        background-color: #D97706 !important;
    }
</style>
""", unsafe_allow_html=True)

UPLOAD_DIR = "uploads_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 2. إنشاء وهجرة قاعدة البيانات تلقائياً
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()
        
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT,
                email TEXT,
                avatar_path TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS financial_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trans_type TEXT,
                department TEXT,
                amount REAL,
                description TEXT,
                trans_date TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS employees (
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
            )""",
            """CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT UNIQUE,
                name TEXT,
                location TEXT,
                price REAL,
                expenses REAL DEFAULT 0.0,
                sale_price REAL DEFAULT 0.0,
                status TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                property_custom_id TEXT,
                investment_amount REAL,
                investment_ratio REAL,
                return_rate REAL,
                total_returns REAL,
                start_date TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                department TEXT,
                action TEXT,
                status TEXT,
                ip_address TEXT,
                timestamp TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                department TEXT,
                issue_text TEXT,
                status TEXT,
                ticket_date TEXT
            )"""
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
            
        # إنشاء حساب المدير الافتراضي إذا لم يكن موجوداً
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role, phone, email, avatar_path) VALUES (?, ?, ?, ?, ?, ?)",
                ('admin', 'admin123', 'Admin', '01000000000', 'admin@mhgroup.com', '')
            )
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
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute(
                "INSERT INTO audit_logs (username, department, action, status, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (username, department, action, status, "127.0.0.1", now)
            )
            conn.commit()
    except Exception:
        pass

# ==========================================
# 3. شاشة تسجيل الدخول المطابقة للتصميم
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 85vh;">
            <div style="background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,00,0,0.1); width: 600px; text-align: right;">
                <h2 style="color: #0A1128; font-weight: 800; margin-bottom: 5px;">Sign In</h2>
                <p style="color: #64748B; margin-bottom: 25px;">Welcome back! Please login to your account</p>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        login_user = st.text_input("Username", key="login_usr")
        login_pass = st.text_input("Password", type="password", key="login_pwd")
        remember_me = st.checkbox("Remember me")
        
        if st.button("Login", use_container_width=True):
            un = login_user.strip()
            pw = login_pass.strip()
            with sqlite3.connect("mh_group_erp.db") as conn:
                res = conn.execute("SELECT role FROM users WHERE username = ? AND password = ?", (un, pw)).fetchone()
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = un
                log_audit_action(un, "النظام", "تسجيل الدخول بنجاح")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")
                
    with col_l2:
        st.markdown("""
            <div style="text-align: center; padding-top: 20px;">
                <h3 style="color: #0A1128; font-weight: 800;">MH GROUP</h3>
                <p style="color: #0A1128; font-weight: 700; margin-top: 10px;">مرحباً بك في MH GROUP ERP</p>
                <p style="color: #64748B; font-size: 0.85rem;">نظام متكامل لإدارة أعمال الاستثمار والتطوير العقاري</p>
                <div style="margin-top: 25px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="background: #F8FAFC; padding: 8px; border-radius: 6px; font-size: 0.8rem; border: 1px solid #E2E8F0;">🛡️ أمان عالي</div>
                    <div style="background: #F8FAFC; padding: 8px; border-radius: 6px; font-size: 0.8rem; border: 1px solid #E2E8F0;">📊 إدارة ذكية</div>
                    <div style="background: #F8FAFC; padding: 8px; border-radius: 6px; font-size: 0.8rem; border: 1px solid #E2E8F0;">📑 تقارير دقيقة</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

else:
    # ==========================================
    # 4. القائمة الجانبية والروابط (مطابقة للصورة تماماً)
    # ==========================================
    st.sidebar.markdown("""
        <div style="text-align: center; padding: 10px 0 20px 0; border-bottom: 1px solid #1E293B;">
            <h2 style="color: #F8FAFC; font-weight: 900; margin: 0;">MH GROUP 🏢</h2>
            <p style="color: #94A3B8; font-size: 0.8rem; margin-top: 5px;">مرحباً، <b>{}</b></p>
        </div>
    """.format(st.session_state['username']), unsafe_allow_html=True)

    menu_options = [
        "📊 لوحة التحكم",
        "👥 المستخدمين",
        "💸 المعاملات المالية",
        "💰 الإدارة المالية",
        "👷 الموارد البشرية",
        "🏢 العقارات",
        "🤝 المستثمرين",
        "💻 تقنية المعلومات",
        "⏱️ سجل العمليات",
        "⚠️ الإبلاغ عن مشكلة"
    ]

    selected_page = st.sidebar.radio("التنقل بين الأقسام:", menu_options, label_visibility="collapsed")

    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("Logout", use_container_width=True):
        log_audit_action(st.session_state["username"], "النظام", "تسجيل خروج آمن")
        st.session_state["logged_in"] = False
        st.rerun()

    # ==========================================
    # 5. محتوى الأقسام والشاشات وتفعيلها بالكامل
    # ==========================================
    
    # --- 1. لوحة التحكم (Dashboard) ---
    if selected_page == "📊 لوحة التحكم":
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown("<h1 class='main-header'>Dashboard</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #64748B; margin-top: -10px;'>Welcome, {st.session_state['username']}</p>", unsafe_allow_html=True)
        with c_head2:
            st.info(f"📅 {datetime.date.today().strftime('%d/%m/%Y')} - {datetime.date.today().replace(day=1).strftime('%d/%m/%Y')}")

        # جسابات الإحصائيات
        df_fin = safe_read_sql("SELECT trans_type, amount FROM financial_transactions")
        tot_inc = df_fin[df_fin["trans_type"] == "واردات (إيرادات)"]["amount"].sum() if not df_fin.empty else 0.0
        tot_exp = df_fin[df_fin["trans_type"] == "صادرات (مصروفات)"]["amount"].sum() if not df_fin.empty else 0.0
        net_prof = tot_inc - tot_exp

        df_props = safe_read_sql("SELECT price FROM properties")
        prop_val = df_props["price"].sum() if not df_props.empty else 0.0

        # المرتكزات الأربعة المطابقة للصورة تماماً
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("إجمالي الإيرادات", f"{tot_inc:,.0f}", "+12.5% عن الشهر الماضي")
        with m2:
            st.metric("إجمالي المصروفات", f"{tot_exp:,.0f}", "-3.2% عن الشهر الماضي")
        with m3:
            st.metric("صافي الأرباح", f"{net_prof:,.0f}", "+18.7% عن الشهر الماضي")
        with m4:
            st.metric("قيمة العقارات", f"{prop_val:,.0f}", "إجمالي قيمة المحفظة العقارية")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("""
                <div class='executive-card'>
                    <h3>نظرة عامة على الأداء</h3>
                    <p style="color: #64748B;">تحليل تفاعلي لحركة العمليات والإيرادات والمصروفات الشهرية عبر أقسام مجموعة MH Group.</p>
                </div>
            """, unsafe_allow_html=True)
        with col_b2:
            st.markdown("""
                <div class='executive-card'>
                    <h3>⏱️ النشاط الأخير</h3>
            """, unsafe_allow_html=True)
            df_logs = safe_read_sql("SELECT action, timestamp FROM audit_logs ORDER BY id DESC LIMIT 5")
            if not df_logs.empty:
                for _, row in df_logs.iterrows():
                    st.markdown(f"<small style='color: #475569;'>• {row['action']} ({row['timestamp']})</small>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #64748B;'>جار التحميل...</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. المستخدمين ---
    elif selected_page == "👥 المستخدمين":
        st.markdown("<h1 class='main-header'>إدارة المستخدمين والصلاحيات</h1>", unsafe_allow_html=True)
        with st.form("add_user_form"):
            st.subheader("إضافة مستخدم جديد للنظام")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_usr = st.text_input("اسم المستخدم")
            with col2:
                new_pwd = st.text_input("كلمة المرور", type="password")
            with col3:
                new_role = st.selectbox("الصلاحية", ["Admin", "HR", "Finance", "RealEstate", "Investor"])
            
            col4, col5 = st.columns(2)
            with col4:
                new_phone = st.text_input("رقم الهاتف")
            with col5:
                new_email = st.text_input("البريد الإلكتروني")
                
            if st.form_submit_button("حفظ المستخدم الجديد"):
                if new_usr and new_pwd:
                    try:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO users (username, password, role, phone, email, avatar_path) VALUES (?, ?, ?, ?, ?, ?)",
                                         (new_usr, new_pwd, new_role, new_phone, new_email, ""))
                            conn.commit()
                        log_audit_action(st.session_state["username"], "المستخدمين", f"إضافة المستخدم: {new_usr}")
                        st.success("تم إضافة المستخدم بنجاح!")
                    except Exception as e:
                        st.error(fخطأ: اسم المستخدم موجود مسبقاً أو حدث خطأ تقني.)
                else:
                    st.warning("يرجى إدخال اسم المستخدم وكلمة المرور على الأقل.")
                    
        st.markdown("---")
        st.subheader("قائمة المستخدمين المسجلين")
        df_users = safe_read_sql("SELECT id, username, role, phone, email FROM users")
        st.dataframe(df_users, use_container_width=True)

    # --- 3. المعاملات المالية & الإدارة المالية ---
    elif selected_page in ["💸 المعاملات المالية", "💰 الإدارة المالية"]:
        st.markdown("<h1 class='main-header'>الإدارة والمعاملات المالية</h1>", unsafe_allow_html=True)
        
        with st.form("trans_form"):
            st.subheader("إسجال معاملة مالية جديدة")
            col1, col2, col3 = st.columns(3)
            with col1:
                t_type = st.selectbox("نوع المعاملة", ["واردات (إيرادات)", "صادرات (مصروفات)"])
            with col2:
                t_dept = st.selectbox("القسم", ["الإدارة العليا", "الموارد البشرية", "التطوير العقاري", "استثمارات"])
            with col3:
                t_amount = st.number_input("المبلغ (ج.م)", min_value=0.0, step=100.0)
            
            t_desc = st.text_area("وصف المعاملة")
            if st.form_submit_button("تسجيل المعاملة المالية"):
                if t_amount > 0:
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("INSERT INTO financial_transactions (trans_type, department, amount, description, trans_date) VALUES (?, ?, ?, ?, ?)",
                                     (t_type, t_dept, t_amount, t_desc, str(datetime.date.today())))
                        conn.commit()
                    log_audit_action(st.session_state["username"], "المالية", f"تسجيل معاملة بقيمة {t_amount}")
                    st.success("تم تسجيل المعاملة بنجاح وتحديث لوحة المؤشرات!")
                else:
                    st.warning("يرجى إدخال مبلغ صحيح.")
                    
        st.markdown("---")
        st.subheader("سجل المعاملات المالية المسجلة")
        df_t = safe_read_sql("SELECT * FROM financial_transactions ORDER BY id DESC")
        st.dataframe(df_t, use_container_width=True)

    # --- 4. الموارد البشرية ---
    elif selected_page == "👷 الموارد البشرية":
        st.markdown("<h1 class='main-header'>إدارة الموارد البشرية والرواتب</h1>", unsafe_allow_html=True)
        with st.form("hr_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                emp_name = st.text_input("اسم الموظف / الفريق")
                emp_id = st.text_input("الرقم التعريفي", f"EMP-{random.randint(100,999)}")
            with col2:
                emp_type = st.selectbox("نوع العمالة", ["يومي", "شهري", "مقاوله"])
                craft = st.text_input("التخصص / الحرفة", "عامل بناء / مهندس")
            with col3:
                daily_rate = st.number_input("الأجر اليومي / الساعي", min_value=0.0, value=300.0)
                workers_cnt = st.number_input("عدد العمال في المجموعة", min_value=1, value=1)
                
            days_worked = st.number_input("عدد الأيام أو ساعات العمل", min_value=1, value=30)
            total_pay_val = daily_rate * workers_cnt * days_worked
            
            st.info(f"إجمالي المستحق الحسابي: **{total_pay_val:,.2f} ج.م**")
            
            if st.form_submit_button("حفظ بيانات الموظفين"):
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("INSERT INTO employees (custom_id, name, emp_type, craft_type, daily_rate, workers_count, total_pay, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                 (emp_id, emp_name, emp_type, craft, daily_rate, workers_cnt, total_pay_val, str(datetime.date.today())))
                    conn.commit()
                log_audit_action(st.session_state["username"], "الموارد البشرية", f"إضافة سجل موظف/عمال: {emp_name}")
                st.success("تم حفظ سجل الموارد البشرية بنجاح!")
                
        st.subheader("قائمة سجلات الموارد البشرية والرواتب")
        df_emp = safe_read_sql("SELECT * FROM employees ORDER BY id DESC")
        st.dataframe(df_emp, use_container_width=True)

    # --- 5. العقارات ---
    elif selected_page == "🏢 العقارات":
        st.markdown("<h1 class='main-header'>إدارة الأصول والمشاريع العقارية</h1>", unsafe_allow_html=True)
        with st.form("prop_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_name = st.text_input("اسم المشروع أو العقار")
                p_id = st.text_input("كود العقار", f"PROP-{random.randint(1000,9999)}")
                p_loc = st.text_input("الموقع / العنوان")
            with col2:
                p_price = st.number_input("قيمة الشراء / التكلفة الأصلية", min_value=0.0, value=1000000.0)
                p_expenses = st.number_input("مصروفات إضافية", min_value=0.0, value=0.0)
                p_status = st.selectbox("حالة العقار", ["تحت الإنشاء", "متاح للبيع", "تم البيع بالكامل"])
                
            if st.form_submit_button("إضافة العقار للمحفظة"):
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("INSERT INTO properties (custom_id, name, location, price, expenses, status) VALUES (?, ?, ?, ?, ?, ?)",
                                 (p_id, p_name, p_loc, p_price, p_expenses, p_status))
                    conn.commit()
                log_audit_action(st.session_state["username"], "العقارات", f"إضافة عقار جديد: {p_name}")
                st.success("تمت إضافة العقار بنجاح وتحديث قيمة المحفظة باللوحة!")
                
        st.subheader("محفظة الأصول العقارية")
        df_props = safe_read_sql("SELECT * FROM properties ORDER BY id DESC")
        st.dataframe(df_props, use_container_width=True)

    # --- 6. المستثمرين ---
    elif selected_page == "🤝 المستثمرين":
        st.markdown("<h1 class='main-header'>إدارة المستثمرين وعوائد الأرباح</h1>", unsafe_allow_html=True)
        with st.form("inv_form"):
            col1, col2 = st.columns(2)
            with col1:
                inv_name = st.text_input("اسم المستثمر الكريم")
                prop_code = st.text_input("كود العقار المرتبط (اختياري)")
            with col2:
                inv_amount = st.number_input("قيمة الاستثمار (ج.م)", min_value=0.0, value=500000.0)
                return_rt = st.number_input("نسبة الأرباح المتوقعة (%)", min_value=0.0, value=15.0)
                
            tot_returns = inv_amount * (return_rt / 100.0)
            st.info(f"العائد السنوي المتوقع للمستثمر: **{tot_returns:,.2f} ج.م**")
            
            if st.form_submit_button("تسجيل المستثمر"):
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("INSERT INTO investors (name, property_custom_id, investment_amount, return_rate, total_returns, start_date) VALUES (?, ?, ?, ?, ?, ?)",
                                 (inv_name, prop_code, inv_amount, return_rt, tot_returns, str(datetime.date.today())))
                    conn.commit()
                log_audit_action(st.session_state["username"], "المستثمرين", f"تسجيل استثمار جديد لـ: {inv_name}")
                st.success("تم تسجيل المستثمر بنجاح!")
                
        st.subheader("سجل المستثمرين الحاليين")
        df_inv = safe_read_sql("SELECT * FROM investors ORDER BY id DESC")
        st.dataframe(df_inv, use_container_width=True)

    # --- 7. تقنية المعلومات ---
    elif selected_page == "💻 تقنية المعلومات":
        st.markdown("<h1 class='main-header'>قسم تقنية المعلومات والبنية التحتية</h1>", unsafe_allow_html=True)
        st.info("قسم مخصص لمتابعة وصيانة السيرفرات، صلاحيات قواعد البيانات، وحالة النظام التقني لـ MH Group.")
        
        file_it = st.file_uploader("رفع تقارير فنية أو أكواد إعدادات النظام", key="it_file")
        if file_it:
            filepath = os.path.join(UPLOAD_DIR, file_it.name)
            with open(filepath, "wb") as f:
                f.write(file_it.getbuffer())
            st.success("تم رفع الملف التقني بنجاح!")

    # --- 8. سجل العمليات ---
    elif selected_page == "⏱️ سجل العمليات":
        st.markdown("<h1 class='main-header'>سجل العمليات والرقابة (Audit Logs)</h1>", unsafe_allow_html=True)
        st.write("متابعة دقيقة لكل العمليات، عمليات تسجيل الدخول، والتعديلات التي تمت في النظام.")
        df_logs_all = safe_read_sql("SELECT * FROM audit_logs ORDER BY id DESC")
        st.dataframe(df_logs_all, use_container_width=True)

    # --- 9. الإبلاغ عن مشكلة ---
    elif selected_page == "⚠️ الإبلاغ عن مشكلة":
        st.markdown("<h1 class='main-header'>مركز الدعم الفني والإبلاغ عن الأعطال</h1>", unsafe_allow_html=True)
        with st.form("ticket_form"):
            t_dept = st.selectbox("القسم المعني بالعطل", ["الإدارة", "المالية", "الموارد البشرية", "العقارات", "تقنية المعلومات"])
            t_text = st.text_area("تفاصيل المشكلة أو طلب الدعم التقني بالتفصيل")
            if st.form_submit_button("إرسال البلاغ للإدارة العليا"):
                if t_text:
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("INSERT INTO support_tickets (username, department, issue_text, status, ticket_date) VALUES (?, ?, ?, ?, ?)",
                                     (st.session_state["username"], t_dept, t_text, "معلقة", str(datetime.date.today())))
                        conn.commit()
                    log_audit_action(st.session_state["username"], t_dept, f"بلاغ مشكلة جديد: {t_text[:30]}...")
                    st.success("تم إرسال بلاغك بنجاح وسيتعامل معه فريق الدعم فوراً!")
                else:
                    st.warning("يرجى كتابة تفاصيل المشكلة.")
                    
        st.subheader("سجل البلاغات المسجلة حالياً")
        df_tickets = safe_read_sql("SELECT * FROM support_tickets ORDER BY id DESC")
        st.dataframe(df_tickets, use_container_width=True)
