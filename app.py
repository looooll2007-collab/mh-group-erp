import datetime
import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والثيمات المؤسسية
# ==========================================
THEMES = {
    "الداكن الملكي والذهبي (Royal Dark & Gold)": {
        "primary": "#D97706",
        "bg": "#0F172A",
        "card": "#1E293B",
        "text": "#F8FAFC",
        "accent": "#F59E0B",
        "border": "#334155",
    },
    "أزرق نيلي احترافي (Modern Indigo)": {
        "primary": "#4F46E5",
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "text": "#1E293B",
        "accent": "#6366F1",
        "border": "#E2E8F0",
    },
}

st.set_page_config(
    page_title="MH Group ERP System - Enterprise Edition",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الداكن الملكي والذهبي (Royal Dark & Gold)"

current_theme = THEMES.get(st.session_state["selected_theme"], THEMES["الداكن الملكي والذهبي (Royal Dark & Gold)"])

st.markdown(
    f"""
<style>
    .stApp {{ background-color: {current_theme["bg"]} !important; color: {current_theme["text"]} !important; }}
    .main-header {{
        font-size: 1.8rem; font-weight: 800; color: {current_theme["primary"]} !important;
        text-align: right; margin-bottom: 15px; padding: 10px;
        border-bottom: 2px solid {current_theme["accent"]}; background-color: {current_theme["card"]};
        border-radius: 8px;
    }}
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important; padding: 15px !important;
        border-radius: 12px !important; border: 1px solid {current_theme["border"]} !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    section[data-testid="stSidebar"] {{ background-color: {current_theme["card"]} !important; border-right: 1px solid {current_theme["border"]} !important; }}
    .stButton>button {{ background-color: {current_theme["primary"]} !important; color: white !important; border-radius: 6px !important; border: none !important; }}
    .executive-card {{ background-color: {current_theme["card"]}; padding: 20px; border-radius: 12px; border: 1px solid {current_theme["border"]}; margin-bottom: 20px; }}
</style>
""", unsafe_allow_html=True,
)

UPLOAD_DIR = "uploads_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 2. قاعدة البيانات
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, phone TEXT, email TEXT, avatar_path TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, status TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS financial_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, trans_type TEXT, department TEXT, amount REAL, description TEXT, trans_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, custom_id TEXT UNIQUE, name TEXT, emp_type TEXT, craft_type TEXT, hourly_rate REAL, daily_rate REAL, workers_count INTEGER DEFAULT 1, total_pay REAL, hire_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY AUTOINCREMENT, custom_id TEXT UNIQUE, name TEXT, location TEXT, price REAL, expenses REAL DEFAULT 0.0, sale_price REAL DEFAULT 0.0, status TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS investors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, property_custom_id TEXT, investment_amount REAL, investment_ratio REAL, return_rate REAL, total_returns REAL, start_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, action TEXT, status TEXT, ip_address TEXT, timestamp TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS department_files (id INTEGER PRIMARY KEY AUTOINCREMENT, department TEXT, filename TEXT, uploader TEXT, upload_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS support_tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, issue_text TEXT, status TEXT, ticket_date TEXT)")
        
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, phone, email, avatar_path) VALUES ('admin', 'admin123', 'Admin', '01000000000', 'admin@mhgroup.com', '')")
        conn.commit()

init_db()

def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db") as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception: return pd.DataFrame()

def log_audit_action(username, department, action, status="ناجحة"):
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute("INSERT INTO audit_logs (username, department, action, status, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (username, department, action, status, "127.0.0.1", now))
            conn.commit()
    except: pass

# ==========================================
# 3. تسجيل الدخول والتنقل
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 class='main-header' style='text-align: center;'>🏢 مجموعة شركات MH Group ERP</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            with sqlite3.connect("mh_group_erp.db") as conn:
                res = conn.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username_input.strip(), password_input.strip())).fetchone()
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = username_input.strip()
                st.rerun()
            else: st.error("بيانات الدخول غير صحيحة!")
else:
    # القائمة الجانبية
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(f"**المستخدم:** `{st.session_state['username']}`\n\n**الصلاحية:** `{st.session_state['user_role']}`")
    
    pages = {
        "Admin": ["📊 لوحة التحليلات التنفيذية", "⚙️ المستخدمون والجلسات", "💰 الإدارة المالية", "👷 الموارد البشرية", "🏢 العقارات والمشاريع", "🤝 المستثمرين", "⏱️ سجل العمليات", "👤 الملف الشخصي", "🎨 الثيمات والألوان"],
        "HR": ["👷 الموارد البشرية", "👤 الملف الشخصي", "🎨 الثيمات والألوان"],
        "Finance": ["💰 الإدارة المالية", "👤 الملف الشخصي", "🎨 الثيمات والألوان"],
        "RealEstate": ["🏢 العقارات والمشاريع", "👤 الملف الشخصي", "🎨 الثيمات والألوان"],
        "Investor": ["🤝 المستثمرين", "👤 الملف الشخصي", "🎨 الثيمات والألوان"]
    }
    
    role = st.session_state["user_role"]
    allowed_pages = pages.get(role, ["👤 الملف الشخصي", "🎨 الثيمات والألوان"])
    selected_page = st.sidebar.radio("الأقسام:", allowed_pages)
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    # ==========================================
    # 📊 اللوحة التنفيذية (المحدثة لتحديث البيانات لحظياً)
    # ==========================================
    if selected_page == "📊 لوحة التحليلات التنفيذية":
        st.markdown("<h1 class='main-header'>🏢 لوحة التحكم التنفيذية الشاملة</h1>", unsafe_allow_html=True)
        
        # مؤشرات عامة
        m1, m2, m3, m4 = st.columns(4)
        fin_data = safe_read_sql("SELECT amount, trans_type FROM financial_transactions")
        tot_inc = fin_data[fin_data["trans_type"] == "واردات (إيرادات)"]["amount"].sum()
        tot_exp = fin_data[fin_data["trans_type"] == "صادرات (مصروفات)"]["amount"].sum()
        m1.metric("إجمالي الإيرادات", f"{tot_inc:,.0f} ج.م")
        m2.metric("إجمالي المصروفات", f"{tot_exp:,.0f} ج.م")
        m3.metric("صافي الأرباح", f"{(tot_inc - tot_exp):,.0f} ج.م")
        m4.metric("المشاريع الحالية", f"{len(safe_read_sql('SELECT id FROM properties'))}")

        # التبويبات مع جلب بيانات محدثة داخل كل تبويب (هنا الحل لمشكلتك)
        tab1, tab2, tab3, tab4 = st.tabs(["📈 التحليلات", "📁 أرشيف مستندات الأقسام", "🛠️ مركز البلاغات", "📋 السجلات"])
        
        with tab1:
            st.subheader("توزيع المعاملات المالية")
            if not fin_data.empty: st.bar_chart(fin_data.groupby("trans_type")["amount"].sum())
        
        with tab2:
            st.subheader("📁 الأرشيف المركزي")
            # جلب البيانات هنا داخل التبويب يضمن التحديث اللحظي عند النقر
            st.dataframe(safe_read_sql("SELECT * FROM department_files ORDER BY id DESC"), use_container_width=True)
        
        with tab3:
            st.subheader("🛠️ البلاغات المفتوحة")
            # جلب البيانات هنا داخل التبويب يضمن التحديث اللحظي
            st.dataframe(safe_read_sql("SELECT * FROM support_tickets ORDER BY id DESC"), use_container_width=True)
            
        with tab4:
            st.dataframe(safe_read_sql("SELECT * FROM audit_logs ORDER BY id DESC"), use_container_width=True)

    # باقي الأقسام (HR, Finance, etc)
    elif selected_page in ["💰 الإدارة المالية", "👷 الموارد البشرية", "🏢 العقارات والمشاريع", "🤝 المستثمرين"]:
        dept_name = selected_page.replace("💰 ", "").replace("👷 ", "").replace("🏢 ", "").replace("🤝 ", "")
        st.markdown(f"<h1 class='main-header'>🏢 قسم: {dept_name}</h1>", unsafe_allow_html=True)
        
        t_up, t_iss = st.tabs(["📁 رفع مستندات", "🛠️ إبلاغ عن مشكلة"])
        with t_up:
            up_file = st.file_uploader(f"رفع مستند لـ {dept_name}")
            if up_file:
                if st.button("تأكيد الرفع"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("INSERT INTO department_files (department, filename, uploader, upload_date) VALUES (?,?,?,?)", (dept_name, up_file.name, st.session_state["username"], str(datetime.date.today())))
                    st.success("تم الرفع!")
        with t_iss:
            issue = st.text_area("تفاصيل المشكلة")
            if st.button("إرسال البلاغ"):
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("INSERT INTO support_tickets (username, department, issue_text, status, ticket_date) VALUES (?,?,?,?,?)", (st.session_state["username"], dept_name, issue, "معلقة", str(datetime.date.today())))
                st.success("تم إرسال البلاغ للإدارة!")

    elif selected_page == "⚙️ المستخدمون والجلسات":
        st.dataframe(safe_read_sql("SELECT * FROM users"), use_container_width=True)
        
    elif selected_page == "👤 الملف الشخصي":
        st.write("ملف المستخدم الشخصي")
        
    elif selected_page == "🎨 الثيمات والألوان":
        selected_th = st.selectbox("اختر الثيم:", list(THEMES.keys()))
        if selected_th != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = selected_th
            st.rerun()
