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
# 1. قائمة الثيمات مع جعل "الداكن الملكي" هو الأساسي
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
    "عنابي فاخر (Burgundy Premium)": {
        "primary": "#881337",
        "bg": "#FFF1F2",
        "card": "#FFFFFF",
        "text": "#4C0519",
        "accent": "#E11D48",
        "border": "#FFE4E6",
    },
    "الليل والسيبربانك (Cyberpunk Neon)": {
        "primary": "#06B6D4",
        "bg": "#0B0F19",
        "card": "#111827",
        "text": "#F3F4F6",
        "accent": "#A855F7",
        "border": "#1F2937",
    },
}

# --- تهيئة الصفحة ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تعيين الثيم الأساسي تلقائياً إلى "الداكن الملكي والذهبي"
if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = (
        "الداكن الملكي والذهبي (Royal Dark & Gold)"
    )

current_theme = THEMES[st.session_state["selected_theme"]]

# --- إعدادات الجلسات المتطورة ---
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

# --- تطبيق CSS للمظهر العام ---
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
# 2. تهيئة قاعدة البيانات والترقية التلقائية
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
        cursor = conn.cursor()

        # 1. جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)

        # 2. جدول جلسات الدخول والأنشطة (IP Tracking)
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

        # 3. جدول العقارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, location TEXT, price REAL, status TEXT, type TEXT, finishing TEXT
            )
        """)

        # 4. جدول مصاريف العقارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER, expense_type TEXT, amount REAL, notes TEXT, date TEXT,
                FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # 5. جدول الموظفين والعمالة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
                hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
                workers_count INTEGER DEFAULT 1, craft_type TEXT
            )
        """)

        # 6. جدول المستثمرين والمالية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT, notes TEXT
            )
        """)

        # 7. جدول IT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, category TEXT, status TEXT, created_at TEXT
            )
        """)

        # 8. جدول المستندات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT, category TEXT, upload_date TEXT, file_data BLOB, file_type TEXT
            )
        """)

        # التأكد من وجود حساب admin الأساسي
        cursor.execute(
            "SELECT * FROM users WHERE LOWER(TRIM(username)) = 'admin'"
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
            )

        conn.commit()


init_db()


def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
            return pd.read_sql_query(query, conn, params=params)
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
    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions (username, ip_address, login_time, last_activity, status)
            VALUES (?, ?, ?, ?, 'نشط')
        """,
            (username, ip_addr, now_str, now_str),
        )
        conn.commit()


def send_real_sms(phone_number, code):
    sms_user = st.secrets.get("SMS_USER", "YOUR_USER")
    sms_pass = st.secrets.get("SMS_PASS", "YOUR_PASS")
    sms_sender = st.secrets.get("SMS_SENDER", "MHGroup")

    url = "https://smsmisr.com/api/SMS/"
    payload = {
        "environment": "1",
        "username": sms_user,
        "password": sms_pass,
        "language": "2",
        "sender": sms_sender,
        "mobile": phone_number,
        "message": f"كود التحقق الخاص بك بنظام MH Group ERP هو: {code}",
    }
    try:
        requests.post(url, data=payload, timeout=8)
        return True
    except Exception:
        return False


# ==========================================
# 3. إدارة الجلسات والدخول
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
if "reset_stage" not in st.session_state:
    st.session_state["reset_stage"] = "request"
if "otp_code" not in st.session_state:
    st.session_state["otp_code"] = None
if "reset_username" not in st.session_state:
    st.session_state["reset_username"] = ""


def login_page():
    cfg = st.session_state["login_config"]
    st.markdown(f"<h1 class='main-header'>{cfg['title']}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if cfg.get("logo_bytes"):
            st.image(cfg["logo_bytes"], use_container_width=True)

        st.subheader(cfg["subtitle"])
        st.caption(cfg["welcome_msg"])

        if not st.session_state["show_forgot_password"]:
            username_input = st.text_input("اسم المستخدم")
            password_input = st.text_input("كلمة المرور", type="password")

            btn_col1, btn_col2 = st.columns([2, 1])
            with btn_col1:
                login_btn = st.button(cfg["btn_text"], use_container_width=True)
            with btn_col2:
                if st.button("نسيت كلمة السر؟", use_container_width=True):
                    st.session_state["show_forgot_password"] = True
                    st.session_state["reset_stage"] = "request"
                    st.rerun()

            if login_btn:
                clean_username = username_input.strip()
                try:
                    init_db()
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT role, username FROM users WHERE LOWER(TRIM(username)) = LOWER(?) AND password = ?",
                            (clean_username, password_input),
                        )
                        res = cursor.fetchone()

                    if res:
                        st.session_state["logged_in"] = True
                        st.session_state["user_role"] = (
                            res[0] if res[0] else "Admin"
                        )
                        st.session_state["username"] = res[1]

                        log_session_start(res[1])

                        st.success("تم تسجيل الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الاتصال: {e}")

            # --- أزرار تسجيل الدخول الموحد (SSO) ---
            st.markdown("---")
            st.markdown(
                "<p style='text-align: center; color: gray;'>أو يمكنك الدخول باستخدام:</p>",
                unsafe_allow_html=True,
            )

            col_sso1, col_sso2 = st.columns(2)
            with col_sso1:
                if cfg.get("google_enabled", True):
                    if st.button("🌐 Google Account", use_container_width=True):
                        st.info("🔄 جاري التوجيه لبوابة Google OAuth...")

            with col_sso2:
                if cfg.get("microsoft_enabled", True):
                    if st.button("🏢 Microsoft 365", use_container_width=True):
                        st.info("🔄 جاري التوجيه لبوابة Microsoft OAuth...")

        else:
            st.info("📱 استعادة كلمة السر عبر كود SMS")
            if st.session_state["reset_stage"] == "request":
                rec_username = st.text_input("اسم المستخدم:")
                rec_phone = st.text_input("رقم الهاتف المسجل للحساب:")

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("إرسال كود التحقق (SMS)", use_container_width=True):
                        clean_rec = rec_username.strip()
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT phone FROM users WHERE LOWER(TRIM(username)) = LOWER(?)",
                                (clean_rec,),
                            )
                            user_row = cursor.fetchone()

                        if user_row and (
                            user_row[0] == rec_phone.strip() or not user_row[0]
                        ):
                            generated_otp = str(random.randint(100000, 999999))
                            st.session_state["otp_code"] = generated_otp
                            st.session_state["reset_username"] = clean_rec

                            send_real_sms(rec_phone.strip(), generated_otp)
                            st.session_state["reset_stage"] = "verify"
                            st.success("تم إرسال كود التحقق إلى هاتفك المحمول.")
                            st.rerun()
                        else:
                            st.error("اسم المستخدم أو رقم الهاتف غير مطابق!")

                with col_r2:
                    if st.button("إلغاء", use_container_width=True):
                        st.session_state["show_forgot_password"] = False
                        st.rerun()

            elif st.session_state["reset_stage"] == "verify":
                st.write(
                    f"تم إرسال كود SMS إلى هاتفك المسجل باسم **{st.session_state['reset_username']}**."
                )
                user_otp = st.text_input(
                    "أدخل كود التحقق المكون من 6 أرقام:",
                    max_chars=6,
                    type="password",
                )

                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    if st.button("تأكيد الكود", use_container_width=True):
                        if user_otp == st.session_state["otp_code"]:
                            st.success("✅ الكود صحيح! انتقلت لصفحة تعيين كلمة السر.")
                            st.session_state["reset_stage"] = "new_pass"
                            st.rerun()
                        else:
                            st.error("❌ الكود غير صحيح! يرجى إعادة المحاولة.")

                with col_v2:
                    if st.button("إلغاء", use_container_width=True):
                        st.session_state["show_forgot_password"] = False
                        st.session_state["reset_stage"] = "request"
                        st.rerun()

            elif st.session_state["reset_stage"] == "new_pass":
                new_reset_pass = st.text_input("كلمة السر الجديدة:", type="password")
                confirm_reset_pass = st.text_input(
                    "تأكيد كلمة السر الجديدة:", type="password"
                )

                if st.button("حفظ كلمة السر الجديدة", use_container_width=True):
                    if not new_reset_pass:
                        st.error("يرجى كتابة كلمة السر!")
                    elif new_reset_pass != confirm_reset_pass:
                        st.error("كلمتا المرور غير متطابقتين!")
                    else:
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET password = ? WHERE LOWER(TRIM(username)) = LOWER(?)",
                                (new_reset_pass, st.session_state["reset_username"]),
                            )
                            conn.commit()
                        st.success("✅ تم تحديث كلمة السر بنجاح!")
                        st.session_state["show_forgot_password"] = False
                        st.session_state["reset_stage"] = "request"
                        st.rerun()


# ==========================================
# 4. التطبيق الرئيسي والأقسام بكامل محتواها
# ==========================================
if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")

    if st.session_state["profile_pic"]:
        st.sidebar.image(st.session_state["profile_pic"], width=90)

    st.sidebar.markdown(
        f"**المستخدم:** {st.session_state['username']}\n\n**الصلاحية:** {st.session_state['user_role']}"
    )

    is_admin = st.session_state["user_role"] == "Admin"

    if is_admin:
        dev_toggle = st.sidebar.checkbox(
            "🛠️ وضع المطور (Developer Mode)",
            value=st.session_state["is_developer"],
        )
        st.session_state["is_developer"] = dev_toggle
    else:
        st.session_state["is_developer"] = False

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

    if is_admin:
        all_pages.append("⚙️ إعدادات المطور والثيمات")

    current_role = st.session_state["user_role"]

    if st.session_state["is_developer"] or is_admin:
        menu_options = all_pages
    else:
        menu_options = ["👤 الملف الشخصي (Profile)"]
        if current_role == "HR":
            menu_options.extend(
                ["👷 إدارة الموارد البشرية والعمالة", "📑 التقارير وإدارة المستندات"]
            )
        elif current_role == "Manager":
            menu_options.extend(
                ["🏡 إدارة العقارات والوحدات", "📑 التقارير وإدارة المستندات"]
            )
        elif current_role == "Accountant":
            menu_options.extend(
                ["💼 قسم المستثمرين والمالية", "📑 التقارير وإدارة المستندات"]
            )
        elif current_role == "IT":
            menu_options.extend(["💻 قسم تقنية المعلومات (IT Support)"])

    page = st.sidebar.radio("القائمة الرئيسية", menu_options)

    if st.sidebar.button("تسجيل الخروج"):
        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
            conn.execute(
                "UPDATE user_sessions SET status = 'مسجل خروج' WHERE username = ? AND status = 'نشط'",
                (st.session_state["username"],),
            )
            conn.commit()
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 1. Dashboard ---
    if page == "📊 لوحة التحكم الرئيسية":
        dash_cfg = st.session_state["dashboard_config"]
        st.markdown(
            f"<h1 class='main-header'>{dash_cfg['header_title']}</h1>",
            unsafe_allow_html=True,
        )
        st.info(dash_cfg["custom_note"])

        if dash_cfg["show_metrics"]:
            prop_df = safe_read_sql("SELECT COUNT(*) as count FROM properties")
            prop_count = prop_df["count"][0] if not prop_df.empty else 0

            emp_df = safe_read_sql("SELECT COUNT(*) as count FROM employees")
            emp_count = emp_df["count"][0] if not emp_df.empty else 0

            inv_df = safe_read_sql(
                "SELECT SUM(investment_amount) as sum FROM investors"
            )
            total_inv = (
                inv_df["sum"][0]
                if (not inv_df.empty and inv_df["sum"][0] is not None)
                else 0
            )

            exp_df = safe_read_sql(
                "SELECT SUM(amount) as sum FROM property_expenses"
            )
            total_exp = (
                exp_df["sum"][0]
                if (not exp_df.empty and exp_df["sum"][0] is not None)
                else 0
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("إجمالي العقارات المسجلة", f"{prop_count} وحدة")
            c2.metric("إجمالي العمالة والموظفين", f"{emp_count} فرد")
            c3.metric("حجم الاستثمارات", f"{total_inv:,.0f} EGP")
            c4.metric("مصاريف العقارات", f"{total_exp:,.0f} EGP")

        st.markdown("---")
        st.subheader("📌 التفاصيل السريعة للأقسام")
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("### 👷 ملخص العمالة والموظفين")
            emp_summary = safe_read_sql(
                "SELECT emp_type as الفئة, COUNT(*) as العدد FROM employees GROUP BY emp_type"
            )
            st.dataframe(emp_summary, use_container_width=True)

        with col_b:
            st.markdown("### 🏡 ملخص حالة العقارات")
            prop_summary = safe_read_sql(
                "SELECT status as الحالة, COUNT(*) as العدد FROM properties GROUP BY status"
            )
            st.dataframe(prop_summary, use_container_width=True)

    # --- 2. Profile ---
    elif page == "👤 الملف الشخصي (Profile)":
        st.title("👤 إدارة الملف الشخصي والحساب")
        col_img, col_info = st.columns([1, 2])

        with col_img:
            st.markdown("### 🖼️ الصورة الشخصية")
            if st.session_state["profile_pic"]:
                st.image(
                    st.session_state["profile_pic"],
                    width=180,
                    caption="الصورة الحالية",
                )
            else:
                st.info("لم يتم رفع صورة شخصية بعد.")

            uploaded_pic = st.file_uploader(
                "رفع / تغيير الصورة", type=["jpg", "png", "jpeg"]
            )
            if uploaded_pic:
                st.session_state["profile_pic"] = uploaded_pic.getvalue()
                st.success("تم تحديث الصورة الشخصية بنجاح!")
                st.rerun()

        with col_info:
            st.markdown("### ✏️ تعديل البيانات الشخصية")
            user_data = safe_read_sql(
                "SELECT phone FROM users WHERE username = ?",
                (st.session_state["username"],),
            )
            curr_phone = (
                user_data["phone"][0]
                if not user_data.empty and user_data["phone"][0]
                else ""
            )

            with st.form("edit_profile_form"):
                new_username = st.text_input(
                    "اسم المستخدم الحالي:", value=st.session_state["username"]
                )
                new_phone = st.text_input(
                    "رقم الهاتف (لأكواد الاستعادة SMS):", value=curr_phone
                )

                if st.form_submit_button("حفظ التعديلات"):
                    clean_new_username = new_username.strip()
                    try:
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET username = ?, phone = ? WHERE username = ?",
                                (
                                    clean_new_username,
                                    new_phone.strip(),
                                    st.session_state["username"],
                                ),
                            )
                            conn.commit()

                        st.session_state["username"] = clean_new_username
                        st.success("تم تحديث البيانات بنجاح!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم الجديد مستخدم بالفعل!")

            st.markdown("---")
            st.markdown("### 🌐 معلومات الجلسة الحالية")
            st.write(f"**IP الجهاز الحالي:** `{get_user_ip()}`")
            st.write(
                f"**تاريخ/وقت الدخول:** `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

    # --- 3. Users & Sessions Management ---
    elif page == "👥 إدارة المستخدمين والصلاحيات والجلسات":
        st.title("👥 إدارة المستخدمين والجلسات النشطة")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "🌐 الجلسات وعناوين IP",
                "➕ إضافة مستخدم",
                "✏️ تعديل مستخدم",
                "📋 قائمة المستخدمين",
                "❌ حذف مستخدم",
            ]
        )

        with tab1:
            st.subheader("🌐 سجل الجلسات المفتوحة وعناوين الـ IP")
            sessions_df = safe_read_sql(
                "SELECT id as ID, username as المستخدم, ip_address as 'عنوان IP', login_time as 'تاريخ الدخول', status as الحالة FROM user_sessions ORDER BY id DESC LIMIT 50"
            )
            st.dataframe(sessions_df, use_container_width=True)

        with tab2:
            st.subheader("➕ إضافة مستخدم جديد")

            # عرض التنبيهات من الجلسة في بداية التبويب لإظهار نتيجة العملية السابقة
            if "user_msg_success" in st.session_state:
                st.success(st.session_state.pop("user_msg_success"))
            if "user_msg_error" in st.session_state:
                st.error(st.session_state.pop("user_msg_error"))

            with st.form("add_new_user_form_v2", clear_on_submit=True):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_phone = st.text_input("رقم الهاتف")
                u_role = st.selectbox(
                    "الصلاحية المحددة",
                    ["Admin", "Manager", "HR", "IT", "Accountant"],
                )

                submit_user_btn = st.form_submit_button("إضافة المستخدم")

                if submit_user_btn:
                    clean_username = u_name.strip()
                    clean_pass = u_pass.strip()

                    if clean_username and clean_pass:
                        try:
                            with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(?)",
                                    (clean_username,),
                                )
                                existing_user = cursor.fetchone()

                                if existing_user:
                                    st.session_state["user_msg_error"] = (
                                        f"❌ المستخدم '{clean_username}' موجود بالفعل في قاعدة البيانات!"
                                    )
                                else:
                                    cursor.execute(
                                        "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                        (
                                            clean_username,
                                            clean_pass,
                                            u_role,
                                            u_phone.strip(),
                                        ),
                                    )
                                    conn.commit()
                                    st.session_state["user_msg_success"] = (
                                        f"✅ تم إضافة المستخدم '{clean_username}' بنجاح!"
                                    )

                                st.rerun()

                        except sqlite3.IntegrityError:
                            st.session_state["user_msg_error"] = (
                                "❌ اسم المستخدم مسجل مسبقاً!"
                            )
                            st.rerun()
                        except Exception as e:
                            st.session_state["user_msg_error"] = (
                                f"حدث خطأ أثناء الحفظ: {e}"
                            )
                            st.rerun()
                    else:
                        st.error("يرجى إدخال اسم المستخدم وكلمة المرور!")

        with tab3:
            users_list_df = safe_read_sql(
                "SELECT id, username, role, phone FROM users"
            )
            if not users_list_df.empty:
                selected_user_edit = st.selectbox(
                    "اختر المستخدم للتعديل:", users_list_df["username"]
                )
                u_row = users_list_df[
                    users_list_df["username"] == selected_user_edit
                ].iloc[0]

                role_options = ["Admin", "Manager", "HR", "IT", "Accountant"]
                current_user_role = str(u_row["role"]).strip()
                default_role_index = (
                    role_options.index(current_user_role)
                    if current_user_role in role_options
                    else 0
                )

                with st.form("edit_user_admin_form"):
                    e_role = st.selectbox(
                        "الصلاحية الجديدة:",
                        role_options,
                        index=default_role_index,
                    )
                    e_phone = st.text_input(
                        "رقم الهاتف:", value=str(u_row["phone"] or "")
                    )
                    e_pass = st.text_input(
                        "كلمة مرور جديدة (اتركها فارغة للتجاهل):", type="password"
                    )

                    if st.form_submit_button("حفظ التعديلات"):
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET role = ?, phone = ? WHERE username = ?",
                                (e_role, e_phone.strip(), selected_user_edit),
                            )
                            if e_pass:
                                cursor.execute(
                                    "UPDATE users SET password = ? WHERE username = ?",
                                    (e_pass, selected_user_edit),
                                )
                            conn.commit()
                        st.success(f"تم تحديث بيانات {selected_user_edit} بنجاح!")
                        st.rerun()

        with tab4:
            st.subheader("📋 جميع المستخدمين المسجلين")
            all_users_df = safe_read_sql(
                "SELECT id as ID, username as 'اسم المستخدم', role as الصلاحية, phone as 'رقم الهاتف' FROM users"
            )
            st.dataframe(all_users_df, use_container_width=True)

        with tab5:
            users_df = safe_read_sql(
                "SELECT id, username FROM users WHERE LOWER(TRIM(username)) != 'admin'"
            )
            if not users_df.empty:
                del_user = st.selectbox(
                    "اختر المستخدم للحذف:", users_df["username"]
                )
                if st.button("حذف الحساب المحدد"):
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        conn.execute(
                            "DELETE FROM users WHERE username = ?", (del_user,)
                        )
                        conn.commit()
                    st.success(f"تم حذف الحساب {del_user}")
                    st.rerun()

    # --- 4. Properties ---
    elif page == "🏡 إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات والمصاريف")
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📋 قائمة العقارات",
                "➕ إضافة عقار",
                "💸 مصاريف العقارات",
                "❌ حذف عقار",
            ]
        )

        with tab1:
            st.dataframe(
                safe_read_sql("SELECT * FROM properties"), use_container_width=True
            )

        with tab2:
            with st.form("add_prop", clear_on_submit=True):
                p_name = st.text_input("اسم العقار / الوحدة")
                p_type = st.selectbox(
                    "نوع العقار:",
                    ["شقة", "فيلا", "محل تجاري", "أرض", "مبنى كامل", "مكتب"],
                )
                p_loc = st.text_input("الموقع")
                p_price = st.number_input("السعر المقدر / الكلي", min_value=0.0)
                p_finishing = st.selectbox(
                    "نوع التشطيب:",
                    ["بدون تشطيب", "لوكس", "سوبر لوكس", "ألترا سوبر لوكس"],
                )
                p_stat = st.selectbox(
                    "الحالة", ["متاح", "تم البيع", "تحت الإنشاء", "محجوز"]
                )

                if st.form_submit_button("حفظ العقار"):
                    if p_name.strip():
                        try:
                            with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                                conn.execute(
                                    "INSERT INTO properties (name, location, price, status, type, finishing) VALUES (?, ?, ?, ?, ?, ?)",
                                    (
                                        p_name.strip(),
                                        p_loc,
                                        float(p_price),
                                        p_stat,
                                        p_type,
                                        p_finishing,
                                    ),
                                )
                                conn.commit()
                            st.success("تم إضافة العقار بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء الحفظ: {e}")
                    else:
                        st.error("يرجى إدخال اسم العقار!")

        with tab3:
            props_df = safe_read_sql("SELECT id, name FROM properties")
            if not props_df.empty:
                with st.form("add_expense_form", clear_on_submit=True):
                    selected_p_id = st.selectbox(
                        "اختر العقار:",
                        props_df["id"],
                        format_func=lambda x: props_df[props_df["id"] == x][
                            "name"
                        ].values[0],
                    )
                    exp_type = st.selectbox(
                        "نوع المصاريف / التشطيب:",
                        [
                            "دهانات",
                            "نجارة",
                            "كهرباء",
                            "سباكة",
                            "محارة وتأسيس",
                            "سيراميك وأرضيات",
                            "رسوم وإجراءات قانونية",
                            "أخرى",
                        ],
                    )
                    exp_amount = st.number_input("المبلغ (EGP):", min_value=0.0)
                    exp_notes = st.text_input("ملاحظات / بيان المصروف:")

                    if st.form_submit_button("تسجيل المصروف"):
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            conn.execute(
                                "INSERT INTO property_expenses (property_id, expense_type, amount, notes, date) VALUES (?, ?, ?, ?, ?)",
                                (
                                    selected_p_id,
                                    exp_type,
                                    float(exp_amount),
                                    exp_notes,
                                    str(datetime.date.today()),
                                ),
                            )
                            conn.commit()
                        st.success("تم تسجيل المصروف بنجاح!")
                        st.rerun()

            exp_list = safe_read_sql("""
                SELECT pe.id, p.name as العقار, pe.expense_type as النوع, pe.amount as المبلغ, pe.notes as ملاحظات, pe.date as التاريخ
                FROM property_expenses pe
                JOIN properties p ON pe.property_id = p.id
            """)
            st.markdown("### 📊 سجّل المصروفات")
            st.dataframe(exp_list, use_container_width=True)

        with tab4:
            props_df = safe_read_sql("SELECT id, name FROM properties")
            if not props_df.empty:
                del_id = st.selectbox(
                    "اختر العقار للحذف",
                    props_df["id"],
                    format_func=lambda x: props_df[props_df["id"] == x][
                        "name"
                    ].values[0],
                )
                if st.button("حذف العقار"):
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        conn.execute("DELETE FROM properties WHERE id = ?", (del_id,))
                        conn.commit()
                    st.success("تم حذف العقار المحدد.")
                    st.rerun()

    # --- 5. HR & Workers ---
    elif page == "👷 إدارة الموارد البشرية والعمالة":
        st.title("👷 إدارة الموارد البشرية والعمالة والمستحقات")
        tab1, tab2, tab3 = st.tabs(
            [
                "➕ تسجيل موظف/عمالة",
                "📊 قائمة الموظفين وحاسبة المستحقات",
                "❌ حذف سجل",
            ]
        )

        with tab1:
            with st.form("add_emp_form", clear_on_submit=True):
                e_name = st.text_input("الاسم الكامل")
                e_type = st.selectbox(
                    "نوع الفئة:", ["موظف ثابت", "عمالة مؤقتة (بالساعة/اليومية)"]
                )
                e_pos = st.text_input("المسمى الوظيفي / الحرفة")

                c1, c2 = st.columns(2)
                with c1:
                    e_pay_type = st.selectbox(
                        "طريقة الاحتساب:", ["راتب شهري", "أجر بالساعة", "أجر يومي"]
                    )
                    e_hourly_rate = st.number_input(
                        "سعر الساعة / اليوم (إن وجد):", min_value=0.0
                    )
                with c2:
                    e_hours_worked = st.number_input(
                        "عدد الساعات / الأيام المنجزة:", min_value=0.0
                    )
                    e_workers_cnt = st.number_input(
                        "عدد العمال (إن كان طاقم):", min_value=1, value=1
                    )

                e_total_pay = e_hourly_rate * e_hours_worked * e_workers_cnt

                st.info(f"💵 إجمالي المستحق المحسوب: {e_total_pay:,.2f} EGP")

                if st.form_submit_button("حفظ الموظف / العمالة"):
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        conn.execute(
                            """
                            INSERT INTO employees (name, emp_type, position, pay_type, hourly_rate, hours_worked, total_pay, hire_date, workers_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                e_name,
                                e_type,
                                e_pos,
                                e_pay_type,
                                e_hourly_rate,
                                e_hours_worked,
                                e_total_pay,
                                str(datetime.date.today()),
                                e_workers_cnt,
                            ),
                        )
                        conn.commit()
                    st.success("تم حفظ البيانات بنجاح!")
                    st.rerun()

        with tab2:
            st.dataframe(
                safe_read_sql("SELECT * FROM employees"), use_container_width=True
            )

        with tab3:
            emps = safe_read_sql("SELECT id, name FROM employees")
            if not emps.empty:
                del_e_id = st.selectbox(
                    "اختر الموظف للحذف:",
                    emps["id"],
                    format_func=lambda x: emps[emps["id"] == x]["name"].values[0],
                )
                if st.button("حذف الموظف"):
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        conn.execute("DELETE FROM employees WHERE id = ?", (del_e_id,))
                        conn.commit()
                    st.success("تم الحذف بنجاح!")
                    st.rerun()

    # --- 6. Finance & Investors ---
    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 إدارة المستثمرين والأرباح والمالية")
        tab1, tab2 = st.tabs(["➕ إضافة مستثمر", "📊 حاسبة الأرباح وسجل الاستثمار"])

        with tab1:
            with st.form("add_inv", clear_on_submit=True):
                inv_name = st.text_input("اسم المستثمر")
                inv_amount = st.number_input("مبلغ الاستثمار (EGP)", min_value=0.0)
                inv_rate = st.number_input("نسبة الربح السنوية (%)", min_value=0.0)
                inv_notes = st.text_input("ملاحظات")

                if st.form_submit_button("إضافة المستثمر"):
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        conn.execute(
                            "INSERT INTO investors (name, investment_amount, return_rate, start_date, notes) VALUES (?, ?, ?, ?, ?)",
                            (
                                inv_name,
                                inv_amount,
                                inv_rate,
                                str(datetime.date.today()),
                                inv_notes,
                            ),
                        )
                        conn.commit()
                    st.success("تم تسحيل المستثمر بنجاح!")
                    st.rerun()

        with tab2:
            inv_df = safe_read_sql("SELECT * FROM investors")
            if not inv_df.empty:
                inv_df["الأرباح السنوية المتوقعة"] = (
                    inv_df["investment_amount"] * (inv_df["return_rate"] / 100.0)
                )
                st.dataframe(inv_df, use_container_width=True)
            else:
                st.info("لا يوجد مستثمرون مسجلون حالياً.")

    # --- 7. IT Support ---
    elif page == "💻 قسم تقنية المعلومات (IT Support)":
        st.title("💻 الدعم الفني وتذاكر IT")
        tab1, tab2 = st.tabs(["➕ إنشاء تذكرة دعم", "📋 التذاكر الحالية"])

        with tab1:
            with st.form("add_ticket", clear_on_submit=True):
                t_title = st.text_input("عنوان المشكلة / الطلب")
                t_cat = st.selectbox(
                    "التصنيف:",
                    [
                        "شبكات وإنترنت",
                        "أجهزة ومعدات",
                        "برمجيات وحسابات",
                        "أخرى",
                    ],
                )
                if st.form_submit_button("إرسال التذكرة"):
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        conn.execute(
                            "INSERT INTO it_tickets (title, category, status, created_at) VALUES (?, ?, ?, ?)",
                            (
                                t_title,
                                t_cat,
                                "مفتوحة",
                                str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                            ),
                        )
                        conn.commit()
                    st.success("تم إرسال التذكرة بنجاح!")
                    st.rerun()

        with tab2:
            st.dataframe(
                safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True
            )

    # --- 8. Documents & Reports ---
    elif page == "📑 التقارير وإدارة المستندات":
        st.title("📑 الأرشيف الرقمي وإدارة المستندات")
        tab1, tab2 = st.tabs(["📤 رفع مستند جديد", "📂 الأرشيف والمستندات"])

        with tab1:
            up_file = st.file_uploader("اختر الملف لرفعه لغرض الأرشيف")
            doc_cat = st.selectbox(
                "تصنيف المستند:",
                ["عقود ورخص", "فواتير ومستندات مالية", "هويات وعمالة", "أخرى"],
            )

            if st.button("حفظ الملف بالأرشيف") and up_file:
                bytes_data = up_file.getvalue()
                with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                    conn.execute(
                        "INSERT INTO documents (file_name, category, upload_date, file_data, file_type) VALUES (?, ?, ?, ?, ?)",
                        (
                            up_file.name,
                            doc_cat,
                            str(datetime.date.today()),
                            bytes_data,
                            up_file.type,
                        ),
                    )
                    conn.commit()
                st.success("تم حفظ المستند بالأرشيف بنجاح!")
                st.rerun()

        with tab2:
            docs_df = safe_read_sql(
                "SELECT id, file_name, category, upload_date, file_type FROM documents"
            )
            st.dataframe(docs_df, use_container_width=True)

    # --- 9. Developer & Themes Settings ---
    elif page == "⚙️ إعدادات المطور والثيمات":
        st.title("⚙️ إعدادات المطور وتخصيص المظهر")

        st.subheader("🎨 تخصيص المظهر والثيمات")
        theme_choice = st.selectbox(
            "اختر الثيم المطلوب للنظام (الافتراضي هو الداكن الملكي):",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["selected_theme"]),
        )
        if st.button("تطبيق الثيم"):
            st.session_state["selected_theme"] = theme_choice
            st.success("تم تغيير ثيم النظام!")
            st.rerun()

        st.markdown("---")
        st.subheader("🔑 إعدادات دخول Google و Microsoft SSO")
        st.text_input("Google Client ID:")
        st.text_input("Google Client Secret:", type="password")
        st.text_input("Microsoft Client ID:")
        st.text_input("Microsoft Tenant ID:")
        st.button("حفظ مفاتيح OAuth SSO")
