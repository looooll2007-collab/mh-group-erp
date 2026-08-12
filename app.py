import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. إعدادات النظام وقاعدة البيانات
# ==========================================
st.set_page_config(page_title="MH Group ERP System", layout="wide")

# إنشاء المجلدات اللازمة
if not os.path.exists("uploads"): os.makedirs("uploads")
if not os.path.exists("db"): os.makedirs("db")

def get_db_connection():
    return sqlite3.connect("db/mh_erp.db")

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # الجداول
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, username TEXT, login_time TEXT, logout_time TEXT, ip TEXT, status TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS finance (id INTEGER PRIMARY KEY, type TEXT, dept TEXT, amount REAL, description TEXT, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS hr_records (id TEXT PRIMARY KEY, name TEXT, role TEXT, daily_rate REAL, hourly_rate REAL, doc_name TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS real_estate (id TEXT PRIMARY KEY, name TEXT, finish TEXT, cost REAL, expenses REAL, price REAL, profit REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS investors (name TEXT, prop_id TEXT, amount REAL, ratio REAL, returns REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS it_logs (emp_name TEXT, emp_id TEXT, hours REAL, daily_rate REAL, hourly_rate REAL, doc_name TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS support_tickets (id INTEGER PRIMARY KEY, user TEXT, category TEXT, issue TEXT, doc_name TEXT, status TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, user TEXT, action TEXT, status TEXT, timestamp TEXT)""")
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. وظائف مساعدة
# ==========================================
def log_action(user, action, status):
    conn = get_db_connection()
    conn.execute("INSERT INTO audit_logs (user, action, status, timestamp) VALUES (?,?,?,?)", 
                 (user, action, status, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ==========================================
# 3. واجهة الدخول
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔑 نظام إدارة MH Group - دخول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user = u
            conn.execute("INSERT INTO sessions (username, login_time, status) VALUES (?,?,?)", (u, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Active"))
            conn.commit()
            log_action(u, "تسجيل دخول", "نجاح")
            st.rerun()
        else:
            log_action(u, "محاولة دخول", "فشل")
            st.error("بيانات غير صحيحة")
    st.stop()

# ==========================================
# 4. القائمة الجانبية (Navigation)
# ==========================================
st.sidebar.title(f"مرحباً {st.session_state.user}")
menu = ["📊 لوحة التحكم", "👥 المستخدمين", "💰 الإدارة المالية", "👷 الموارد البشرية", "🏢 العقارات والمخزون", "🤝 المستثمرين", "💻 قسم IT", "⏱️ سجل العمليات", "⚠️ الإبلاغ عن مشكلة"]
choice = st.sidebar.radio("القائمة", menu)

if st.sidebar.button("تسجيل خروج"):
    conn = get_db_connection()
    conn.execute("UPDATE sessions SET logout_time=? WHERE username=? AND status='Active'", (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.user))
    conn.commit()
    st.session_state.logged_in = False
    st.rerun()

# ==========================================
# 5. الصفحات
# ==========================================

# 1. Dashboard
if choice == "📊 لوحة التحكم":
    st.header("📈 لوحة التحكم العامة")
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM finance", conn)
    if not df.empty:
        col1, col2 = st.columns(2)
        fig1 = px.pie(df, values='amount', names='type', title="توزيع المالية (إيرادات/صادرات)")
        col1.plotly_chart(fig1)
        fig2 = px.bar(df, x='date', y='amount', color='dept', title="حركة السيولة بالأقسام")
        col2.plotly_chart(fig2)

# 2. Users
elif choice == "👥 المستخدمين":
    st.header("👥 إدارة المستخدمين وصلاحيات الدخول")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("new_user"):
            n_u = st.text_input("اسم المستخدم")
            n_p = st.text_input("كلمة المرور")
            if st.form_submit_button("إضافة مستخدم"):
                get_db_connection().execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (n_u, n_p, "User"))
                st.success("تم")
    with col2:
        st.subheader("سجل الجلسات")
        st.dataframe(pd.read_sql("SELECT * FROM sessions", get_db_connection()))

# 3. Finance (Calculator)
elif choice == "💰 الإدارة المالية":
    st.header("💰 الإدارة المالية والحاسبة")
    tab1, tab2 = st.tabs(["حاسبة الرواتب", "سجل المعاملات"])
    with tab1:
        workers = st.number_input("عدد العمال", 1)
        hours = st.number_input("عدد الساعات", 1)
        hourly_r = st.number_input("سعر الساعة", 50)
        daily_r = st.number_input("اليومية الأساسية", 200)
        st.metric("إجمالي المستحق", f"{(workers * hours * hourly_r) + (workers * daily_r)} ج.م")
    with tab2:
        with st.form("finance_entry"):
            t = st.selectbox("نوع المعاملة", ["واردات", "صادرات", "سلف"])
            d = st.text_input("القسم")
            a = st.number_input("المبلغ")
            if st.form_submit_button("حفظ"):
                get_db_connection().execute("INSERT INTO finance (type, dept, amount, date) VALUES (?,?,?,?)", (t, d, a, datetime.date.today()))
                st.success("تم الحفظ")
        st.dataframe(pd.read_sql("SELECT * FROM finance", get_db_connection()))

# 4. HR
elif choice == "👷 الموارد البشرية":
    st.header("👷 إدارة الموارد البشرية")
    with st.form("hr_form"):
        eid = st.text_input("رقم الـ ID")
        name = st.text_input("اسم الموظف/المورد")
        role = st.selectbox("الوظيفة", ["عامل", "نحات", "مهندس"])
        dr = st.number_input("سعر اليومية")
        hr = st.number_input("سعر الساعة")
        file = st.file_uploader("إرفاق مستند")
        if st.form_submit_button("حفظ الموظف"):
            fname = "N/A"
            if file:
                fname = file.name
                with open(f"uploads/{fname}", "wb") as f: f.write(file.getbuffer())
            get_db_connection().execute("INSERT INTO hr_records VALUES (?,?,?,?,?,?)", (eid, name, role, dr, hr, fname))
            st.success("تم حفظ البيانات")
    st.dataframe(pd.read_sql("SELECT * FROM hr_records", get_db_connection()))

# 5. Real Estate
elif choice == "🏢 العقارات والمخزون":
    st.header("🏢 إدارة العقارات")
    with st.form("prop_form"):
        c1, c2 = st.columns(2)
        pid = c1.text_input("ID العقار")
        pname = c2.text_input("اسم العقار")
        finish = c1.selectbox("نوع التشطيب", ["سوبر لوكس", "نص تشطيب", "بدون"])
        cost = c2.number_input("التكلفة")
        exp = c1.number_input("المصروفات")
        price = c2.number_input("سعر البيع")
        if st.form_submit_button("إضافة عقار"):
            profit = price - (cost + exp)
            get_db_connection().execute("INSERT INTO real_estate VALUES (?,?,?,?,?,?,?)", (pid, pname, finish, cost, exp, price, profit))
            st.success(f"تم الإضافة، الربح المتوقع: {profit}")
    st.dataframe(pd.read_sql("SELECT * FROM real_estate", get_db_connection()))

# 6. Investors
elif choice == "🤝 المستثمرين":
    st.header("🤝 إدارة المستثمرين")
    with st.form("inv_form"):
        iname = st.text_input("اسم المستثمر")
        pid = st.text_input("رقم العقار المستثمر فيه")
        amount = st.number_input("قيمة الاستثمار")
        ratio = st.slider("نسبة الاستثمار (%)", 1, 100)
        if st.form_submit_button("حساب العائد"):
            returns = amount * (ratio/100)
            get_db_connection().execute("INSERT INTO investors VALUES (?,?,?,?,?)", (iname, pid, amount, ratio, returns))
            st.info(f"إجمالي العائد: {returns}")
    st.dataframe(pd.read_sql("SELECT * FROM investors", get_db_connection()))

# 7. IT
elif choice == "💻 قسم IT":
    st.header("💻 قسم تقنية المعلومات")
    with st.form("it_form"):
        name = st.text_input("اسم الموظف")
        eid = st.text_input("ID الموظف")
        hours = st.number_input("عدد ساعات العمل")
        file = st.file_uploader("إرفاق ملف تقني")
        if st.form_submit_button("تسجيل"):
            get_db_connection().execute("INSERT INTO it_logs VALUES (?,?,?,?,?,?)", (name, eid, hours, 0, 0, file.name if file else "N/A"))
            st.success("تم")
    st.dataframe(pd.read_sql("SELECT * FROM it_logs", get_db_connection()))

# 8. Logs
elif choice == "⏱️ سجل العمليات":
    st.header("⏱️ سجل العمليات والرقابة")
    st.dataframe(pd.read_sql("SELECT * FROM audit_logs", get_db_connection()))

# 9. Support
elif choice == "⚠️ الإبلاغ عن مشكلة":
    st.header("⚠️ مركز الدعم الفني")
    with st.form("ticket_form"):
        cat = st.selectbox("تصنيف المشكلة", ["تقنية", "مالية", "إدارية"])
        issue = st.text_area("تفاصيل المشكلة")
        file = st.file_uploader("إرفاق مستند للمشكلة")
        if st.form_submit_button("إرسال البلاغ"):
            get_db_connection().execute("INSERT INTO support_tickets (user, category, issue, doc_name, status) VALUES (?,?,?,?,?)", 
                                        (st.session_state.user, cat, issue, file.name if file else "N/A", "مفتوح"))
            st.success("تم إرسال بلاغك!")
    st.dataframe(pd.read_sql("SELECT * FROM support_tickets", get_db_connection()))
