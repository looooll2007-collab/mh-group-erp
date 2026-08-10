import datetime
import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والثيمات
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
    .stApp {{
        background-color: {current_theme["bg"]} !important;
        color: {current_theme["text"]} !important;
    }}
    .main-header {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {current_theme["primary"]} !important;
        text-align: right;
        margin-bottom: 15px;
        padding: 10px;
        border-bottom: 2px solid {current_theme["accent"]};
        background-color: {current_theme["card"]};
        border-radius: 8px;
    }}
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important;
        padding: 12px !important;
        border-radius: 10px !important;
        border: 1px solid {current_theme["border"]} !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {current_theme["card"]} !important;
        border-right: 1px solid {current_theme["border"]} !important;
    }}
    .stButton>button {{
        background-color: {current_theme["primary"]} !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: bold !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)

UPLOAD_DIR = "uploads_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# 2. قاعدة البيانات والجداول
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT,
                avatar_path TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_time TEXT,
                logout_time TEXT,
                ip_address TEXT,
                status TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trans_type TEXT,
                department TEXT,
                amount REAL,
                description TEXT,
                trans_date TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
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
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custom_id TEXT UNIQUE,
                name TEXT,
                location TEXT,
                price REAL,
                expenses REAL DEFAULT 0.0,
                sale_price REAL DEFAULT 0.0,
                status TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                property_custom_id TEXT,
                investment_amount REAL,
                investment_ratio REAL,
                return_rate REAL,
                total_returns REAL,
                start_date TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                department TEXT,
                action TEXT,
                status TEXT,
                ip_address TEXT,
                timestamp TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS department_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT,
                filename TEXT,
                uploader TEXT,
                upload_date TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                department TEXT,
                issue_text TEXT,
                status TEXT,
                ticket_date TEXT
            )
        """)

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, phone, avatar_path) VALUES ('admin', 'admin123', 'Admin', '01000000000', '')")

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
        ip = "127.0.0.1"
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            if "X-Forwarded-For" in headers:
                ip = headers["X-Forwarded-For"].split(",")[0]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute(
                "INSERT INTO audit_logs (username, department, action, status, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (username, department, action, status, ip, now)
            )
            conn.commit()
    except Exception:
        pass

# ==========================================
# 3. تسجيل الدخول
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

def login_page():
    st.markdown("<h1 class='main-header' style='text-align: center;'>🏢 مجموعة شركات MH Group ERP</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 بوابة الدخول الموحدة للمجموعة")
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button("تسجيل الدخول", use_container_width=True):
            un = username_input.strip()
            pw = password_input.strip()
            with sqlite3.connect("mh_group_erp.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (un, pw))
                res = cursor.fetchone()

            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = un

                login_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with sqlite3.connect("mh_group_erp.db") as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO user_sessions (username, login_time, logout_time, ip_address, status) VALUES (?, ?, ?, ?, ?)",
                        (un, login_now, "نشطة حالياً", "127.0.0.1", "نشطة")
                    )
                    conn.commit()
                    st.session_state["session_id"] = cur.lastrowid

                log_audit_action(un, "الدخول", f"تسجيل دخول بصلاحية: {res[0]}")
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")

if not st.session_state["logged_in"]:
    login_page()
else:
    user_rec = safe_read_sql("SELECT phone, avatar_path FROM users WHERE username = ?", (st.session_state["username"],))
    user_avatar = user_rec.iloc[0]["avatar_path"] if not user_rec.empty and user_rec.iloc[0]["avatar_path"] else None

    st.sidebar.title("🏢 MH Group ERP")
    if user_avatar and os.path.exists(user_avatar):
        st.sidebar.image(user_avatar, width=80)
    st.sidebar.markdown(f"**المستخدم:** `{st.session_state['username']}`\n\n**الصلاحية:** `{st.session_state['user_role']}`")

    # تحديد الصلاحيات والقوائم حسب دور المستخدم
    role = st.session_state["user_role"]

    allowed_pages = ["📊 لوحة التحليلات التنفيذية"]

    if role == "Admin":
        allowed_pages.extend([
            "⚙️ المستخدمون والجلسات والـ IP",
            "💰 الإدارة المالية",
            "📌 لوحة خدمات الإدارة المالية",
            "👷 الموارد البشرية",
            "📌 لوحة خدمات الموارد البشرية",
            "🏢 العقارات والمشاريع",
            "📌 لوحة خدمات العقارات والمشاريع",
            "🤝 المستثمرين",
            "📌 لوحة خدمات المستثمرين",
            "⏱️ سجل العمليات",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ])
    elif role == "HR":
        allowed_pages.extend([
            "👷 الموارد البشرية",
            "📌 لوحة خدمات الموارد البشرية",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ])
    elif role == "Finance":
        allowed_pages.extend([
            "💰 الإدارة المالية",
            "📌 لوحة خدمات الإدارة المالية",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ])
    elif role == "RealEstate":
        allowed_pages.extend([
            "🏢 العقارات والمشاريع",
            "📌 لوحة خدمات العقارات والمشاريع",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ])
    elif role == "Investor":
        allowed_pages.extend([
            "🤝 المستثمرين",
            "📌 لوحة خدمات المستثمرين",
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ])
    else:
        allowed_pages.extend([
            "👤 الملف الشخصي",
            "🎨 الثيمات والألوان"
        ])

    selected_page = st.sidebar.radio("الأقسام:", allowed_pages)

    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        if st.session_state["session_id"]:
            logout_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute("UPDATE user_sessions SET logout_time = ?, status = 'منتهية' WHERE id = ?", (logout_now, st.session_state["session_id"]))
                conn.commit()
        log_audit_action(st.session_state["username"], "خروج", "تسجيل خروج آمن")
        st.session_state["logged_in"] = False
        st.session_state["session_id"] = None
        st.rerun()

    # دالة لتقديم صفحة خدمات القسم المستقلة من القائمة الجانبية
    def render_department_service_page(dept_name):
        st.markdown(f"<h1 class='main-header'>📌 لوحة خدمات قسم: {dept_name}</h1>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["👤 الملف الشخصي السريع", "📁 رفع تقارير ومستندات القسم", "🛠️ الإبلاغ عن مشكلة بالقسم"])
        
        with t1:
            curr = st.session_state["username"]
            df_u = safe_read_sql("SELECT username, phone, role, avatar_path FROM users WHERE username = ?", (curr,))
            if not df_u.empty:
                c_img, c_txt = st.columns([1, 3])
                with c_img:
                    av = df_u.iloc[0]["avatar_path"]
                    if av and os.path.exists(av):
                        st.image(av, width=100)
                    else:
                        st.info("لا توجد صورة شخصية.")
                with c_txt:
                    st.write(f"**اسم المستخدم:** {df_u.iloc[0]['username']}")
                    st.write(f"**الصلاحية:** {df_u.iloc[0]['role']}")
                    st.write(f"**الهاتف:** {df_u.iloc[0]['phone']}")

        with t2:
            uploaded_file = st.file_uploader(f"رفع مستند أو تقرير جديد لـ {dept_name}", key=f"up_{dept_name}")
            if uploaded_file:
                filepath = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute("INSERT INTO department_files (department, filename, uploader, upload_date) VALUES (?, ?, ?, ?)",
                                 (dept_name, uploaded_file.name, st.session_state["username"], str(datetime.date.today())))
                    conn.commit()
                st.success("تم رفع المستند/التقرير بنجاح!")
            
            st.write("#### المستندات والتقارير المرفوعة للقسم:")
            df_files = safe_read_sql("SELECT filename, uploader, upload_date FROM department_files WHERE department = ?", (dept_name,))
            st.dataframe(df_files, use_container_width=True)

        with t3:
            with st.form(f"issue_form_{dept_name}"):
                issue_desc = st.text_area("تفاصيل المشكلة أو العطل التقني في القسم")
                if st.form_submit_button("إرسال الإبلاغ للإدارة"):
                    if issue_desc:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO support_tickets (username, department, issue_text, status, ticket_date) VALUES (?, ?, ?, ?, ?)",
                                         (st.session_state["username"], dept_name, issue_desc, "معلقة", str(datetime.date.today())))
                            conn.commit()
                        log_audit_action(st.session_state["username"], dept_name, f"إبلاغ عن مشكلة: {issue_desc}")
                        st.success("تم تسجيل الإبلاغ وإرساله بنجاح!")

    # ==========================================
    # 📊 1. لوحة التحليلات التنفيذية
    # ==========================================
    if selected_page == "📊 لوحة التحليلات التنفيذية":
        st.markdown(f"<h1 class='main-header'>🏢 لوحة التحكم</h1>", unsafe_allow_html=True)
        st.markdown(f"👋 **مرحباً بك، {st.session_state['username']}**")

        df_fin = safe_read_sql("SELECT trans_type, amount FROM financial_transactions")
        tot_inc = df_fin[df_fin["trans_type"] == "واردات (إيرادات)"]["amount"].sum() if not df_fin.empty else 0.0
        tot_exp = df_fin[df_fin["trans_type"] == "صادرات (مصروفات)"]["amount"].sum() if not df_fin.empty else 0.0
        net_prof = tot_inc - tot_exp

        df_props = safe_read_sql("SELECT price FROM properties")
        prop_val = df_props["price"].sum() if not df_props.empty else 0.0
        prop_count = len(df_props)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("إجمالي الإيرادات", f"{tot_inc:,.0f} ج.م", "12.5%+ عن الشهر الماضي")
        with m2:
            st.metric("إجمالي المصروفات", f"{tot_exp:,.0f} ج.م", "3.2%- عن الشهر الماضي")
        with m3:
            st.metric("صافي الأرباح", f"{net_prof:,.0f} ج.م", "18.7%+ عن الشهر الماضي")
        with m4:
            st.metric("قيمة العقارات", f"{prop_val:,.0f} ج.م", "إجمالي المحفظة العقارية")
        with m5:
            st.metric("العقارات المسجلة", f"{prop_count}", "عقار مسجل بالنظام")

        st.markdown("---")

        col_l, col_m, col_r = st.columns([2, 1.2, 1.2])
        with col_l:
            st.subheader("📈 نظرة عامة على الأداء")
            chart_data = pd.DataFrame({
                "الشهر": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو"],
                "الإيرادات": [5000000, 6200000, 5800000, 7100000, 6900000, 7400000, tot_inc if tot_inc>0 else 8250000],
                "المصروفات": [2100000, 2300000, 2200000, 2500000, 2700000, 2600000, tot_exp if tot_exp>0 else 2850000],
                "الأرباح": [2900000, 3900000, 3600000, 4600000, 4200000, 4800000, net_prof if net_prof!=0 else 5400000]
            })
            st.line_chart(chart_data.set_index("الشهر"))

        with col_m:
            st.subheader("🍩 توزيع المصروفات")
            exp_dist = pd.DataFrame({
                "الفئة": ["شراء عقارات", "مصاريف تطوير", "مصاريف إدارية", "رواتب وأجور", "أخرى"],
                "النسبة": [40, 25, 15, 10, 10]
            })
            st.bar_chart(exp_dist.set_index("الفئة"))
            st.caption(f"إجمالي المصروفات الحالية: {tot_exp:,.0f} ج.م")

        with col_r:
            st.subheader("⚡ النشاط الأخير")
            df_logs_recent = safe_read_sql("SELECT action, timestamp FROM audit_logs ORDER BY id DESC LIMIT 5")
            if not df_logs_recent.empty:
                for _, row in df_logs_recent.iterrows():
                    st.markdown(f"🔹 **{row['action']}**\n<small style='color:gray;'>{row['timestamp']}</small>", unsafe_allow_html=True)
            else:
                st.info("لا توجد أنشطة مسجلة حديثاً.")

    # ==========================================
    # 👤 الملف الشخصي (مُصحح تماماً)
    # ==========================================
    elif selected_page == "👤 الملف الشخصي":
        st.markdown("<h1 class='main-header'>👤 الملف الشخصي وإعدادات الحساب</h1>", unsafe_allow_html=True)
        curr_user = st.session_state["username"]
        df_u = safe_read_sql("SELECT username, phone, role, avatar_path FROM users WHERE username = ?", (curr_user,))
        
        if not df_u.empty:
            col_img, col_info = st.columns([1, 2])
            with col_img:
                current_av = df_u.iloc[0]["avatar_path"]
                if current_av and os.path.exists(current_av):
                    st.image(current_av, width=150, caption="الصورة الشخصية الحالية")
                else:
                    st.info("لا توجد صورة شخصية مرفوعة.")
                
                avatar_file = st.file_uploader("رفع أو تغيير الصورة الشخصية", type=["jpg", "png", "jpeg"], key="profile_avatar_upload")
                if avatar_file:
                    av_path = os.path.join(UPLOAD_DIR, f"avatar_{curr_user}_{avatar_file.name}")
                    with open(av_path, "wb") as f:
                        f.write(avatar_file.getbuffer())
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("UPDATE users SET avatar_path = ? WHERE username = ?", (av_path, curr_user))
                        conn.commit()
                    st.success("تم تحديث الصورة الشخصية بنجاح!")
                    st.rerun()

            with col_info:
                st.write(f"**اسم المستخدم:** `{df_u.iloc[0]['username']}`")
                st.write(f"**الصلاحية الحالية:** `{df_u.iloc[0]['role']}`")
                
                with st.form("update_profile_form"):
                    new_phone = st.text_input("رقم الهاتف الحالي", value=df_u.iloc[0]['phone'] or "")
                    old_pw = st.text_input("كلمة المرور الحالية", type="password")
                    new_pw = st.text_input("كلمة المرور الجديدة (اختياري)", type="password")
                    confirm_pw = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
                    
                    if st.form_submit_button("حفظ التحديثات"):
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            cur = conn.cursor()
                            cur.execute("SELECT password FROM users WHERE username = ?", (curr_user,))
                            db_pw = cur.fetchone()[0]
                            
                            if old_pw != db_pw:
                                st.error("كلمة المرور الحالية غير صحيحة!")
                            elif new_pw and new_pw != confirm_pw:
                                st.error("كلمتا المرور الجديدتان غير متطابقتين!")
                            else:
                                final_pw = new_pw if new_pw else db_pw
                                cur.execute("UPDATE users SET password = ?, phone = ? WHERE username = ?", (final_pw, new_phone, curr_user))
                                conn.commit()
                                log_audit_action(curr_user, "الملف الشخصي", "تحديث بيانات الحساب")
                                st.success("تم تحديث البيانات بنجاح!")
                                st.rerun()

    # ==========================================
    # 🎨 الثيمات والألوان
    # ==========================================
    elif selected_page == "🎨 الثيمات والألوان":
        st.markdown("<h1 class='main-header'>🎨 تخصيص ألوان وثيم المنظومة</h1>", unsafe_allow_html=True)
        theme_options = list(THEMES.keys())
        selected_th = st.selectbox("اختر ثيم النظام:", theme_options, index=theme_options.index(st.session_state["selected_theme"]) if st.session_state["selected_theme"] in theme_options else 0)
        if selected_th != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = selected_th
            st.rerun()

    # ==========================================
    # ⚙️ المستخدمون والجلسات والـ IP
    # ==========================================
    elif selected_page == "⚙️ المستخدمون والجلسات والـ IP":
        st.markdown("<h1 class='main-header'>⚙️ إدارة المستخدمين والجلسات النشطة والـ IP</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["👥 إدارة الحسابات", "➕ إضافة مستخدم", "📡 الجلسات النشطة والـ IP"])

        with tab1:
            df_users = safe_read_sql("SELECT id, username, role, phone FROM users")
            st.dataframe(df_users, use_container_width=True)
            user_to_del = st.selectbox("اختر المستخدم للحذف:", options=[""] + df_users["username"].tolist())
            if st.button("تأكيد حذف الحساب"):
                if user_to_del and user_to_del != "admin":
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                        conn.commit()
                    st.success(f"تم حذف الحساب {user_to_del}!")
                    st.rerun()

        with tab2:
            with st.form("add_user_f"):
                nu = st.text_input("اسم المستخدم")
                np = st.text_input("كلمة المرور", type="password")
                nr = st.selectbox("الصلاحية", ["HR", "Finance", "RealEstate", "Investor", "Admin"])
                nph = st.text_input("رقم الهاتف")
                if st.form_submit_button("إضافة الحساب"):
                    if nu and np:
                        try:
                            with sqlite3.connect("mh_group_erp.db") as conn:
                                conn.execute("INSERT INTO users (username, password, role, phone, avatar_path) VALUES (?, ?, ?, ?, ?)", (nu.strip(), np.strip(), nr, nph, ""))
                                conn.commit()
                            st.success(f"تم إضافة المستخدم {nu} بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مكرر!")

        with tab3:
            st.subheader("📡 سجل الجلسات النشطة وإدارة الـ IPs")
            df_sessions = safe_read_sql("SELECT * FROM user_sessions ORDER BY id DESC")
            st.dataframe(df_sessions, use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                sess_id_del = st.number_input("أدخل ID الجلسة لحذفها:", min_value=1, step=1)
                if st.button("حذف الجلسة النشطة"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM user_sessions WHERE id = ?", (sess_id_del,))
                        conn.commit()
                    st.success("تم حذف الجلسة بنجاح!")
                    st.rerun()
            with c2:
                ip_to_del = st.text_input("أدخل IP للمسح الشامل:")
                if st.button("مسح سجلات الـ IP"):
                    if ip_to_del:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("DELETE FROM user_sessions WHERE ip_address = ?", (ip_to_del,))
                            conn.commit()
                        st.success("تم مسح السجلات بنجاح!")
                        st.rerun()

    # ==========================================
    # 💰 الإدارة المالية
    # ==========================================
    elif selected_page == "💰 الإدارة المالية":
        st.markdown("<h1 class='main-header'>💰 الإدارة المالية وحاسبة المستحقات والعمالة</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["💸 تسجيل المصروفات والإيرادات", "📜 كشف الحسابات"])
        with tab1:
            with st.form("fin_form"):
                ttype = st.selectbox("نوع المعاملة", ["صادرات (مصروفات)", "واردات (إيرادات)"])
                tdept = st.selectbox("القسم التابع له", ["العقارات", "الموارد البشرية", "المستثمرين", "عام"])
                tamt = st.number_input("المبلغ (EGP)", min_value=0.0)
                tdesc = st.text_input("الوصف / البيان")
                if st.form_submit_button("حفظ المعاملة"):
                    if tamt > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO financial_transactions (trans_type, department, amount, description, trans_date) VALUES (?, ?, ?, ?, ?)",
                                         (ttype, tdept, tamt, tdesc, str(datetime.date.today())))
                            conn.commit()
                        st.success("تم الحفظ بنجاح!")
                        st.rerun()
        with tab2:
            st.dataframe(safe_read_sql("SELECT * FROM financial_transactions ORDER BY id DESC"), use_container_width=True)

    elif selected_page == "📌 لوحة خدمات الإدارة المالية":
        render_department_service_page("الإدارة المالية")

    # ==========================================
    # 👷 الموارد البشرية
    # ==========================================
    elif selected_page == "👷 الموارد البشرية":
        st.markdown("<h1 class='main-header'>👷 قسم الموارد البشرية والعمالة</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 سجل الكادر", "➕ إضافة كادر"])
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM employees"), use_container_width=True)
        with tab2:
            with st.form("add_emp_form"):
                cid = st.text_input("ID الفريد", value=f"EMP-{random.randint(1000, 9999)}")
                ename = st.text_input("اسم العامل / الموظف")
                etype = st.selectbox("الفئة", ["موظف ثابت", "مورد عمال", "عامل مستقل"])
                ctype = st.selectbox("التخصص", ["نقاش", "نحات", "عامل", "مشرف", "إداري"])
                hrate = st.number_input("سعر الساعة", min_value=0.0)
                drate = st.number_input("سعر اليومية", min_value=0.0)
                wcnt = st.number_input("عدد العمال", min_value=1, value=1)
                tot = (hrate * 8 * wcnt) if hrate > 0 else (drate * wcnt)
                if st.form_submit_button("حفظ البيانات"):
                    if ename:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO employees (custom_id, name, emp_type, craft_type, hourly_rate, daily_rate, workers_count, total_pay, hire_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                         (cid, ename, etype, ctype, hrate, drate, wcnt, tot, str(datetime.date.today())))
                            conn.commit()
                        st.success("تم الحفظ!")
                        st.rerun()

    elif selected_page == "📌 لوحة خدمات الموارد البشرية":
        render_department_service_page("الموارد البشرية")

    # ==========================================
    # 🏢 العقارات والمشاريع
    # ==========================================
    elif selected_page == "🏢 العقارات والمشاريع":
        st.markdown("<h1 class='main-header'>🏢 قسم إدارة العقارات والمشاريع</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 العقارات المسجلة", "➕ إضافة عقار"])
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM properties"), use_container_width=True)
        with tab2:
            with st.form("add_prop_f"):
                pid = st.text_input("ID العقار", value=f"PROP-{random.randint(100, 999)}")
                pname = st.text_input("اسم المشروع / العقار")
                ploc = st.text_input("الموقع")
                pprice = st.number_input("سعر الشراء", min_value=0.0)
                pexp = st.number_input("المصروفات", min_value=0.0)
                psale = st.number_input("سعر البيع المتوقع", min_value=0.0)
                if st.form_submit_button("حفظ العقار"):
                    if pname:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO properties (custom_id, name, location, price, expenses, sale_price, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                         (pid, pname, ploc, pprice, pexp, psale, "متاح"))
                            conn.commit()
                        st.success("تم الحفظ!")
                        st.rerun()

    elif selected_page == "📌 لوحة خدمات العقارات والمشاريع":
        render_department_service_page("العقارات والمشاريع")

    # ==========================================
    # 🤝 المستثمرين
    # ==========================================
    elif selected_page == "🤝 المستثمرين":
        st.markdown("<h1 class='main-header'>🤝 قسم المستثمرين وحساب الأرباح</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📋 سجل المستثمرين", "➕ إضافة مستثمر"])
        with tab1:
            st.dataframe(safe_read_sql("SELECT * FROM investors ORDER BY id DESC"), use_container_width=True)
        with tab2:
            df_props = safe_read_sql("SELECT custom_id FROM properties")
            prop_options = df_props["custom_id"].tolist() if not df_props.empty else ["عام"]
            with st.form("add_investor_form"):
                inv_name = st.text_input("اسم المستثمر")
                prop_id = st.selectbox("العقار المرتبط", prop_options)
                inv_amt = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                inv_ratio = st.number_input("نسبة المشاركة (%)", min_value=0.0, max_value=100.0)
                return_rate = st.number_input("نسبة العائد المتوقع (%)", min_value=0.0)
                tot_returns = inv_amt * (1 + (return_rate / 100))
                if st.form_submit_button("حفظ بيانات المستثمر"):
                    if inv_name and inv_amt > 0:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute("INSERT INTO investors (name, property_custom_id, investment_amount, investment_ratio, return_rate, total_returns, start_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                         (inv_name, prop_id, inv_amt, inv_ratio, return_rate, tot_returns, str(datetime.date.today())))
                            conn.commit()
                        st.success("تم الحفظ!")
                        st.rerun()

    elif selected_page == "📌 لوحة خدمات المستثمرين":
        render_department_service_page("المستثمرين")

    # ==========================================
    # ⏱️ سجل العمليات
    # ==========================================
    elif selected_page == "⏱️ سجل العمليات":
        st.markdown("<h1 class='main-header'>⏱️ سجل العمليات والأنشطة (Audit Trail)</h1>", unsafe_allow_html=True)
        if st.button("🗑️ تفريغ كافة السجلات"):
            with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute("DELETE FROM audit_logs")
                conn.commit()
            st.success("تم التفريغ!")
            st.rerun()
        df_logs = safe_read_sql("SELECT id, username, department, action, status, ip_address, timestamp FROM audit_logs ORDER BY id DESC")
        st.dataframe(df_logs, use_container_width=True)
