import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import datetime
import uuid

# ---------------------------------------------------------
# 0. مكتبة إنشاء ملفات PDF
# ---------------------------------------------------------
try:
    from fpdf import FPDF
except ImportError:
    st.error("يرجى تثبيت مكتبة fpdf2 عبر الأمر: pip install fpdf2")

# ---------------------------------------------------------
# 1. إعدادات الصفحة وتهيئة محرك الثيمات (Theme Engine)
# ---------------------------------------------------------
st.set_page_config(
    page_title="MH GROUP ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تعيين الثيم الافتراضي في الجلسة
if 'app_theme' not in st.session_state:
    st.session_state['app_theme'] = "Dark Executive"

# قاموس الألوان والتصاميم المتاحة للمطور
THEMES_CONFIG = {
    "Dark Executive": {
        "bg": "#0d1117",
        "card_bg": "linear-gradient(145deg, #161b22 0%, #1f242d 100%)",
        "sidebar_bg": "#161b22",
        "text": "#f0f6fc",
        "accent": "#d4af37",
        "accent_hover": "#ffd700",
        "border": "#30363d",
        "kpi_val": "#ffd700"
    },
    "Golden Luxury": {
        "bg": "#120f0a",
        "card_bg": "linear-gradient(145deg, #1c1710 0%, #2a2218 100%)",
        "sidebar_bg": "#1a150e",
        "text": "#f7f3e9",
        "accent": "#f59e0b",
        "accent_hover": "#fbbf24",
        "border": "#42321c",
        "kpi_val": "#fbbf24"
    },
    "Light Professional": {
        "bg": "#f8fafc",
        "card_bg": "linear-gradient(145deg, #ffffff 0%, #f1f5f9 100%)",
        "sidebar_bg": "#1e293b",
        "text": "#0f172a",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "border": "#cbd5e1",
        "kpi_val": "#1e40af"
    },
    "Midnight Cyber": {
        "bg": "#090d16",
        "card_bg": "linear-gradient(145deg, #111827 0%, #1f2937 100%)",
        "sidebar_bg": "#0f172a",
        "text": "#e2e8f0",
        "accent": "#00f2fe",
        "accent_hover": "#4facfe",
        "border": "#1e293b",
        "kpi_val": "#00f2fe"
    },
    "Emerald Corporate": {
        "bg": "#061412",
        "card_bg": "linear-gradient(145deg, #0d231f 0%, #14352e 100%)",
        "sidebar_bg": "#0b1d19",
        "text": "#ecfdf5",
        "accent": "#10b981",
        "accent_hover": "#34d399",
        "border": "#164e63",
        "kpi_val": "#34d399"
    }
}

current_theme_cfg = THEMES_CONFIG[st.session_state['app_theme']]

# تطبيق الـ CSS الديناميكي وإلغاء مشكلة Keyboard Tooltips عند التمرير
st.markdown(f"""
    <style>
    /* 1. إخفاء حواشي وتلميحات الكيبورد والـ Tooltips نهائياً عند التمرير */
    [data-testid="stSidebar"] [data-testid="stRadio"] label::before,
    [data-testid="stSidebar"] [data-testid="stRadio"] label::after,
    [title*="keyboard"], [aria-label*="keyboard"], .st-emotion-cache-12fmw4p,
    [data-baseweb="tooltip"], div[role="tooltip"], [data-testid="stSidebar"] *[title] {{
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}
    
    *:focus-visible {{
        outline: none !important;
        box-shadow: none !important;
    }}

    /* 2. خلفيات ونصوص التطبيق */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {current_theme_cfg["bg"]} !important;
        color: {current_theme_cfg["text"]} !important;
    }}
        
    /* 3. القائمة الجانبية */
    [data-testid="stSidebar"] {{
        background-color: {current_theme_cfg["sidebar_bg"]} !important;
        border-right: 1px solid {current_theme_cfg["border"]} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: #e6edf3 !important;
    }}
    [data-testid="stSidebar"] .stRadio label {{
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }}

    /* 4. العناوين والنصوص */
    h1, h2, h3, h4, h5, h6, label, p, span {{
        color: {current_theme_cfg["text"]} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }}
    h1 {{ color: {current_theme_cfg["accent"]} !important; font-size: 2.2rem !important; font-weight: 700; }}
    h2 {{ color: {current_theme_cfg["accent"]} !important; font-size: 1.6rem !important; border-bottom: 2px solid {current_theme_cfg["border"]}; padding-bottom: 8px; margin-top: 15px; }}
    h3 {{ font-size: 1.25rem !important; }}

    /* 5. كروت المؤشرات KPI */
    .kpi-card {{
        background: {current_theme_cfg["card_bg"]};
        border: 1px solid {current_theme_cfg["border"]};
        border-top: 3px solid {current_theme_cfg["accent"]};
        border-radius: 12px;
        padding: 20px 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.3);
    }}
    .kpi-title {{
        color: #8b949e !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
        display: block;
    }}
    .kpi-value {{
        color: {current_theme_cfg["kpi_val"]} !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }}

    /* 6. الأزرار */
    .stButton>button {{
        background: linear-gradient(135deg, {current_theme_cfg["accent"]} 0%, #aa7c11 100%) !important;
        color: #0d1117 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        transition: all 0.3s ease !important;
    }}
    .stButton>button:hover {{
        background: linear-gradient(135deg, {current_theme_cfg["accent_hover"]} 0%, {current_theme_cfg["accent"]} 100%) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.4) !important;
        transform: translateY(-1px);
    }}

    /* 7. المدخلات والجداول */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {{
        background-color: {current_theme_cfg["sidebar_bg"]} !important;
        color: {current_theme_cfg["text"]} !important;
        border: 1px solid {current_theme_cfg["border"]} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stDataFrame"] {{
        background-color: {current_theme_cfg["sidebar_bg"]} !important;
        border: 1px solid {current_theme_cfg["border"]} !important;
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
    with get_connection() as conn:
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

        # مستخدم Admin افتراضي
        cursor.execute("SELECT * FROM users WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (id, username, password, full_name, email, phone, avatar_path, role)
                VALUES (1, 'admin', 'mh123456', 'مدير النظام - MH GROUP', 'admin@mhgroup.com', '01000000000', '', 'ادمن')
            ''')

        # مستخدم مطور افتراضي (Developer)
        cursor.execute("SELECT * FROM users WHERE username = 'developer'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, password, full_name, email, phone, avatar_path, role)
                VALUES ('developer', 'dev123456', 'مطور النظام (Dev Master)', 'dev@mhgroup.com', '01111111111', '', 'مطور')
            ''')

        # جدول الجلسات النشطة
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
# 4. إدارة الجلسة والدخول
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
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, role FROM active_sessions WHERE token = ?", (session_token,))
        sess_data = cursor.fetchone()
        
    if sess_data:
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = sess_data[0]
        st.session_state['user_role'] = sess_data[1]

def login():
    st.markdown("<h1 style='text-align: center; color: #d4af37; margin-top: 50px;'>MH GROUP للاستثمار والتطوير العقاري</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #8b949e !important;'>نظام إدارة الموارد المؤسسية ERP</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        username_input = st.text_input("اسم المستخدم", key="login_username")
        password_input = st.text_input("كلمة المرور", type="password", key="login_password")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("تسجيل الدخول", use_container_width=True, key="login_btn"):
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username_input, password_input))
                user = cursor.fetchone()
                
                if user:
                    token = str(uuid.uuid4())
                    cursor.execute("INSERT INTO active_sessions (token, user_id, role) VALUES (?, ?, ?)", (token, user[0], user[1]))
                    conn.commit()
                    
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user[0]
                    st.session_state['user_role'] = user[1]
                    st.query_params["session"] = token
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

if not st.session_state['logged_in']:
    login()
    st.stop()

with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, avatar_path, role FROM users WHERE id = ?", (st.session_state['user_id'],))
    current_user = cursor.fetchone()

st.sidebar.title("MH GROUP ERP")
if current_user:
    if current_user[2] and os.path.exists(current_user[2]):
        st.sidebar.image(current_user[2], width=90)
    st.sidebar.markdown(f"**أهلاً بك، {current_user[1]}**")
    st.sidebar.caption(f"الصلاحية: `{current_user[3]}`")

st.sidebar.markdown("---")

user_role = st.session_state['user_role']
username_str = current_user[0] if current_user else ""

allowed_menu = ["الملف الشخصي"]

if user_role in ["ادمن", "مطور"]:
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

# إضافة قسم المطور حصرياً
if user_role == "مطور" or username_str == "developer":
    allowed_menu.append("إعدادات الثيمات (للمطور)")

menu = st.sidebar.radio("الأقسام المتاحة:", allowed_menu, key="main_sidebar_menu_radio")
st.sidebar.markdown("---")

if st.sidebar.button("تسجيل الخروج", key="logout_btn", use_container_width=True):
    if "session" in st.query_params:
        token_to_del = st.query_params["session"]
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_sessions WHERE token = ?", (token_to_del,))
            conn.commit()
        st.query_params.clear()
        
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['user_role'] = None
    st.rerun()

# ---------------------------------------------------------
# 5. Dashboard (اللوحة الرئيسية)
# ---------------------------------------------------------
if menu == "الرئيسية (Dashboard)":
    st.header("لوحة التحكم والأداء العام")
    
    with get_connection() as conn:
        df_fin = pd.read_sql_query("SELECT * FROM finance", conn)
        df_prop = pd.read_sql_query("SELECT * FROM properties", conn)
        df_hr = pd.read_sql_query("SELECT * FROM hr", conn)
    
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
                font=dict(color=current_theme_cfg["text"]),
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
                color_discrete_sequence=['#2
