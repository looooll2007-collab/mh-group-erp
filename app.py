import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import random

# ==========================================
# 1. إعدادات النظام وقاعدة البيانات
# ==========================================
st.set_page_config(page_title="MH Group ERP", layout="wide")

# إنشاء مجلدات الملفات
os.makedirs("uploads", exist_ok=True)

def init_db():
    conn = sqlite3.connect("mh_erp.db")
    cursor = conn.cursor()
    # جداول المستخدمين والعمليات
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS session_logs (id INTEGER PRIMARY KEY, username TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, status TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS financials (id INTEGER PRIMARY KEY, type TEXT, category TEXT, department TEXT, amount REAL, description TEXT, date TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS hr_data (id TEXT PRIMARY KEY, name TEXT, type TEXT, daily_rate REAL, hourly_rate REAL, doc_name TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS properties (id TEXT PRIMARY KEY, name TEXT, finish_type TEXT, cost REAL, expenses REAL, sale_price REAL, profit REAL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS investors (name TEXT, prop_id TEXT, amount REAL, ratio REAL, returns REAL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS it_data (emp_name TEXT, emp_id TEXT, hours INTEGER, daily_rate REAL, hourly_rate REAL, doc_name TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS issues (user TEXT, dept TEXT, category TEXT, issue TEXT, doc_name TEXT, status TEXT)""")
    
    # إضافة مستخدم افتراضي
    try: cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'Admin')")
    except: pass
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. المكونات والوظائف المساعدة
# ==========================================
def get_ip(): return "192.168.1.1" # محاكاة للـ IP

def log_session(username, action):
    conn = sqlite3.connect("mh_erp.db")
    if action == "login":
        conn.execute("INSERT INTO session_logs (username, login_time, ip_address, status) VALUES (?, ?, ?, ?)", 
                     (username, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), get_ip(), "Active"))
    else:
        conn.execute("UPDATE session_logs SET logout_time = ? WHERE username = ? AND status = 'Active'", 
                     (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username))
        conn.execute("UPDATE session_logs SET status = 'Logged Out' WHERE username = ? AND status = 'Active'", (username,))
    conn.commit()
    conn.close()

# ==========================================
# 3. واجهة تسجيل الدخول
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول إلى MH Group ERP")
    user = st.text_input("اسم المستخدم")
    pw = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        conn = sqlite3.connect("mh_erp.db")
        user_data = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw)).fetchone()
        if user_data:
            st.session_state.logged_in = True
            st.session_state.username = user
            log_session(user, "login")
            st.rerun()
        else: st.error("بيانات خاطئة!")
    st.stop()

# ==========================================
# 4. القائمة الجانبية (Sidebar)
# ==========================================
st.sidebar.title(f"مرحباً {st.session_state.username}")
page = st.sidebar.radio("القائمة الرئيسية", [
    "📊 لوحة التحكم (Dashboard)", "👥 إدارة المستخدمين", "💰 الإدارة المالية", 
    "👷 الموارد البشرية (HR)", "🏢 العقارات والمخزون", "🤝 المستثمرين", 
    "💻 قسم IT", "⏱️ سجل العمليات", "⚠️ الإبلاغ عن مشكلة"
])

if st.sidebar.button("خروج"):
    log_session(st.session_state.username, "logout")
    st.session_state.logged_in = False
    st.rerun()

# ==========================================
# 5. الصفحات
# ==========================================

# 1. Dashboard
if page == "📊 لوحة التحكم (Dashboard)":
    st.header("لوحة التحكم العامة")
    conn = sqlite3.connect("mh_erp.db")
    df_fin = pd.read_sql("SELECT * FROM financials", conn)
    
    col1, col2 = st.columns(2)
    if not df_fin.empty:
        fig = px.pie(df_fin, values='amount', names='category', title="توزيع المصروفات والإيرادات")
        col1.plotly_chart(fig)
        
        fig2 = px.bar(df_fin, x='date', y='amount', color='type', title="حركة السيولة المالية")
        col2.plotly_chart(fig2)

# 2. User Management
elif page == "👥 إدارة المستخدمين":
    st.header("إدارة المستخدمين")
    conn = sqlite3.connect("mh_erp.db")
    
    # إضافة مستخدم
    with st.expander("إضافة مستخدم جديد"):
        new_u = st.text_input("اسم المستخدم")
        new_p = st.text_input("كلمة المرور")
        if st.button("حفظ"):
            conn.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (new_u, new_p, "User"))
            conn.commit()
            st.success("تم!")
            
    st.subheader("سجل الجلسات والـ IP")
    df_logs = pd.read_sql("SELECT * FROM session_logs", conn)
    st.dataframe(df_logs)

# 3. Financial Management (Calculator included)
elif page == "💰 الإدارة المالية":
    st.header("قسم الإدارة المالية")
    
    # الحاسبة
    with st.expander("حاسبة رواتب الموردين/العمال"):
        col1, col2 = st.columns(2)
        with col1:
            workers = st.number_input("عدد العمال", 1)
            hours = st.number_input("عدد الساعات", 1)
            rate_h = st.number_input("سعر الساعة", 100)
        with col2:
            daily_base = st.number_input("اليومية الأساسية", 500)
            st.write(f"### الإجمالي: {(workers * hours * rate_h) + (workers * daily_base)}")
    
    # المعاملات
    with st.form("finance_form"):
        t_type = st.selectbox("النوع", ["إيرادات", "صادرات", "سلف"])
        amount = st.number_input("المبلغ")
        desc = st.text_area("وصف")
        if st.form_submit_button("تسجيل"):
            conn = sqlite3.connect("mh_erp.db")
            conn.execute("INSERT INTO financials (type, amount, description, date) VALUES (?,?,?,?)", (t_type, amount, desc, datetime.date.today()))
            conn.commit()
            st.success("تم التسجيل")

# 4. HR (Uploads + ID)
elif page == "👷 الموارد البشرية (HR)":
    st.header("إدارة الموارد البشرية")
    id_code = st.text_input("رقم الـ ID للموظف")
    name = st.text_input("الاسم")
    file = st.file_uploader("إرفاق مستند")
    if st.button("حفظ"):
        # منطق حفظ الملف
        if file:
            with open(f"uploads/{file.name}", "wb") as f: f.write(file.getbuffer())
        st.success("تم حفظ البيانات")

# 5. Real Estate
elif page == "🏢 العقارات والمخزون":
    st.header("إدارة العقارات")
    # مدخلات العقار (النوع، التشطيب، التكلفة، الربح)
    with st.form("realestate_form"):
        name = st.text_input("اسم العقار")
        finish = st.selectbox("نوع التشطيب", ["سوبر لوكس", "نص تشطيب", "بدون"])
        cost = st.number_input("سعر التكلفة")
        price = st.number_input("سعر البيع")
        if st.form_submit_button("إضافة"):
            profit = price - cost
            st.write(f"الربح المتوقع: {profit}")
            # Insert to DB...

# (يمكنك إضافة باقي الصفحات بنفس النمط المذكور أعلاه لـ IT و المستثمرين)

# 9. Issues
elif page == "⚠️ الإبلاغ عن مشكلة":
    st.header("الدعم الفني")
    cat = st.selectbox("تصنيف المشكلة", ["تقنية", "مالية", "أخرى"])
    issue = st.text_area("تفاصيل المشكلة")
    file = st.file_uploader("مستند داعم")
    if st.button("إرسال البلاغ"):
        st.success("تم استلام بلاغك!")
