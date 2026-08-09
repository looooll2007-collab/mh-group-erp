import base64
import datetime
import io
import json
import random
import sqlite3
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. قائمة الثيمات
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
    "أخضر زمردي فخم (Emerald Slate)": {
        "primary": "#059669",
        "bg": "#F4FBF7",
        "card": "#FFFFFF",
        "text": "#064E3B",
        "accent": "#10B981",
        "border": "#D1FAE5",
    },
}

st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = (
        "الداكن الملكي والذهبي (Royal Dark & Gold)"
    )

current_theme = THEMES[st.session_state["selected_theme"]]

# --- إعدادات الجلسات ---
if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 نظام إدارة MH Group ERP",
        "subtitle": "🔐 تسجيل الدخول للنظام",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
        "logo_bytes": None,
        "google_enabled": True,
        "microsoft_enabled": True,
    }

if "dashboard_config" not in st.session_state:
    st.session_state["dashboard_config"] = {
        "header_title": "📊 لوحة التحكم المتقدمة والملخص العام",
        "show_metrics": True,
        "custom_note": "أهلاً بك في لوحة تحكم النظام العامة. يمكنك متابعة العمليات من هنا.",
    }

st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {current_theme["bg"]} !important;
        color: {current_theme["text"]} !important;
    }}
    .main-header {{
        font-size: 2rem;
        font-weight: 800;
        color: {current_theme["primary"]} !important;
        text-align: center;
        margin-bottom: 20px;
        padding: 12px;
        border-bottom: 3px solid {current_theme["accent"]};
        background-color: {current_theme["card"]};
        border-radius: 10px;
    }}
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid {current_theme["border"]} !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {current_theme["card"]} !important;
        border-right: 1px solid {current_theme["border"]} !important;
    }}
    .stButton>button {{
        background-color: {current_theme["primary"]} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. تهيئة قاعدة البيانات والأمان
# ==========================================
def get_db_connection():
    return sqlite3.connect("mh_group_erp.db", timeout=20)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip_address TEXT,
            login_time TEXT,
            last_activity TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, location TEXT, price REAL, status TEXT, type TEXT, finishing TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER, expense_type TEXT, amount REAL, notes TEXT, date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
            hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
            workers_count INTEGER DEFAULT 1, craft_type TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT, notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, category TEXT, status TEXT, created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT, category TEXT, upload_date TEXT, file_data BLOB, file_type TEXT
        )
    """)

    cursor.execute("SELECT * FROM users WHERE LOWER(TRIM(username)) = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
        )

    conn.commit()
    conn.close()


init_db()


def safe_read_sql(query, params=()):
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def get_user_ip():
    try:
        ctx = st.context
        if hasattr(ctx, "headers") and "X-Forwarded-For" in ctx.headers:
            return ctx.headers["X-Forwarded-For"].split(",")[0]
    except Exception:
        pass
    try:
        return requests.get("https://api.ipify.org", timeout=2).text
    except Exception:
        return "127.0.0.1 (Local)"


def log_session_start(username):
    ip_addr = get_user_ip()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_sessions (username, ip_address, login_time, last_activity, status)
        VALUES (?, ?, ?, ?, 'نشط')
    """,
        (username, ip_addr, now_str, now_str),
    )
    conn.commit()
    conn.close()


# ==========================================
# 3. تسجيل الدخول للجلسات
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "is_developer" not in st.session_state:
    st.session_state["is_developer"] = False
if "profile_pic" not in st.session_state:
    st.session_state["profile_pic"] = None
if "show_forgot_password" not in st.session_state:
    st.session_state["show_forgot_password"] = False


def login_page():
    cfg = st.session_state["login_config"]
    st.markdown(f"<h1 class='main-header'>{cfg['title']}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader(cfg["subtitle"])
        st.caption(cfg["welcome_msg"])

        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")

        if st.button(cfg["btn_text"], use_container_width=True):
            clean_username = username_input.strip()
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, username FROM users WHERE LOWER(TRIM(username)) = LOWER(?) AND password = ?",
                (clean_username, password_input),
            )
            res = cursor.fetchone()
            conn.close()

            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0] if res[0] else "Admin"
                st.session_state["username"] = res[1]
                log_session_start(res[1])
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")


# ==========================================
# 4. لوحة ERP والأقسام
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(
        f"**المستخدم:** {st.session_state['username']}\n\n**الصلاحية:** {st.session_state['user_role']}"
    )

    is_admin = st.session_state["user_role"] == "Admin"
    if is_admin:
        st.session_state["is_developer"] = st.sidebar.checkbox(
            "🛠️ وضع المطور (Developer Mode)",
            value=st.session_state["is_developer"],
        )

    all_pages = [
        "📊 لوحة التحكم الرئيسية",
        "👤 الملف الشخصي (Profile)",
        "👥 إدارة المستخدمين والصلاحيات والجلسات",
        "🏡 إدارة العقارات والوحدات",
        "👷 إدارة الموارد البشرية والعمالة",
        "💼 قسم المستثمرين والمالية",
        "💻 قسم تقنية المعلومات (IT Support)",
        "📑 التقارير وإدارة المستندات",
    ]

    page = st.sidebar.radio("القائمة الرئيسية", all_pages)

    if st.sidebar.button("تسجيل الخروج"):
        conn = get_db_connection()
        conn.execute(
            "UPDATE user_sessions SET status = 'مسجل خروج' WHERE username = ? AND status = 'نشط'",
            (st.session_state["username"],),
        )
        conn.commit()
        conn.close()
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 1. Dashboard ---
    if page == "📊 لوحة التحكم الرئيسية":
        st.markdown(
            f"<h1 class='main-header'>{st.session_state['dashboard_config']['header_title']}</h1>",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "إجمالي العقارات",
            f"{len(safe_read_sql('SELECT id FROM properties'))} وحدة",
        )
        c2.metric(
            "العمالة والموظفين",
            f"{len(safe_read_sql('SELECT id FROM employees'))} فرد",
        )
        inv_sum = (
            safe_read_sql(
                "SELECT SUM(investment_amount) as s FROM investors"
            )["s"].fillna(0)[0]
            if not safe_read_sql(
                "SELECT SUM(investment_amount) as s FROM investors"
            ).empty
            else 0
        )
        c3.metric("حجم الاستثمارات", f"{inv_sum:,.0f} EGP")

    # --- 3. Users Management (Fixed) ---
    elif page == "👥 إدارة المستخدمين والصلاحيات والجلسات":
        st.title("👥 إدارة المستخدمين")
        tab1, tab2 = st.tabs(["📋 القائمة", "➕ إضافة مستخدم"])

        with tab1:
            st.dataframe(
                safe_read_sql(
                    "SELECT id, username, role, phone FROM users"
                ),
                use_container_width=True,
            )

        with tab2:
            if "u_msg_succ" in st.session_state:
                st.success(st.session_state.pop("u_msg_succ"))
            if "u_msg_err" in st.session_state:
                st.error(st.session_state.pop("u_msg_err"))

            if "form_key_u" not in st.session_state:
                st.session_state["form_key_u"] = 0

            with st.form(f"add_user_f_{st.session_state['form_key_u']}"):
                u_n = st.text_input("اسم المستخدم")
                u_p = st.text_input("كلمة المرور", type="password")
                u_ph = st.text_input("رقم الهاتف")
                u_r = st.selectbox(
                    "الصلاحية", ["Admin", "Manager", "HR", "IT", "Accountant"]
                )

                if st.form_submit_button("إضافة المستخدم"):
                    clean_u = u_n.strip()
                    if clean_u and u_p.strip():
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(?)",
                            (clean_u,),
                        )
                        if cursor.fetchone():
                            st.session_state["u_msg_err"] = (
                                f"❌ المستخدم '{clean_u}' موجود بالفعل!"
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                (clean_u, u_p.strip(), u_r, u_ph.strip()),
                            )
                            conn.commit()
                            st.session_state["u_msg_succ"] = (
                                f"✅ تم إضافة '{clean_u}' بنجاح!"
                            )
                        conn.close()
                        st.session_state["form_key_u"] += 1
                        st.rerun()
                    else:
                        st.error("يرجى ملء كافة الحقول!")

    # --- 6. Investors & Finance (FIXED OperationalError) ---
    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 إدارة المستثمرين والأرباح والمالية")
        tab1, tab2 = st.tabs(["➕ إضافة مستثمر", "📊 حاسبة الأرباح وسجل الاستثمار"])

        with tab1:
            if "inv_msg_succ" in st.session_state:
                st.success(st.session_state.pop("inv_msg_succ"))
            if "inv_msg_err" in st.session_state:
                st.error(st.session_state.pop("inv_msg_err"))

            if "inv_form_key" not in st.session_state:
                st.session_state["inv_form_key"] = 0

            with st.form(f"add_inv_form_{st.session_state['inv_form_key']}"):
                inv_name = st.text_input("اسم المستثمر")
                inv_amount = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                inv_rate = st.number_input("نسبة الربح السنوية (%)", min_value=0.0)
                inv_notes = st.text_input("ملاحظات")

                if st.form_submit_button("إضافة المستثمر"):
                    if inv_name.strip() and inv_amount > 0:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO investors (name, investment_amount, return_rate, start_date, notes)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                                (
                                    inv_name.strip(),
                                    float(inv_amount),
                                    float(inv_rate),
                                    str(datetime.date.today()),
                                    inv_notes.strip(),
                                ),
                            )
                            conn.commit()
                            conn.close()

                            st.session_state["inv_msg_succ"] = (
                                f"✅ تم حفظ المستثمر {inv_name} بنجاح!"
                            )
                            st.session_state["inv_form_key"] += 1
                            st.rerun()
                        except Exception as e:
                            st.session_state["inv_msg_err"] = (
                                f"❌ تعذر الحفظ لقاعدة البيانات: {e}"
                            )
                            st.session_state["inv_form_key"] += 1
                            st.rerun()
                    else:
                        st.error("يرجى كتابة اسم المستثمر ومبلغ أكبر من صفر!")

        with tab2:
            st.subheader("📊 سجل المستثمرين وحساب الأرباح")
            inv_df = safe_read_sql("SELECT * FROM investors")
            if not inv_df.empty:
                inv_df["الأرباح السنوية المتوقعة"] = (
                    inv_df["investment_amount"] * (inv_df["return_rate"] / 100.0)
                )
                st.dataframe(inv_df, use_container_width=True)
            else:
                st.info("لا يوجد مستثمرون مسجلون حالياً.")
