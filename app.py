import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# 1. إعدادات الصفحة والتسجيل
# ---------------------------------------------------------
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. إعداد قاعدة البيانات (Database Setup)
# ---------------------------------------------------------
DB_FILE = "mh_group.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            avatar_path TEXT,
            role TEXT NOT NULL DEFAULT 'ادمن'
        )
    """)
    
    # إضافة الحساب الرئيسي الافتراضي إذا لم يكن موجوداً
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password, full_name, role)
            VALUES ('admin', 'admin123', 'مدير النظام', 'ادمن')
        """)

    # جدول الموارد البشرية
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            type TEXT,
            worker_category TEXT,
            grade TEXT,
            work_hours REAL DEFAULT 0,
            hourly_rate REAL DEFAULT 0,
            daily_rate REAL DEFAULT 0,
            workers_count INTEGER DEFAULT 0
        )
    """)

    # جدول المالية
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            description TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول السلف
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_code TEXT NOT NULL,
            person_name TEXT,
            amount REAL NOT NULL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # جدول العقارات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prop_code TEXT UNIQUE NOT NULL,
            prop_type TEXT,
            base_price REAL DEFAULT 0,
            expenses REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            status TEXT DEFAULT 'متاح'
        )
    """)

    # جدول قسم IT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS it_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name TEXT,
            work_hours REAL DEFAULT 0,
            hourly_rate REAL DEFAULT 0
        )
    """)

    # جدول الشركاء/المستثمرين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_name TEXT,
            prop_code TEXT,
            share_percentage REAL DEFAULT 0,
            invested_amount REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. إدارة جلسة التسجيل (Authentication & Session State)
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None

# دالة إنشاء ملف PDF للأجور
def generate_payroll_pdf(df_payroll):
    pdf_filename = "payroll_report.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,
        spaceAfter=20
    )
    
    elements.append(Paragraph("MH GROUP - Payroll Report", title_style))
    elements.append(Spacer(1, 10))
    
    # تحويل البيانات إلى جدول ReportLab
    table_data = [list(df_payroll.columns)]
    for idx, row in df_payroll.iterrows():
        table_data.append([str(val) for val in row.values])
        
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e1e2f")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8f9fa")),
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]))
    
    elements.append(t)
    doc.build(elements)
    return pdf_filename

# ---------------------------------------------------------
# 4. شاشة تسجيل الدخول
# ---------------------------------------------------------
if not st.session_state['logged_in']:
    st.title("🏢 MH Group - نظام إدارة المؤسسة (ERP)")
    st.subheader("تسجيل الدخول")
    
    with st.form("login_form"):
        user_input = st.text_input("اسم المستخدم")
        pass_input = st.text_input("كلمة المرور", type="password")
        submit_btn = st.form_submit_button("دخول")
        
        if submit_btn:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?", (user_input, pass_input))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['username'] = user[1]
                st.session_state['role'] = user[2]
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
    st.stop()

# ---------------------------------------------------------
# 5. القائمة الجانبية والثيمات
# ---------------------------------------------------------
active_theme = {
    'bg': '#121212',
    'card': '#1e1e2f',
    'text': '#ffffff',
    'accent': '#64ffda'
}

with st.sidebar:
    st.title("MH Group ERP")
    st.write(f"مرحباً بك: **{st.session_state['username']}**")
    st.caption(f"الصلاحية: {st.session_state['role']}")
    st.markdown("---")
    
    menu = st.radio(
        "القائمة الرئيسية",
        [
            "اللوحة الرئيسية",
            "الملف الشخصي",
            "إدارة المستخدمين والصلاحيات",
            "رفع المستندات",
            "الموارد البشرية (HR)",
            "المالية والأجور",
            "المخزون العقاري",
            "قسم تكنولوجيا المعلومات (IT)",
            "أسهم المستثمرين"
        ]
    )
    
    st.markdown("---")
    if st.button("تسجيل الخروج"):
        st.session_state['logged_in'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = None
        st.session_state['role'] = None
        st.rerun()

# ---------------------------------------------------------
# 6. اللوحة الرئيسية (Dashboard)
# ---------------------------------------------------------
if menu == "اللوحة الرئيسية":
    st.header("📊 اللوحة الرئيسية والتحليلات")

    # جلب البيانات
    conn = get_connection()
    df_fin = pd.read_sql_query("SELECT type as 'النوع', amount as 'المبلغ', category as 'التصنيف' FROM finance", conn)
    df_prop = pd.read_sql_query("SELECT status FROM properties", conn)
    df_emp = pd.read_sql_query("SELECT COUNT(*) as count FROM hr", conn)
    conn.close()

    # بطاقات الإحصائيات Top KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_income = df_fin[df_fin['النوع'] == 'إيراد']['المبلغ'].sum() if not df_fin.empty else 0
    total_expense = df_fin[df_fin['النوع'] == 'مصروف']['المبلغ'].sum() if not df_fin.empty else 0
    emp_count = df_emp['count'].iloc[0] if not df_emp.empty else 0
    prop_count = len(df_prop) if not df_prop.empty else 0

    kpi1.metric("إجمالي الإيرادات", f"{total_income:,.0f} ج.م")
    kpi2.metric("إجمالي المصروفات", f"{total_expense:,.0f} ج.م")
    kpi3.metric("صافي الأرباح", f"{(total_income - total_expense):,.0f} ج.م")
    kpi4.metric("عدد العمالة / العقارات", f"{emp_count} / {prop_count}")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("الرسم البياني للمالية (إيرادات ومصروفات)")
        if not df_fin.empty:
            fig1 = px.bar(
                df_fin,
                x='التصنيف',
                y='المبلغ',
                color='النوع',
                barmode='group',
                color_discrete_map={'إيراد': '#64ffda', 'مصروف': '#ff007f'}
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=active_theme['text']
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("لا توجد بيانات مالية للعرض حالياً.")

    with col_chart2:
        st.subheader("حالة العقارات بالمخزون")
        if not df_prop.empty:
            fig2 = px.histogram(
                df_prop,
                x='status',
                color='status',
                color_discrete_sequence=['#d4af37', '#64ffda', '#ff007f']
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=active_theme['text'],
                xaxis_title="الحالة",
                yaxis_title="العدد"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("لا توجد بيانات عقارية للعرض حالياً.")

# ---------------------------------------------------------
# 7. الملف الشخصي (Profile)
# ---------------------------------------------------------
elif menu == "الملف الشخصي":
    st.header("👤 الملف الشخصي وإعدادات الحساب")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, email, phone, avatar_path, role FROM users WHERE id = ?", (st.session_state['user_id'],))
    user_info = cursor.fetchone()
    conn.close()

    if user_info:
        col_avatar, col_details = st.columns([1, 2])
        with col_avatar:
            if user_info[4] and os.path.exists(user_info[4]):
                st.image(user_info[4], width=180, caption="الصورة الشخصية")
            else:
                st.info("لم يتم رفع صورة شخصية بعد.")

            uploaded_avatar = st.file_uploader("تغيير الصورة الشخصية", type=["jpg", "jpeg", "png"], key="profile_avatar_upload")
            if uploaded_avatar:
                os.makedirs("avatars", exist_ok=True)
                avatar_path = os.path.join("avatars", f"user_{st.session_state['user_id']}.png")
                with open(avatar_path, "wb") as f:
                    f.write(uploaded_avatar.getbuffer())

                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET avatar_path = ? WHERE id = ?", (avatar_path, st.session_state['user_id']))
                conn.commit()
                conn.close()
                st.success("تم تحديث الصورة الشخصية بنجاح!")
                st.rerun()

        with col_details:
            st.subheader("البيانات الشخصية")
            new_full_name = st.text_input("الاسم بالكامل", value=user_info[1] or "")
            new_email = st.text_input("البريد الإلكتروني", value=user_info[2] or "")
            new_phone = st.text_input("رقم الهاتف", value=user_info[3] or "")
            st.text_input("اسم المستخدم", value=user_info[0], disabled=True)
            st.text_input("الصلاحية", value=user_info[5], disabled=True)

            if st.button("حفظ التعديلات", key="save_profile_info"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET full_name = ?, email = ?, phone = ? 
                    WHERE id = ?
                """, (new_full_name, new_email, new_phone, st.session_state['user_id']))
                conn.commit()
                conn.close()
                st.success("تم تحديث البيانات بنجاح!")
                st.rerun()

        st.markdown("---")
        st.subheader("تغيير كلمة المرور")
        c1, c2 = st.columns(2)
        with c1:
            old_pass = st.text_input("كلمة المرور الحالية", type="password", key="old_pass")
            new_pass = st.text_input("كلمة المرور الجديدة", type="password", key="new_pass")
            confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة", type="password", key="confirm_pass")

            if st.button("تحديث كلمة المرور", key="change_pass_btn"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM users WHERE id = ?", (st.session_state['user_id'],))
                current_db_pass = cursor.fetchone()[0]

                if old_pass != current_db_pass:
                    st.error("كلمة المرور الحالية غير صحيحة!")
                elif new_pass != confirm_pass:
                    st.error("كلمتا المرور الجديدتان غير متطابقتين!")
                elif not new_pass:
                    st.error("يرجى إدخال كلمة مرور جديدة صحيحة!")
                else:
                    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_pass, st.session_state['user_id']))
                    conn.commit()
                    st.success("تم تغيير كلمة المرور بنجاح!")
                conn.close()

# ---------------------------------------------------------
# 8. إدارة المستخدمين والصلاحيات (Admin Only)
# ---------------------------------------------------------
elif menu == "إدارة المستخدمين والصلاحيات":
    st.header("👥 إدارة المستخدمين وصلاحيات النظام")

    tab_users, tab_add_user = st.tabs(["قائمة المستخدمين", "إضافة مستخدم جديد"])

    with tab_users:
        conn = get_connection()
        df_users = pd.read_sql_query("SELECT id, username, full_name, email, phone, role FROM users", conn)
        conn.close()

        st.dataframe(df_users, use_container_width=True)

        st.markdown("---")
        st.subheader("تعديل صلاحية أو حذف مستخدم")
        col_u1, col_u2, col_u3 = st.columns(3)

        user_list = df_users['username'].tolist()
        with col_u1:
            selected_user = st.selectbox("اختر المستخدم:", user_list, key="select_user_to_edit")
        
        with col_u2:
            new_role = st.selectbox("الصلاحية الجديدة:", ["ادمن", "HR", "محاسب", "IT", "عقارات", "مطور"], key="select_new_role")

        with col_u3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("تحديث الصلاحية", key="update_role_btn"):
                if selected_user == "admin":
                    st.error("لا يمكن تعديل صلاحية الحساب الرئيسي (admin)!")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, selected_user))
                    conn.commit()
                    conn.close()
                    st.success(f"تم تحديث صلاحية {selected_user} إلى {new_role} بنجاح!")
                    st.rerun()

        if st.button("❌ حذف المستخدم المحدد", key="delete_user_btn"):
            if selected_user == "admin":
                st.error("لا يمكن حذف الحساب الرئيسي (admin)!")
            else:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (selected_user,))
                conn.commit()
                conn.close()
                st.success(f"تم حذف المستخدم {selected_user} بنجاح!")
                st.rerun()

    with tab_add_user:
        st.subheader("إضافة حساب جديد")
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("اسم المستخدم (Username)", key="add_u_username")
            new_password = st.text_input("كلمة المرور", type="password", key="add_u_password")
            new_fullname = st.text_input("الاسم بالكامل", key="add_u_fullname")
        with c2:
            new_u_email = st.text_input("البريد الإلكتروني", key="add_u_email")
            new_u_phone = st.text_input("رقم الهاتف", key="add_u_phone")
            new_u_role = st.selectbox("الصلاحية", ["ادمن", "HR", "محاسب", "IT", "عقارات", "مطور"], key="add_u_role")

        if st.button("إنشاء الحساب", key="create_user_submit"):
            if not new_username or not new_password:
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور على الأقل!")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO users (username, password, full_name, email, phone, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_username, new_password, new_fullname, new_u_email, new_u_phone, new_u_role))
                    conn.commit()
                    conn.close()
                    st.success(f"تم إضافة المستخدم {new_username} بنجاح!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("اسم المستخدم موجود بالفعل! يرجى اختيار اسم مستخدم آخر.")

# ---------------------------------------------------------
# 9. رفع المستندات (Document Upload Center)
# ---------------------------------------------------------
elif menu == "رفع المستندات":
    st.header("📁 مركز رفع وإدارة المستندات والأوراق الرسمية")

    DOCS_DIR = "uploaded_documents"
    os.makedirs(DOCS_DIR, exist_ok=True)

    tab_upload, tab_view = st.tabs(["رفع مستند جديد", "استعراض المستندات"])

    with tab_upload:
        st.subheader("تحميل مستند للأنظمة")
        doc_category = st.selectbox("تصنيف المستند:", ["عقود عقارية", "فواتير ومستندات مالية", "أوراق موظفين (HR)", "سجلات ومعاملات عامة"], key="doc_cat")
        doc_title = st.text_input("عنوان / وصف المستند", key="doc_title")
        uploaded_file = st.file_uploader("اختر الملف (PDF, PNG, JPG, XLSX, DOCX)", type=["pdf", "png", "jpg", "jpeg", "xlsx", "docx"], key="doc_file")

        if st.button("حفظ المستند", key="save_doc_btn"):
            if uploaded_file and doc_title:
                file_ext = uploaded_file.name.split(".")[-1]
                saved_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{doc_title.replace(' ', '_')}.{file_ext}"
                file_path = os.path.join(DOCS_DIR, saved_filename)

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.success(f"تم رفع المستند '{doc_title}' بنجاح في قسم [{doc_category}]!")
            else:
                st.error("يرجى رفع ملف وإدخال عنوان المستند أولاً.")

    with tab_view:
        st.subheader("المستندات المحفوظة بالنظام")
        files = os.listdir(DOCS_DIR)
        if files:
            for file in files:
                f_path = os.path.join(DOCS_DIR, file)
                c_f1, c_f2, c_f3 = st.columns([3, 1, 1])
                with c_f1:
                    st.markdown(f"📄 **{file}**")
                with c_f2:
                    with open(f_path, "rb") as f:
                        st.download_button("تحميل", data=f.read(), file_name=file, key=f"dl_{file}")
                with c_f3:
                    if st.button("حذف", key=f"del_{file}"):
                        os.remove(f_path)
                        st.success(f"تم حذف {file}")
                        st.rerun()
        else:
            st.info("لا توجد مستندات مرفوعة حالياً.")

# ---------------------------------------------------------
# 10. الموارد البشرية (HR)
# ---------------------------------------------------------
elif menu == "الموارد البشرية (HR)":
    st.header("👷 قسم الموارد البشرية وإدارة العمالة")

    tab_hr_list, tab_add_emp = st.tabs(["سجل العمالة والموظفين", "إضافة موظف / مقاول"])

    with tab_hr_list:
        conn = get_connection()
        df_hr = pd.read_sql_query("SELECT id, emp_code as 'الكود الوظيفي', name as 'الاسم', type as 'الصفة', worker_category as 'نوع العامل', grade as 'الدرجة', work_hours as 'ساعات العمل', hourly_rate as 'أجر الساعة', daily_rate as 'اليومية', workers_count as 'عدد العمال المتابعين' FROM hr", conn)
        conn.close()

        st.dataframe(df_hr, use_container_width=True)

        st.markdown("---")
        st.subheader("إدارة السجلات")
        if not df_hr.empty:
            emp_codes = df_hr['الكود الوظيفي'].dropna().tolist()
            selected_emp_code = st.selectbox("اختر الكود الوظيفي للحذف:", emp_codes, key="select_emp_del")
            if st.button("❌ حذف السجل المحدد", key="del_emp_btn"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM hr WHERE emp_code = ?", (selected_emp_code,))
                conn.commit()
                conn.close()
                st.success("تم حذف السجل بنجاح!")
                st.rerun()

    with tab_add_emp:
        st.subheader("تسجيل فرد / مقاول جديد")
        c1, c2 = st.columns(2)
        with c1:
            emp_code = st.text_input("الكود الوظيفي", value=f"EMP-{datetime.datetime.now().strftime('%M%S')}", key="hr_code")
            emp_name = st.text_input("الاسم بالكامل", key="hr_name")
            emp_type = st.selectbox("الصفة", ["موظف دائم", "عامل باليومية", "مقاول صنايعية"], key="hr_type")
            worker_cat = st.selectbox("نوع العامل / التخصص", ["إداري", "مهندس", "صنايعي (محارة/مباني)", "عامل عادي", "مشرف موقع"], key="hr_cat")
        with c2:
            emp_grade = st.selectbox("الدرجة / المستوى", ["A", "B", "C"], key="hr_grade")
            daily_rate = st.number_input("اليومية / الأجر اليومي (ج.م)", min_value=0.0, step=50.0, key="hr_daily")
            hourly_rate = st.number_input("أجر الساعة (إن وجد)", min_value=0.0, step=10.0, key="hr_hourly")
            workers_cnt = st.number_input("عدد العمال التابعين (للمقاولين)", min_value=0, step=1, key="hr_w_cnt")

        if st.button("تسجيل البيانات", key="save_hr_btn"):
            if not emp_name:
                st.error("يرجى إدخال الاسم!")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO hr (emp_code, name, type, worker_category, grade, daily_rate, hourly_rate, workers_count, work_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (emp_code, emp_name, emp_type, worker_cat, emp_grade, daily_rate, hourly_rate, workers_cnt))
                    conn.commit()
                    conn.close()
                    st.success(f"تم تسجيل {emp_name} بنجاح!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("الكود الوظيفي مكرر!")

# ---------------------------------------------------------
# 11. المالية والأجور
# ---------------------------------------------------------
elif menu == "المالية والأجور":
    st.header("💰 الإدارة المالية وحسابات الأجور والسلف")

    tab_payroll, tab_finance_logs, tab_advances = st.tabs(["مسودات والأجور الشهري/الأسسبوعي", "سجل المعاملات المالية (إيرادات ومصروفات)", "إدارة السلف"])

    with tab_payroll:
        st.subheader("جدول مسحوبات وأجور الموظفين والعمال")

        conn = get_connection()
        df_hr = pd.read_sql_query("SELECT emp_code, name, type, daily_rate, hourly_rate, work_hours FROM hr", conn)
        df_advances = pd.read_sql_query("SELECT emp_code, SUM(amount) as total_adv FROM advances GROUP BY emp_code", conn)
        conn.close()

        if not df_hr.empty:
            df_merged = pd.merge(df_hr, df_advances, on="emp_code", how="left")
            df_merged['total_adv'] = df_merged['total_adv'].fillna(0)

            # حساب المستحق الصافي (اليومية * أيام العمل المفترضة - السلف)
            df_merged['أيام العمل'] = 26  # قيمة افتراضية قابلة للحساب
            df_merged['إجمالي الاستحقاق'] = df_merged['daily_rate'] * df_merged['أيام العمل']
            df_merged['الصافي المستحق'] = df_merged['إجمالي الاستحقاق'] - df_merged['total_adv']

            df_merged.rename(columns={
                'emp_code': 'الكود الوظيفي',
                'name': 'اسم الموظف/المورد',
                'type': 'نوع العامل',
                'daily_rate': 'اليومية',
                'total_adv': 'إجمالي السلف'
            }, inplace=True)

            st.dataframe(df_merged[['الكود الوظيفي', 'اسم الموظف/المورد', 'نوع العامل', 'اليومية', 'أيام العمل', 'إجمالي الاستحقاق', 'إجمالي السلف', 'الصافي المستحق']], use_container_width=True)

            if st.button("🖨️ طباعة وتصدير كشف الأجور (PDF)", key="gen_pdf_btn"):
                pdf_path = generate_payroll_pdf(df_merged)
                with open(pdf_path, "rb") as f:
                    st.download_button("تحميل ملف PDF", data=f.read(), file_name="MH_GROUP_Payroll.pdf", mime="application/pdf", key="dl_pdf_btn")
        else:
            st.info("لا توجد بيانات عمالة لحساب الأجور.")

    with tab_finance_logs:
        st.subheader("إضافة معاملة مالية جديدة")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            trans_type = st.selectbox("نوع المعاملة", ["مصروف", "إيراد"], key="fin_type")
            trans_amount = st.number_input("المبلغ (ج.م)", min_value=0.0, step=100.0, key="fin_amount")
        with col_f2:
            trans_cat = st.selectbox("التصنيف", ["خامات ومواد بناء", "أجور وعمالة", "مشتريات عقارية", "مبيعات وحدات", "نثريات ومرافق"], key="fin_cat")
            trans_desc = st.text_input("البيان / الوصف", key="fin_desc")

        if st.button("تسجيل المعاملة المالية", key="save_fin_btn"):
            if trans_amount > 0:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO finance (type, amount, category, description)
                    VALUES (?, ?, ?, ?)
                """, (trans_type, trans_amount, trans_cat, trans_desc))
                conn.commit()
                conn.close()
                st.success("تم تسجيل المعاملة المالية بنجاح!")
                st.rerun()
            else:
                st.error("يرجى إدخال مبلغ صحيح!")

        st.markdown("---")
        st.subheader("سجل الخزينة والتدفقات")
        conn = get_connection()
        df_fin = pd.read_sql_query("SELECT id, type as 'النوع', amount as 'المبلغ', category as 'التصنيف', description as 'البيان' FROM finance", conn)
        conn.close()
        st.dataframe(df_fin, use_container_width=True)

    with tab_advances:
        st.subheader("تسجيل سلفة موظف / عامل")
        conn = get_connection()
        df_hr_nodes = pd.read_sql_query("SELECT emp_code, name FROM hr", conn)
        conn.close()

        if not df_hr_nodes.empty:
            emp_options = {f"{row['name']} ({row['emp_code']})": row['emp_code'] for _, row in df_hr_nodes.iterrows()}
            selected_emp_label = st.selectbox("اختر الموظف:", list(emp_options.keys()), key="adv_emp_select")
            adv_amount = st.number_input("مبلغ السلفة (ج.م)", min_value=0.0, step=50.0, key="adv_amt")

            if st.button("تسجيل السلفة", key="save_adv_btn"):
                if adv_amount > 0:
                    emp_code_val = emp_options[selected_emp_label]
                    person_name_val = selected_emp_label.split(" (")[0]
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO advances (emp_code, person_name, amount)
                        VALUES (?, ?, ?)
                    """, (emp_code_val, person_name_val, adv_amount))
                    conn.commit()
                    conn.close()
                    st.success(f"تم تسجيل سلفة بقيمة {adv_amount} ج.م بنجاح!")
                    st.rerun()
        else:
            st.info("يرجى إضافة عمالة أولاً في قسم الـ HR لتتمكن من إضافة سلف.")

        st.markdown("---")
        conn = get_connection()
        df_adv_list = pd.read_sql_query("SELECT id, emp_code as 'كود الموظف', person_name as 'الاسم', amount as 'مبلغ السلفة', date_added as 'تاريخ التسجيل' FROM advances", conn)
        conn.close()
        st.dataframe(df_adv_list, use_container_width=True)

# ---------------------------------------------------------
# 12. المخزون العقاري
# ---------------------------------------------------------
elif menu == "المخزون العقاري":
    st.header("🏠 إدارة المخزون العقاري والوحدات")

    tab_props, tab_add_prop = st.tabs(["قائمة العقارات والوحدات", "إضافة وحدة جديدة"])

    with tab_props:
        conn = get_connection()
        df_prop = pd.read_sql_query("SELECT id, prop_code as 'كود العقار', prop_type as 'النوع', base_price as 'السعر الأساسي', expenses as 'المصروفات', total_price as 'التكلفة الإجمالية', selling_price as 'سعر البيع', status as 'الحالة' FROM properties", conn)
        conn.close()

        st.dataframe(df_prop, use_container_width=True)

    with tab_add_prop:
        st.subheader("إضافة وحدة عقارية جديدة")
        c1, c2 = st.columns(2)
        with c1:
            p_code = st.text_input("كود الوحدة / العقار", value=f"PROP-{datetime.datetime.now().strftime('%d%H%M')}", key="p_code")
            p_type = st.selectbox("نوع العقار", ["شقة سكنية", "فيلا", "محل تجاري", "مكتب إداري", "أرض بناء"], key="p_type")
            p_base = st.number_input("سعر الشراء / الأساسي (ج.م)", min_value=0.0, step=10000.0, key="p_base")
        with c2:
            p_exp = st.number_input("التراخيص والمصروفات (ج.م)", min_value=0.0, step=1000.0, key="p_exp")
            p_sell = st.number_input("سعر البيع المستهدف (ج.م)", min_value=0.0, step=10000.0, key="p_sell")
            p_status = st.selectbox("حالة العقار", ["متاح", "تم البيع", "قيد التشطيب"], key="p_status")

        p_total = p_base + p_exp

        if st.button("حفظ العقار بالمخزون", key="save_prop_btn"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO properties (prop_code, prop_type, base_price, expenses, total_price, selling_price, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (p_code, p_type, p_base, p_exp, p_total, p_sell, p_status))
                conn.commit()
                conn.close()
                st.success(f"تم إضافة العقار {p_code} بنجاح!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("كود العقار مكرر!")

# ---------------------------------------------------------
# 13. قسم تكنولوجيا المعلومات (IT)
# ---------------------------------------------------------
elif menu == "قسم تكنولوجيا المعلومات (IT)":
    st.header("💻 قسم تكنولوجيا المعلومات والتطوير")

    st.info("سجلات أعمال وتطوير البرمجيات بالشركة.")

    c1, c2 = st.columns(2)
    with c1:
        it_name = st.text_input("اسم المهندس / المطور", key="it_name")
        it_hours = st.number_input("ساعات العمل", min_value=0.0, step=1.0, key="it_hours")
    with c2:
        it_rate = st.number_input("أجر الساعة (ج.م)", min_value=0.0, step=50.0, key="it_rate")

    if st.button("تسجيل ساعات التطوير", key="save_it_btn"):
        if it_name and it_hours > 0:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO it_logs (emp_name, work_hours, hourly_rate)
                VALUES (?, ?, ?)
            """, (it_name, it_hours, it_rate))
            conn.commit()
            conn.close()
            st.success("تم تسجيل بيانات قسم الـ IT بنجاح!")
            st.rerun()

    st.markdown("---")
    conn = get_connection()
    df_it = pd.read_sql_query("SELECT id, emp_name as 'المهندس', work_hours as 'ساعات العمل', hourly_rate as 'أجر الساعة', (work_hours * hourly_rate) as 'الإجمالي' FROM it_logs", conn)
    conn.close()
    st.dataframe(df_it, use_container_width=True)

# ---------------------------------------------------------
# 14. أسهم المستثمرين
# ---------------------------------------------------------
elif menu == "أسهم المستثمرين":
    st.header("🤝 إدارة الشركاء وأسهم المستثمرين")

    tab_inv_list, tab_add_inv = st.tabs(["قائمة أسهم المستثمرين", "إضافة مستثمر لشراكة"])

    with tab_inv_list:
        conn = get_connection()
        df_inv = pd.read_sql_query("SELECT id, investor_name as 'اسم المستثمر', prop_code as 'كود العقار', share_percentage as 'نسبة الشراكة %', invested_amount as 'المبلغ المستثمر' FROM investors", conn)
        conn.close()

        st.dataframe(df_inv, use_container_width=True)

    with tab_add_inv:
        conn = get_connection()
        df_p = pd.read_sql_query("SELECT prop_code FROM properties", conn)
        conn.close()

        if not df_p.empty:
            inv_name = st.text_input("اسم المستثمر / الشريك", key="inv_name")
            p_select = st.selectbox("اختر العقار الشريك فيه:", df_p['prop_code'].tolist(), key="inv_p_select")
            inv_share = st.number_input("نسبة الشراكة (%)", min_value=0.0, max_value=100.0, step=1.0, key="inv_share")
            inv_amount = st.number_input("المبلغ المدفوع (ج.م)", min_value=0.0, step=10000.0, key="inv_amt")

            if st.button("تسجيل حصة الشريك", key="save_inv_btn"):
                if inv_name and inv_amount > 0:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO investors (investor_name, prop_code, share_percentage, invested_amount)
                        VALUES (?, ?, ?, ?)
                    """, (inv_name, p_select, inv_share, inv_amount))
                    conn.commit()
                    conn.close()
                    st.success(f"تم تسجيل حصة الشريك {inv_name} بنجاح!")
                    st.rerun()
        else:
            st.info("يرجى إدخال عقارات بالمخزون العقاري أولاً لربط المستثمرين بها.")
