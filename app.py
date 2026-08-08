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
# 1. إعدادات الصفحة وإدارة الثيمات (Theme Engine)
# ---------------------------------------------------------
st.set_page_config(
    page_title="MH GROUP ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# حفظ الثيم المختار في الجلسة
if 'current_theme' not in st.session_state:
    st.session_state['current_theme'] = 'Executive Dark Gold'

# تعريف لوحات الألوان للثيمات المختلفة
THEMES = {
    'Executive Dark Gold': {
        'bg': '#0d1117', 'sidebar': '#161b22', 'border': '#30363d',
        'text': '#f0f6fc', 'primary': '#d4af37', 'accent': '#ffd700',
        'card_bg': 'linear-gradient(145deg, #161b22 0%, #1f242d 100%)',
        'btn_bg': 'linear-gradient(135deg, #d4af37 0%, #aa7c11 100%)'
    },
    'Midnight Navy': {
        'bg': '#0a192f', 'sidebar': '#112240', 'border': '#233554',
        'text': '#e6f1ff', 'primary': '#64ffda', 'accent': '#00f2fe',
        'card_bg': 'linear-gradient(145deg, #112240 0%, #1d3557 100%)',
        'btn_bg': 'linear-gradient(135deg, #00b4db 0%, #0083b0 100%)'
    },
    'Emerald Obsidian': {
        'bg': '#061a14', 'sidebar': '#0d281e', 'border': '#1b4332',
        'text': '#e8f5e9', 'primary': '#2ecc71', 'accent': '#52b788',
        'card_bg': 'linear-gradient(145deg, #0d281e 0%, #1b4332 100%)',
        'btn_bg': 'linear-gradient(135deg, #2ecc71 0%, #15803d 100%)'
    },
    'Cyberpunk Neon': {
        'bg': '#0f051d', 'sidebar': '#1e0836', 'border': '#3d1263',
        'text': '#f3e8ff', 'primary': '#ff007f', 'accent': '#00f0ff',
        'card_bg': 'linear-gradient(145deg, #1e0836 0%, #2a085c 100%)',
        'btn_bg': 'linear-gradient(135deg, #ff007f 0%, #7928ca 100%)'
    },
    'Corporate Light': {
        'bg': '#f8f9fa', 'sidebar': '#ffffff', 'border': '#dee2e6',
        'text': '#212529', 'primary': '#1b365d', 'accent': '#0b5ed7',
        'card_bg': 'linear-gradient(145deg, #ffffff 0%, #f1f3f5 100%)',
        'btn_bg': 'linear-gradient(135deg, #1b365d 0%, #0d6efd 100%)'
    }
}

active_theme = THEMES.get(st.session_state['current_theme'], THEMES['Executive Dark Gold'])

# كود التنسيق الشامل + حجب تلميحات الاختصارات والدبل عند مرور الماوس
st.markdown(f"""
    <style>
    /* إلغاء حوادث التولتيب تماماً وحظر أي تلميحات تفاعلية للـ Hover */
    [data-baseweb="tooltip"], div[role="tooltip"], .stTooltipIcon, [data-testid="stSidebar"] [title] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    /* إخفاء نصوص إرشادات الكيبورد الدبل عند الحركة فوق الخيارات */
    div[data-testid="stRadio"] label span small, 
    div[data-testid="stRadio"] label ::after {{
        display: none !important;
    }}

    /* 1. إجبار خلفية التطبيق الأساسية */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {active_theme['bg']} !important;
        color: {active_theme['text']} !important;
    }}
    
    /* 2. ضبط القائمة الجانبية */
    [data-testid="stSidebar"] {{
        background-color: {active_theme['sidebar']} !important;
        border-right: 1px solid {active_theme['border']} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {active_theme['text']} !important;
    }}
    [data-testid="stSidebar"] .stRadio label {{
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }}

    /* 3. العناوين والنصوص */
    h1, h2, h3, h4, h5, h6, label, p, span {{
        color: {active_theme['text']} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    h1 {{ color: {active_theme['primary']} !important; font-size: 2.2rem !important; font-weight: 700; }}
    h2 {{ color: {active_theme['primary']} !important; font-size: 1.6rem !important; border-bottom: 2px solid {active_theme['border']}; padding-bottom: 8px; margin-top: 15px; }}
    h3 {{ font-size: 1.25rem !important; color: {active_theme['text']} !important; }}

    /* 4. كروت المؤشرات المخصصة */
    .kpi-card {{
        background: {active_theme['card_bg']};
        border: 1px solid {active_theme['border']};
        border-top: 3px solid {active_theme['primary']};
        border-radius: 12px;
        padding: 20px 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
    }}
    .kpi-title {{
        color: {active_theme['text']} !important;
        opacity: 0.8;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
        display: block;
    }}
    .kpi-value {{
        color: {active_theme['accent']} !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }}

    /* 5. تصميم أزرار النظام */
    .stButton>button {{
        background: {active_theme['btn_bg']} !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
    }}
    .stButton>button:hover {{
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5) !important;
        transform: translateY(-1px);
    }}

    /* 6. توحيد الحقول والمدخلات والجداول */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: {active_theme['sidebar']} !important;
        color: {active_theme['text']} !important;
        border: 1px solid {active_theme['border']} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stDataFrame"] {{
        background-color: {active_theme['sidebar']} !important;
        border: 1px solid {active_theme['border']} !important;
        border-radius: 10px !important;
    }}
    
    .js-plotly-plot .plotly, .plot-container {{
        background-color: transparent !important;
    }}
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            category TEXT,
            description TEXT
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS it_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_name TEXT,
            work_hours REAL,
            hourly_rate REAL
        )
    ''')

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
if 'username' not in st.session_state:
    st.session_state['username'] = None

query_params = st.query_params
if "session" in query_params and not st.session_state['logged_in']:
    session_token = query_params["session"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT u.id, u.role, u.username FROM active_sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ?", (session_token,))
    sess_data = cursor.fetchone()
    conn.close()
    
    if sess_data:
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = sess_data[0]
        st.session_state['user_role'] = sess_data[1]
        st.session_state['username'] = sess_data[2]

def login():
    st.markdown("<h1 style='text-align: center; color: #d4af37; margin-top: 50px;'>MH GROUP للاستثمار والتطوير العقاري</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; opacity: 0.8;'>نظام إدارة الموارد المؤسسية ERP</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        username_input = st.text_input("اسم المستخدم", key="login_username")
        password_input = st.text_input("كلمة المرور", type="password", key="login_password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("تسجيل الدخول", use_container_width=True, key="login_btn"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, role, username FROM users WHERE username = ? AND password = ?", (username_input, password_input))
            user = cursor.fetchone()
            
            if user:
                token = str(uuid.uuid4())
                cursor.execute("INSERT INTO active_sessions (token, user_id, role) VALUES (?, ?, ?)", (token, user[0], user[1]))
                conn.commit()
                conn.close()
                
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user[0]
                st.session_state['user_role'] = user[1]
                st.session_state['username'] = user[2]
                
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
cursor.execute("SELECT full_name, avatar_path, role, username FROM users WHERE id = ?", (st.session_state['user_id'],))
current_user = cursor.fetchone()
conn.close()

# تأكيد تحديث متغيرات الجلسة من القاعدة مباشرة
if current_user:
    st.session_state['user_role'] = current_user[2]
    st.session_state['username'] = current_user[3]

st.sidebar.title("MH GROUP ERP")
if current_user:
    if current_user[1] and os.path.exists(current_user[1]):
        st.sidebar.image(current_user[1], width=90)
    st.sidebar.markdown(f"**أهلاً بك، {current_user[0]}**")
    st.sidebar.caption(f"الصلاحية: `{current_user[2]}`")

st.sidebar.markdown("---")

user_role = st.session_state.get('user_role', '')
username = st.session_state.get('username', '')

allowed_menu = ["الملف الشخصي"]

if user_role == "ادمن" or username == "admin":
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

# ضمان إظهار خيار الثيمات للمطور/الآدمن بشكل صريح ومباشر
if user_role in ["ادمن", "مطور"] or username == "admin":
    allowed_menu.append("🎨 إعدادات الثيمات (خاص بالمطور)")

menu = st.sidebar.radio("الأقسام المتاحة:", allowed_menu, key="main_sidebar_menu_radio")

st.sidebar.markdown("---")
if st.sidebar.button("تسجيل الخروج", key="logout_btn", use_container_width=True):
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
    st.session_state['username'] = None
    st.rerun()

# ---------------------------------------------------------
# 5. قسم تخصيص الثيمات (خاص بالمطورين)
# ---------------------------------------------------------
if menu == "🎨 إعدادات الثيمات (خاص بالمطور)":
    st.header("🛠️ مركز تخصيص الثيمات والمظهر (خاص بالمطور)")
    st.info("قم باختيار الثيم المناسب، وسوف تتحدث ألوان النظام فوراً على كل الأجزاء والكروت والجداول.")
    
    st.subheader("اختر ثيم الواجهة:")
    selected_theme = st.selectbox(
        "الثيمات المتاحة:",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state['current_theme'])
    )
    
    if st.button("تطبيق الثيم فوراً"):
        st.session_state['current_theme'] = selected_theme
        st.success(f"تم تطبيق ثيم '{selected_theme}' بنجاح!")
        st.rerun()

# ---------------------------------------------------------
# 6. Dashboard (اللوحة الرئيسية الاحترافية)
# ---------------------------------------------------------
elif menu == "الرئيسية (Dashboard)":
    st.header("لوحة التحكم والأداء العام")
    
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
    with c1:
        st.markdown(f"""
            <div class="kpi-card">
                <span class="kpi-title">إجمالي الإيرادات</span>
                <h3 class="kpi-value">{total_rev:,.2f} ج.م</h3>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="kpi-card">
                <span class="kpi-title">إجمالي المصروفات</span>
                <h3 class="kpi-value">{total_exp:,.2f} ج.م</h3>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="kpi-card">
                <span class="kpi-title">صافي الأرباح</span>
                <h3 class="kpi-value">{net_profit:,.2f} ج.م</h3>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="kpi-card">
                <span class="kpi-title">العقارات / القوة البشرية</span>
                <h3 class="kpi-value">{total_props} عقار / {total_employees} فرد</h3>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("توزيع التدفقات المالية")
        if not df_fin.empty:
            fig1 = px.pie(
                df_fin, 
                values='amount', 
                names='type', 
                hole=0.5, 
                color_discrete_sequence=['#d4af37', '#e74c3c']
            )
            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font=dict(color=active_theme['text']),
                legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("لا توجد بيانات مالية مسجلة بعد.")
            
    with col_chart2:
        st.subheader("حالة المخزون العقاري")
        if not df_prop.empty:
            fig2 = px.pie(
                df_prop, 
                names='status', 
                hole=0.5, 
                color_discrete_sequence=['#2ecc71', '#f39c12']
            )
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font=dict(color=active_theme['text']),
                legend=dict(orientation="h", y=-0.1)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("لا توجد عقارات مسجلة بالمخزون بعد.")

# ---------------------------------------------------------
# 7. قسم الموارد البشرية (HR)
# ---------------------------------------------------------
elif menu == "الموارد البشرية (HR)":
    st.header("قسم الموارد البشرية والعمالة")
    
    tab1, tab2, tab3 = st.tabs(["إضافة جديد", "عرض وحذف السجلات", "تعديل بيانات"])
    
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
            st.subheader("حذف سجل من HR")
            hr_to_delete = st.selectbox("اختر السجل المراد حذفه (ID)", df_hr['id'].tolist(), key="hr_del_select")
            if st.button("حذف السجل المحدد", key="hr_del_btn"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM hr WHERE id = ?", (hr_to_delete,))
                conn.commit()
                conn.close()
                st.success("تم حذف السجل بنجاح!")
                st.rerun()
        conn.close()

    with tab3:
        conn = get_connection()
        df_hr_edit = pd.read_sql_query("SELECT * FROM hr", conn)
        conn.close()
        
        if not df_hr_edit.empty:
            emp_to_edit = st.selectbox("اختر السجل للتعديل", df_hr_edit['emp_code'].tolist())
            selected_row = df_hr_edit[df_hr_edit['emp_code'] == emp_to_edit].iloc[0]
            
            with st.form("edit_hr_form"):
                e_name = st.text_input("الاسم", value=selected_row['name'])
                e_type = st.selectbox("النوع", ["موظف", "مورد", "عامل عادية"], index=["موظف", "مورد", "عامل عادية"].index(selected_row['type']) if selected_row['type'] in ["موظف", "مورد", "عامل عادية"] else 0)
                e_daily = st.number_input("اليومية", value=float(selected_row['daily_rate'] or 0.0))
                
                if st.form_submit_button("تحديث البيانات"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE hr SET name = ?, type = ?, daily_rate = ? WHERE emp_code = ?", (e_name, e_type, e_daily, emp_to_edit))
                    conn.commit()
                    conn.close()
                    st.success("تم تحديث البيانات!")
                    st.rerun()
