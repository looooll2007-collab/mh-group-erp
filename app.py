import base64
import datetime
import io
import random
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        "header_title": "لوحة التحكم",
        "show_metrics": True,
        "custom_note": "مرحباً بك، المدير العام 👋",
    }

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = (
        "الداكن الملكي والذهبي (Royal Dark & Gold)"
    )

current_theme = THEMES[st.session_state["selected_theme"]]

# --- تطبيق CSS المخصص لمطابقة الواجهة في الصورة ---
st.markdown(
    f"""
<style>
    .stApp {{
        background-color: #0d131f !important;
        color: #F8FAFC !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: #111827 !important;
        border-right: 1px solid #1f2937 !important;
    }}
    .stButton>button {{
        background-color: {current_theme["primary"]} !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }}
    
    /* Top Navbar Elements */
    .top-nav {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #111827;
        padding: 10px 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #1f2937;
    }}
    .search-box {{
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 8px;
        color: #9ca3af;
        padding: 6px 15px;
        font-size: 0.85rem;
        width: 300px;
        text-align: center;
    }}
    .user-badge {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    /* Dashboard Metric Cards */
    .metric-card {{
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 16px;
        position: relative;
    }}
    .metric-title {{
        color: #9ca3af;
        font-size: 0.85rem;
        margin-bottom: 5px;
    }}
    .metric-value {{
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
    }}
    .metric-sub {{
        font-size: 0.75rem;
        margin-top: 5px;
    }}
    .badge-green {{
        color: #10b981;
        background: rgba(16, 185, 129, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
    }}
    .badge-red {{
        color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
    }}
    
    /* Table Styling */
    .custom-table-card {{
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 15px;
    }}
    .status-pill {{
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }}
    .status-completed {{ background: rgba(16, 185, 129, 0.2); color: #10b981; }}
    .status-sold {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
    .status-available {{ background: rgba(59, 130, 246, 0.2); color: #3b82f6; }}
    .status-dev {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; }}
    
    /* Activity Item */
    .activity-item {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #1f2937;
    }}
    .activity-title {{ font-size: 0.85rem; font-weight: 600; color: #e5e7eb; }}
    .activity-time {{ font-size: 0.75rem; color: #6b7280; }}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. تهيئة قاعدة البيانات والتحديث التلقائي
# ==========================================
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        # جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)

        # جدول كلمة سر الأقسام الخاصة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS section_passwords (
                section_name TEXT PRIMARY KEY,
                password TEXT
            )
        """)

        cursor.execute("PRAGMA table_info(users)")
        u_cols = [c[1] for c in cursor.fetchall()]
        if "phone" not in u_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
            )

        # جدول العقارات
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

        # جدول مصاريف العقارات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER, expense_type TEXT, amount REAL, notes TEXT, date TEXT,
                FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # جدول الموظفين والعمالة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
                hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
                workers_count INTEGER DEFAULT 1, craft_type TEXT
            )
        """)

        # جدول المستثمرين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
            )
        """)

        # جدول تذاكر IT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, category TEXT, status TEXT, created_at TEXT
            )
        """)

        # جدول المستندات والأرشيف
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT, category TEXT, upload_date TEXT,
                file_data BLOB, file_type TEXT
            )
        """)
        conn.commit()


init_db()


def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db") as conn:
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
                with sqlite3.connect("mh_group_erp.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT role FROM users WHERE username = ? AND password = ?",
                        (username_input, password_input),
                    )
                    res = cursor.fetchone()

                if res:
                    st.session_state["logged_in"] = True
                    st.session_state["user_role"] = res[0]
                    st.session_state["username"] = username_input
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة!")

        else:
            st.info("📱 استعادة كلمة السر عبر كود SMS")

            if st.session_state["reset_stage"] == "request":
                rec_username = st.text_input("اسم المستخدم:")
                rec_phone = st.text_input("رقم الهاتف المسجل للحساب:")

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("إرسال كود التحقق (SMS)", use_container_width=True):
                        with sqlite3.connect("mh_group_erp.db") as conn:
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
                        with sqlite3.connect("mh_group_erp.db") as conn:
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
    # Sidebar MH Group Branding
    st.sidebar.markdown(
        """
        <div style="text-align: right; padding-bottom: 15px; border-bottom: 1px solid #1f2937;">
            <h2 style="color: #f59e0b; margin:0; font-size: 1.4rem;">MH GROUP</h2>
            <p style="color: #6b7280; font-size: 0.75rem; margin:0;">ERP SYSTEM</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state["profile_pic"]:
        st.sidebar.image(st.session_state["profile_pic"], width=90)

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
        "📊 لوحة التحكم",
        "🏡 العقارات والمشروعات",
        "💼 الإدارة المالية",
        "👷 الموارد البشرية",
        "🤝 المستثمرين",
        "🚛 الموردين",
        "👥 الموظفين",
        "💻 IT Support",
        "📑 المستندات",
        "📈 التقارير",
        "👥 المستخدمين والصلاحيات",
        "⚙️ الإعدادات",
        "⏱️ سجل العمليات",
    ]

    current_role = st.session_state["user_role"]

    if st.session_state["is_developer"] or is_admin:
        menu_options = all_pages
    else:
        menu_options = ["📊 لوحة التحكم", "👤 الملف الشخصي (Profile)"]
        if current_role == "HR":
            menu_options.extend(["👷 الموارد البشرية", "📑 المستندات"])
        elif current_role == "Manager":
            menu_options.extend(["🏡 العقارات والمشروعات", "📑 المستندات"])
        elif current_role == "Accountant":
            menu_options.extend(["💼 الإدارة المالية", "🤝 المستثمرين"])
        elif current_role == "IT":
            menu_options.extend(["💻 IT Support"])

    page = st.sidebar.radio("القائمة", menu_options)

    # Sidebar Footer Branding
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: #6b7280; font-size: 0.8rem; margin-bottom: 10px;">
            <strong>M H Group</strong><br>للاستثمار والتطوير العقاري
        </div>
    """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- Top Navigation Bar ---
    top_col1, top_col2, top_col3 = st.columns([1, 2, 1])
    with top_col1:
        st.markdown(
            "### ☰ " + page
        )
    with top_col2:
        st.markdown(
            '<div style="text-align:center;"><input type="text" class="search-box" placeholder="ابحث هنا... Ctrl + K"></div>',
            unsafe_allow_html=True,
        )
    with top_col3:
        st.markdown(
            """
            <div style="display:flex; justify-content:flex-end; align-items:center; gap:15px; color:#9ca3af;">
                <span>☀️</span>
                <span>🔔 <sup style="color:#f59e0b;">5</sup></span>
                <div style="text-align:left;">
                    <div style="color:white; font-size:0.85rem; font-weight:bold;">المدير العام</div>
                    <div style="font-size:0.7rem;">admin@mhgroup.com</div>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- 1. Dashboard (المتطابقة تماماً مع الصورة) ---
    if page == "📊 لوحة التحكم":
        # Header Row
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            st.markdown(
                "### 👋 مرحباً بك، المدير العام"
            )
        with head_col2:
            st.date_input(
                "الفترة الحالية",
                value=(
                    datetime.date(2024, 5, 1),
                    datetime.date(2024, 5, 31),
                ),
            )

        # 5 Top KPI Cards
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

        with kpi1:
            st.markdown(
                """
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="metric-title">إجمالي الإيرادات</span>
                        <span style="background:#8b5cf6; padding:5px 8px; border-radius:50%; font-size:0.8rem;">💲</span>
                    </div>
                    <div class="metric-value">8,250,000 <span style="font-size:0.9rem; color:#9ca3af;">ج.م</span></div>
                    <div class="metric-sub"><span class="badge-green">📈 +12.5%</span> عن الشهر الماضي</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi2:
            st.markdown(
                """
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="metric-title">إجمالي المصروفات</span>
                        <span style="background:#ef4444; padding:5px 8px; border-radius:50%; font-size:0.8rem;">📉</span>
                    </div>
                    <div class="metric-value">2,850,000 <span style="font-size:0.9rem; color:#9ca3af;">ج.م</span></div>
                    <div class="metric-sub"><span class="badge-red">📉 -3.2%</span> عن الشهر الماضي</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi3:
            st.markdown(
                """
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="metric-title">صافي الأرباح</span>
                        <span style="background:#10b981; padding:5px 8px; border-radius:50%; font-size:0.8rem;">📊</span>
                    </div>
                    <div class="metric-value">5,400,000 <span style="font-size:0.9rem; color:#9ca3af;">ج.م</span></div>
                    <div class="metric-sub"><span class="badge-green">📈 +18.7%</span> عن الشهر الماضي</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi4:
            st.markdown(
                """
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="metric-title">قيمة العقارات</span>
                        <span style="background:#3b82f6; padding:5px 8px; border-radius:50%; font-size:0.8rem;">🏢</span>
                    </div>
                    <div class="metric-value">45,750,000 <span style="font-size:0.9rem; color:#9ca3af;">ج.م</span></div>
                    <div class="metric-sub" style="color:#9ca3af;">إجمالي قيمة المحفظة العقارية</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        with kpi5:
            st.markdown(
                """
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="metric-title">العقارات المباعة</span>
                        <span style="background:#f59e0b; padding:5px 8px; border-radius:50%; font-size:0.8rem;">🏠</span>
                    </div>
                    <div class="metric-value">12</div>
                    <div class="metric-sub" style="color:#9ca3af;">عقار هذا الشهر</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts Row
        chart_col1, chart_col2, activity_col = st.columns([2, 1.2, 1])

        with chart_col1:
            st.markdown("#### نظرة عامة على الأداء")
            months = [
                "يناير",
                "فبراير",
                "مارس",
                "أبريل",
                "مايو",
                "يونيو",
                "يوليو",
            ]
            revenues = [6.0, 6.8, 7.2, 7.5, 7.8, 7.8, 9.0]
            expenses = [1.5, 1.8, 1.7, 2.2, 2.6, 2.5, 3.1]
            profits = [4.5, 5.0, 5.5, 5.3, 5.2, 5.3, 5.9]

            fig_performance = go.Figure()
            fig_performance.add_trace(
                go.Scatter(
                    x=months,
                    y=revenues,
                    mode="lines+markers",
                    name="الإيرادات",
                    line=dict(color="#8b5cf6", width=3),
                )
            )
            fig_performance.add_trace(
                go.Scatter(
                    x=months,
                    y=expenses,
                    mode="lines+markers",
                    name="المصروفات",
                    line=dict(color="#ef4444", width=3),
                )
            )
            fig_performance.add_trace(
                go.Scatter(
                    x=months,
                    y=profits,
                    mode="lines+markers",
                    name="الأرباح",
                    line=dict(color="#10b981", width=3),
                )
            )

            fig_performance.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#9ca3af"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig_performance, use_container_width=True)

        with chart_col2:
            st.markdown("#### توزيع المصروفات")
            categories = [
                "شراء عقارات",
                "مصاريف تطوير",
                "مصاريف إدارية",
                "رواتب وأجور",
                "أخرى",
            ]
            values = [40, 25, 15, 10, 10]
            colors = ["#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7"]

            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=categories,
                        values=values,
                        hole=0.6,
                        marker=dict(colors=colors),
                    )
                ]
            )
            fig_donut.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#9ca3af"),
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown(
                "<div style='text-align:center; font-size:0.85rem; color:#9ca3af;'>إجمالي: 2,850,000 ج.م</div>",
                unsafe_allow_html=True,
            )

        with activity_col:
            st.markdown("#### النشاط الأخير")
            st.markdown(
                """
                <div class="custom-table-card" style="height:320px;">
                    <div class="activity-item">
                        <div>
                            <div class="activity-title">🏢 تم إضافة عقار جديد</div>
                            <div class="activity-time">منذ 10 دقائق</div>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div>
                            <div class="activity-title">💲 تم تسجيل إيراد جديد</div>
                            <div class="activity-time">منذ 30 دقيقة</div>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div>
                            <div class="activity-title">📄 تم رفع مستند جديد</div>
                            <div class="activity-time">منذ ساعتين</div>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div>
                            <div class="activity-title">👤 تم إضافة موظف جديد</div>
                            <div class="activity-time">منذ 3 ساعات</div>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div>
                            <div class="activity-title">🏢 تم تحديث بيانات عقار</div>
                            <div class="activity-time">منذ 5 ساعات</div>
                        </div>
                    </div>
                    <div style="text-align:center; margin-top:15px; font-size:0.8rem; color:#f59e0b; cursor:pointer;">عرض كل النشاط</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Bottom Tables Row
        btm_col1, btm_col2 = st.columns(2)

        with btm_col1:
            st.markdown("#### آخر المعاملات المالية")
            fin_df = pd.DataFrame(
                [
                    {
                        "نوع العملية": "إيراد",
                        "المبلغ": "850,000 ج.م",
                        "الجهة": "عميل - شركة النصر",
                        "التاريخ": "2024-05-23",
                        "الحالة": "مكتملة",
                    },
                    {
                        "نوع العملية": "مصروف",
                        "المبلغ": "250,000 ج.م",
                        "الجهة": "مورد - مقاولات مصر",
                        "التاريخ": "2024-05-23",
                        "الحالة": "مكتملة",
                    },
                    {
                        "نوع العملية": "إيراد",
                        "المبلغ": "1,200,000 ج.م",
                        "الجهة": "عميل - أحمد محمود",
                        "التاريخ": "2024-05-22",
                        "الحالة": "مكتملة",
                    },
                    {
                        "نوع العملية": "مصروف",
                        "المبلغ": "150,000 ج.م",
                        "الجهة": "شركة الكهرباء",
                        "التاريخ": "2024-05-22",
                        "الحالة": "مكتملة",
                    },
                ]
            )
            st.dataframe(fin_df, use_container_width=True)

        with btm_col2:
            st.markdown("#### آخر العقارات المضافة")
            prop_df_dash = pd.DataFrame(
                [
                    {
                        "اسم العقار": "فيلا النرجس 001",
                        "سعر الشراء": "5,200,000 ج.م",
                        "الحالة": "تحت التطوير",
                        "تاريخ الإضافة": "2024-05-23",
                    },
                    {
                        "اسم العقار": "عمارة الشروق 15",
                        "سعر الشراء": "8,750,000 ج.م",
                        "الحالة": "مباع",
                        "تاريخ الإضافة": "2024-05-22",
                    },
                    {
                        "اسم العقار": "قطعة أرض التجمع",
                        "سعر الشراء": "3,100,000 ج.م",
                        "الحالة": "متاح",
                        "تاريخ الإضافة": "2024-05-21",
                    },
                    {
                        "اسم العقار": "مول القاهرة الجديدة",
                        "سعر الشراء": "15,000,000 ج.م",
                        "الحالة": "تحت التطوير",
                        "تاريخ الإضافة": "2024-05-20",
                    },
                ]
            )
            st.dataframe(prop_df_dash, use_container_width=True)

    # --- باقي الأقسام تباعاً دون تغيير في الوظائف ---
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
                        with sqlite3.connect("mh_group_erp.db") as conn:
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

    elif page == "👥 المستخدمين والصلاحيات":
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
                            with sqlite3.connect("mh_group_erp.db") as conn:
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
                        with sqlite3.connect("mh_group_erp.db") as conn:
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
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            "DELETE FROM users WHERE username = ?", (del_user,)
                        )
                        conn.commit()
                    st.success(f"تم حذف الحساب {del_user}")
                    st.rerun()

    elif page == "🏡 العقارات والمشروعات":
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
                            with sqlite3.connect("mh_group_erp.db") as conn:
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
                        with sqlite3.connect("mh_group_erp.db") as conn:
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
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            "DELETE FROM properties WHERE id = ?", (del_id,)
                        )
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        st.markdown("### 📋 قائمة كافة العقارات والوحدات")
        st.dataframe(
            safe_read_sql(
                "SELECT id, name AS الاسم, type AS النوع, finishing AS التشطيب, location AS الموقع, price AS السعر, status AS الحالة FROM properties"
            ),
            use_container_width=True,
        )

    elif page == "👷 الموارد البشرية":
        st.title("👷 إدارة العمالة والموظفين والموردين")
        tab1, tab2 = st.tabs(["➕ إضافة موظف / مورد عمالة", "❌ حذف فرد"])

        with tab1:
            e_type = st.selectbox(
                "نوع الفئة المراد تسجيلها:",
                ["عامل", "مشرف", "مورد عمالة / مقاول"],
            )

            with st.form("add_emp_form"):
                e_name = st.text_input("اسم الفرد / اسم توريد المقاول")
                e_pos = st.text_input("المسمى الوظيفي / اسم الشركة أو المقاولة")

                w_count = 1
                c_type = "عامل عادي"

                if e_type == "مورد عمالة / مقاول":
                    col_w1, col_w2 = st.columns(2)
                    w_count = col_w1.number_input(
                        "عدد العمالة الموردة:", min_value=1, value=1, step=1
                    )
                    c_type = col_w2.selectbox(
                        "نوع تخصص العمالة:",
                        [
                            "نحات",
                            "مبيض محارة",
                            "عامل عادي",
                            "بناء",
                            "سباك",
                            "كهربائي",
                            "نقاش",
                            "حداد / نجار مسلح",
                        ],
                    )

                p_type = st.radio(
                    "نظام الحساب والماليات:", ["بالساعة", "يومية أساسية"]
                )

                c1, c2 = st.columns(2)
                h_rate = c1.number_input("سعر الساعة", min_value=0.0)
                h_worked = c2.number_input("عدد الساعات", min_value=0.0)
                d_rate = st.number_input("سعر اليومية الأساسية", min_value=0.0)

                if st.form_submit_button("حفظ البيانات"):
                    tot_pay = (
                        (h_rate * h_worked) if p_type == "بالساعة" else d_rate
                    )
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            """INSERT INTO employees 
                            (name, emp_type, position, pay_type, hourly_rate, hours_worked, daily_rate, total_pay, hire_date, workers_count, craft_type) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                e_name,
                                e_type,
                                e_pos,
                                p_type,
                                float(h_rate),
                                float(h_worked),
                                float(d_rate),
                                float(tot_pay),
                                str(datetime.date.today()),
                                int(w_count),
                                c_type,
                            ),
                        )
                        conn.commit()
                    st.success(f"تم الحفظ بنجاح! إجمالي المستحق: {tot_pay} EGP")

        with tab2:
            emp_df = safe_read_sql("SELECT id, name FROM employees")
            if not emp_df.empty:
                del_emp_id = st.selectbox(
                    "اختر الفرد للحذف",
                    emp_df["id"],
                    format_func=lambda x: emp_df[emp_df["id"] == x][
                        "name"
                    ].values[0],
                )
                if st.button("حذف البيانات"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            "DELETE FROM employees WHERE id = ?", (del_emp_id,)
                        )
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        st.dataframe(
            safe_read_sql(
                "SELECT id, name AS الاسم, emp_type AS الفئة, position AS الوظيفة, craft_type AS التخصص, workers_count AS عدد_العمالة, total_pay AS المستحق_المالي, hire_date AS التاريخ FROM employees"
            ),
            use_container_width=True,
        )

    elif page == "🤝 المستثمرين":
        st.title("💼 قسم المستثمرين وحاسبة الأرباح")
        inv_tabs = st.tabs(
            [
                "➕ تسجيل مستثمر",
                "🧮 حاسبة الأرباح والخسائر (P&L)",
                "❌ حذف مستثمر",
            ]
        )

        with inv_tabs[0]:
            with st.form("add_inv_form"):
                i_name = st.text_input("اسم المستثمر")
                i_amount = st.number_input(
                    "مبلغ الاستثمار (EGP)", min_value=0.0, step=1000.0
                )
                i_rate = st.number_input(
                    "نسبة العائد المتفق عليها (%)", min_value=0.0, step=0.5
                )

                if st.form_submit_button("تسجيل المستثمر"):
                    if i_name.strip():
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                                (
                                    i_name.strip(),
                                    float(i_amount),
                                    float(i_rate),
                                    str(datetime.date.today()),
                                ),
                            )
                            conn.commit()
                        st.success(f"تم تسجيل المستثمر '{i_name}' بنجاح!")
                        st.rerun()

        with inv_tabs[1]:
            st.subheader("🧮 حاسبة الأرباح والخسائر التقديرية")
            pnl_col1, pnl_col2 = st.columns(2)

            with pnl_col1:
                calc_amount = st.number_input(
                    "رأس المال (EGP):",
                    min_value=0.0,
                    value=100000.0,
                    step=10000.0,
                )
                calc_rate = st.number_input(
                    "نسبة العائد (%):", min_value=0.0, value=15.0, step=0.5
                )
                calc_months = st.slider(
                    "المدة (بالشهور):", 1, 36, value=12
                )

            with pnl_col2:
                gross_profit = calc_amount * (calc_rate / 100) * (calc_months / 12)
                net_total = calc_amount + gross_profit
                monthly_payout = gross_profit / calc_months

                st.metric("إجمالي الربح المتوقع", f"{gross_profit:,.2f} EGP")
                st.metric("إجمالي المستحق النهائي", f"{net_total:,.2f} EGP")
                st.metric("العائد الشهري المفترض", f"{monthly_payout:,.2f} EGP")

        with inv_tabs[2]:
            inv_df = safe_read_sql("SELECT id, name FROM investors")
            if not inv_df.empty:
                del_inv_id = st.selectbox(
                    "اختر المستثمر للحذف",
                    inv_df["id"],
                    format_func=lambda x: inv_df[inv_df["id"] == x][
                        "name"
                    ].values[0],
                )
                if st.button("حذف المستثمر"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            "DELETE FROM investors WHERE id = ?", (del_inv_id,)
                        )
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

    elif page == "⚙️ الإعدادات":
        if not is_admin:
            st.error("⛔ عذراً، هذه الصفحة مخصصة لمدير النظام (Admin) فقط!")
        else:
            st.title("⚙️ إعدادات المطور والثيمات")
            dev_tab1, dev_tab2 = st.tabs(
                ["🖼️ تخصيص الواجهة", "🎨 التحكم بالثيمات"]
            )

            with dev_tab1:
                cfg_login = st.session_state["login_config"]
                login_img_file = st.file_uploader(
                    "رفع شعار النظام:", type=["png", "jpg", "jpeg"]
                )
                if login_img_file:
                    st.session_state["login_config"][
                        "logo_bytes"
                    ] = login_img_file.getvalue()
                    st.success("تم التحديث بنجاح!")

            with dev_tab2:
                selected_theme_name = st.selectbox(
                    "اختر الثيم المطبق:", list(THEMES.keys())
                )
                if selected_theme_name != st.session_state["selected_theme"]:
                    st.session_state["selected_theme"] = selected_theme_name
                    st.rerun()
