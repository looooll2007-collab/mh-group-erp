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
    .sso-btn-google {{
        background-color: #EA4335 !important;
        color: white !important;
    }}
    .sso-btn-ms {{
        background-color: #00A4EF !important;
        color: white !important;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. تهيئة قاعدة البيانات وقاعدة الجلسات
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

        # 5. جدول الموظفين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
                hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
                workers_count INTEGER DEFAULT 1, craft_type TEXT
            )
        """)

        # 6. جدول المستثمرين
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

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
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


# دالة لجلب IP الجهاز الخاص بالمستخدم
def get_user_ip():
    try:
        # لمحاولة جلب الـ Client IP من الـ Headers
        ctx = st.context
        if hasattr(ctx, "headers") and "X-Forwarded-For" in ctx.headers:
            return ctx.headers["X-Forwarded-For"].split(",")[0]
    except Exception:
        pass
    try:
        # افتراضي عبر API سريع
        return requests.get("https://api.ipify.org", timeout=2).text
    except Exception:
        return "127.0.0.1 (Local)"


# دالة تسجيل بدء الجلسة
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
                    st.rerun()

            if login_btn:
                try:
                    init_db()
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

                        # تسجيل الجلسة والعنوان IP
                        log_session_start(username_input)

                        st.success("تم تسجيل الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الاتصال: {e}")

            # --- أزرار تسجيل الدخول الموحد (Google / Microsoft) ---
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: gray;'>أو يمكنك الدخول باستخدام:</p>", unsafe_allow_html=True)

            col_sso1, col_sso2 = st.columns(2)
            with col_sso1:
                if cfg.get("google_enabled", True):
                    if st.button("🌐 Google Account", use_container_width=True):
                        st.info("🔄 جاري التوجيه لبوابة Google OAuth...")
                        # هنا يتم وضع توجيه رابط Google OAuth الخاص بالمنظمة

            with col_sso2:
                if cfg.get("microsoft_enabled", True):
                    if st.button("🏢 Microsoft 365", use_container_width=True):
                        st.info("🔄 جاري التوجيه لبوابة Microsoft OAuth...")
                        # هنا يتم وضع توجيه رابط Microsoft OAuth الخاص بالمنظمة

        else:
            st.info("📱 استعادة كلمة السر")
            rec_username = st.text_input("اسم المستخدم:")
            if st.button("إرسال كود الاستعادة", use_container_width=True):
                st.success("تم إرسال تعليمات الاستعادة.")
            if st.button("إلغاء", use_container_width=True):
                st.session_state["show_forgot_password"] = False
                st.rerun()


# ==========================================
# 4. التطبيق الرئيسي والأقسام
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
        # تحديث حالة الجلسة
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
            uploaded_pic = st.file_uploader(
                "رفع / تغيير الصورة", type=["jpg", "png", "jpeg"]
            )
            if uploaded_pic:
                st.session_state["profile_pic"] = uploaded_pic.getvalue()
                st.success("تم تحديث الصورة الشخصية!")
                st.rerun()

        with col_info:
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
                "SELECT id, username as المستخدم, ip_address as 'عنوان IP', login_time as 'تاريخ الدخول', status as الحالة FROM user_sessions ORDER BY id DESC LIMIT 50"
            )
            st.dataframe(sessions_df, use_container_width=True)

        with tab2:
            with st.form("add_user_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_phone = st.text_input("رقم الهاتف")
                u_role = st.selectbox(
                    "الصلاحية المحددة",
                    ["Admin", "Manager", "HR", "IT", "Accountant"],
                )
                
                if st.form_submit_button("إضافة المستخدم"):
                    # إزالة المسافات الزائدة من البداية والنهاية
                    clean_username = u_name.strip()
                    
                    if clean_username and u_pass:
                        try:
                            with sqlite3.connect("mh_group_erp.db", timeout=10) as conn:
                                # التحقق أولاً من عدم وجود الاسم بمسافات أو بدون
                                cursor = conn.cursor()
                                cursor.execute("SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(?)", (clean_username,))
                                existing_user = cursor.fetchone()
                                
                                if existing_user:
                                    st.error(f"❌ المستخدم '{clean_username}' موجود بالفعل في قاعدة البيانات!")
                                else:
                                    conn.execute(
                                        "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                        (clean_username, u_pass, u_role, u_phone.strip()),
                                    )
                                    conn.commit()
                                    st.success(f"✅ تم إضافة المستخدم '{clean_username}' بنجاح!")
                                    st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ اسم المستخدم مسجل مسبقاً!")
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

                with st.form("edit_user_admin_form"):
                    e_role = st.selectbox(
                        "الصلاحية الجديدة:",
                        ["Admin", "Manager", "HR", "IT", "Accountant"],
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
            # إظهار كافة المستخدمين بدون استثناء وتنسيق العرض
            all_users_df = safe_read_sql("SELECT id as ID, username as 'اسم المستخدم', role as الصلاحية, phone as 'رقم الهاتف' FROM users")
            st.dataframe(all_users_df, use_container_width=True)

        with tab5:
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
            ]
        )

        with tab1:
            st.subheader("🌐 سجل الجلسات المفتوحة وعناوين الـ IP")
            sessions_df = safe_read_sql(
                "SELECT id, username as المستخدم, ip_address as 'عنوان IP', login_time as 'تاريخ الدخول', status as الحالة FROM user_sessions ORDER BY id DESC LIMIT 50"
            )
            st.dataframe(sessions_df, use_container_width=True)

        with tab2:
            with st.form("add_user_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_phone = st.text_input("رقم الهاتف")
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

                with st.form("edit_user_admin_form"):
                    e_role = st.selectbox(
                        "الصلاحية الجديدة:",
                        ["Admin", "Manager", "HR", "IT", "Accountant"],
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

        with tab4:
            st.dataframe(
                safe_read_sql("SELECT id, username, role, phone FROM users"),
                use_container_width=True,
            )

        with tab5:
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

    # --- باقي الأقسام تعمل بكامل كفاءتها ---
    elif page == "🏡 إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات والمصاريف")
        st.dataframe(
            safe_read_sql("SELECT * FROM properties"), use_container_width=True
        )

    elif page == "👷 إدارة الموارد البشرية والعمالة":
        st.title("👷 إدارة الموارد البشرية والعمالة")
        st.dataframe(
            safe_read_sql("SELECT * FROM employees"), use_container_width=True
        )

    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين والمالية")
        st.dataframe(
            safe_read_sql("SELECT * FROM investors"), use_container_width=True
        )

    elif page == "💻 قسم تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات")
        st.dataframe(
            safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True
        )

    elif page == "📑 التقارير وإدارة المستندات":
        st.title("📑 الأرشيف والمستندات")
        st.dataframe(
            safe_read_sql(
                "SELECT id, file_name, category, upload_date FROM documents"
            ),
            use_container_width=True,
        )

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
