import base64
import datetime
import io
import random
import sqlite3
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. قائمة الثيمات وإعدادات الألوان (Themes)
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

# --- إعدادات الجلسات المتطورة (Session States) ---
if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 نظام إدارة MH Group ERP",
        "subtitle": "🔐 تسجيل الدخول للنظام",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
        "logo_bytes": None,
    }

if "dashboard_config" not in st.session_state:
    st.session_state["dashboard_config"] = {
        "header_title": "📊 لوحة التحكم المتقدمة والملخص العام",
        "show_metrics": True,
        "custom_note": "أهلاً بك في لوحة تحكم النظام العامة. يمكنك متابعة العمليات من هنا.",
    }

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "الداكن الملكي والذهبي (Royal Dark & Gold)"

current_theme = THEMES[st.session_state["selected_theme"]]

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
# 2. تهيئة قاعدة البيانات والتحديث التلقائي
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
        cursor = conn.cursor()

        # 1. إنشاء جدول المستخدمين إن لم يكن موجوداً
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)

        # 2. فحص وإضافة الأعمدة الناقصة لجدول users تلقائياً (Schema Migration)
        cursor.execute("PRAGMA table_info(users)")
        u_cols = [c[1] for c in cursor.fetchall()]

        if "role" not in u_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Admin'")
        if "phone" not in u_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        # 3. التأكد من وجود حساب المسؤول Admin
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
            )
        else:
            # تحديث صلاحية admin للتأكد من عدم وجود قيم فارغة
            cursor.execute(
                "UPDATE users SET role = 'Admin' WHERE username = 'admin' AND (role IS NULL OR role = '')"
            )

        # 4. جدول كلمة سر الأقسام الخاصة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS section_passwords (
                section_name TEXT PRIMARY KEY,
                password TEXT
            )
        """)

        # 5. جدول العقارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, 
                location TEXT, 
                price REAL, 
                status TEXT,
                type TEXT, 
                finishing TEXT
            )
        """)

        cursor.execute("PRAGMA table_info(properties)")
        p_cols = [c[1] for c in cursor.fetchall()]
        required_p_cols = {
            "name": "TEXT",
            "location": "TEXT",
            "price": "REAL",
            "status": "TEXT",
            "type": "TEXT",
            "finishing": "TEXT",
        }
        for col_name, col_type in required_p_cols.items():
            if col_name not in p_cols:
                cursor.execute(
                    f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}"
                )

        # 6. جدول مصاريف العقارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER, expense_type TEXT, amount REAL, notes TEXT, date TEXT,
                FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # 7. جدول الموظفين والعمالة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
                hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
                workers_count INTEGER DEFAULT 1, craft_type TEXT
            )
        """)

        # 8. جدول المستثمرين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
            )
        """)

        # 9. جدول تذاكر IT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, category TEXT, status TEXT, created_at TEXT
            )
        """)

        # 10. جدول المستندات والأرشيف
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT, category TEXT, upload_date TEXT,
                file_data BLOB, file_type TEXT
            )
        """)
        conn.commit()


# تشغيل التهيئة تلقائياً عند تحميل التطبيق
init_db()


def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()


# ==========================================
# 3. دالة إرسال الـ SMS الحقيقية عبر البوابة
# ==========================================
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
        response = requests.post(url, data=payload, timeout=8)
        return True
    except Exception:
        return False


# ==========================================
# 4. إدارة الجلسة والدخول
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


# ==========================================
# 5. شاشة تسجيل الدخول المخصصة
# ==========================================
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
                try:
                    init_db()  # ضمان تحديث الهيكل قبل الاستعلام
                    with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT role FROM users WHERE username = ? AND password = ?",
                            (username_input, password_input),
                        )
                        res = cursor.fetchone()

                    if res:
                        st.session_state["logged_in"] = True
                        st.session_state["user_role"] = (
                            res[0] if res[0] else "Admin"
                        )
                        st.session_state["username"] = username_input
                        st.success("تم تسجيل الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الاتصال: {e}")

        else:
            st.info("📱 استعادة كلمة السر عبر كود SMS")

            if st.session_state["reset_stage"] == "request":
                rec_username = st.text_input("اسم المستخدم:")
                rec_phone = st.text_input("رقم الهاتف المسجل للحساب:")

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("إرسال كود التحقق (SMS)", use_container_width=True):
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT phone FROM users WHERE username = ?",
                                (rec_username,),
                            )
                            user_row = cursor.fetchone()

                        if user_row and (
                            user_row[0] == rec_phone or not user_row[0]
                        ):
                            generated_otp = str(random.randint(100000, 999999))
                            st.session_state["otp_code"] = generated_otp
                            st.session_state["reset_username"] = rec_username

                            send_real_sms(rec_phone, generated_otp)

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
                st.success("🔓 يرجى كتابة كلمة السر الجديدة لتحديث حسابك:")
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
                                "UPDATE users SET password = ? WHERE username = ?",
                                (new_reset_pass, st.session_state["reset_username"]),
                            )
                            conn.commit()
                        st.success("✅ تم تحديث كلمة السر بنجاح!")
                        st.session_state["show_forgot_password"] = False
                        st.session_state["reset_stage"] = "request"
                        st.rerun()


# ==========================================
# 6. لوحة التحكم الرئيسية والأقسام
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
        "👥 إدارة المستخدمين والصلاحيات",
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
                    try:
                        with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET username = ?, phone = ? WHERE username = ?",
                                (
                                    new_username,
                                    new_phone,
                                    st.session_state["username"],
                                ),
                            )
                            conn.commit()

                        st.session_state["username"] = new_username
                        st.success("تم تحديث البيانات بنجاح!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم الجديد مستخدم بالفعل!")

    # --- 3. Users Management ---
    elif page == "👥 إدارة المستخدمين والصلاحيات":
        st.title("👥 إدارة المستخدمين والحسابات")
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "➕ إضافة مستخدم",
                "✏️ تعديل مستخدم",
                "📋 قائمة المستخدمين",
                "❌ حذف مستخدم",
            ]
        )

        with tab1:
            with st.form("add_user_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_phone = st.text_input("رقم الهاتف (لاستقبال كود SMS)")
                u_role = st.selectbox(
                    "الصلاحية المحددة",
                    ["Admin", "Manager", "HR", "IT", "Accountant"],
                )
                if st.form_submit_button("إضافة المستخدم"):
                    if u_name and u_pass:
                        try:
                            with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                                conn.execute(
                                    "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                    (u_name, u_pass, u_role, u_phone),
                                )
                                conn.commit()
                            st.success(f"تم إضافة المستخدم '{u_name}' بنجاح!")
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مسجل مسبقاً!")

        with tab2:
            st.subheader("✏️ تعديل بيانات وصلاحية مستخدم")
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
                                (e_role, e_phone, selected_user_edit),
                            )
                            if e_pass:
                                cursor.execute(
                                    "UPDATE users SET password = ? WHERE username = ?",
                                    (e_pass, selected_user_edit),
                                )
                            conn.commit()
                        st.success(f"تم تحديث بيانات {selected_user_edit} بنجاح!")
                        st.rerun()

        with tab3:
            st.dataframe(
                safe_read_sql("SELECT id, username, role, phone FROM users"),
                use_container_width=True,
            )

        with tab4:
            users_df = safe_read_sql(
                "SELECT id, username FROM users WHERE username != 'admin'"
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
        tab1, tab2, tab3 = st.tabs(
            ["➕ إضافة عقار", "💸 مصاريف العقارات", "❌ حذف عقار"]
        )

        with tab1:
            with st.form("add_prop"):
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
                        st.error("يرجى أدخال اسم العقار!")

        with tab2:
            props_df = safe_read_sql("SELECT id, name FROM properties")
            if not props_df.empty:
                with st.form("add_expense_form"):
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

        with tab3:
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
