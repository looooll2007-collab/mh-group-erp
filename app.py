import base64
import datetime
import io
import random
import sqlite3
import pandas as pd
import streamlit as st

# --- Expanded Theme Palette Configuration (7 Themes) ---
THEMES = {
    "أزرق نيلي احترافي (Modern Indigo)": {
        "primary": "#4F46E5",
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "text": "#1E293B",
        "accent": "#6366F1",
        "border": "#E2E8F0",
    },
    "الداكن الملكي والذهبي (Royal Dark & Gold)": {
        "primary": "#D97706",
        "bg": "#0F172A",
        "card": "#1E293B",
        "text": "#F8FAFC",
        "accent": "#F59E0B",
        "border": "#334155",
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
    "الصحراء والذهبي الدافئ (Desert Gold)": {
        "primary": "#B45309",
        "bg": "#FFFBEB",
        "card": "#FFFFFF",
        "text": "#78350F",
        "accent": "#D97706",
        "border": "#FEF3C7",
    },
    "الرمادي الرخامي الفاخر (Slate & Minimal Gray)": {
        "primary": "#334155",
        "bg": "#F1F5F9",
        "card": "#FFFFFF",
        "text": "#0F172A",
        "accent": "#64748B",
        "border": "#CBD5E1",
    },
}

# --- Page Configuration ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Default Session Configurations ---
if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 نظام إدارة MH Group ERP",
        "subtitle": "🔐 تسجيل الدخول للنظام",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
        "recovery_key": "123456",
        "logo_bytes": None,  # Persistent Login Image/Logo
    }

if "dashboard_config" not in st.session_state:
    st.session_state["dashboard_config"] = {
        "header_title": "📊 لوحة التحكم المتقدمة والملخص العام",
        "show_metrics": True,
        "custom_note": "أهلاً بك في لوحة تحكم النظام العامة. يمكنك متابعة العمليات من هنا.",
    }

# --- Preserve Theme Across Refresh ---
if "theme" in st.query_params:
    saved_theme = st.query_params["theme"]
    if saved_theme in THEMES:
        st.session_state["selected_theme"] = saved_theme

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = "أزرق نيلي احترافي (Modern Indigo)"

current_theme = THEMES[st.session_state["selected_theme"]]

# --- Dynamic Styles Injection ---
st.markdown(
    f"""
<style>
    [title*="keyboard"], [title*="Keyboard"], [data-testid="stHeader"] button title {{
        display: none !important;
    }}
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
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    div[data-testid="stMetric"] {{
        background-color: {current_theme["card"]} !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: 1px solid {current_theme["border"]} !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
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


# --- Database Initialization & Auto Migration ---
def init_db():
    with sqlite3.connect("mh_group_erp.db") as conn:
        cursor = conn.cursor()

        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                phone TEXT
            )
        """)

        # Add phone column if missing
        cursor.execute("PRAGMA table_info(users)")
        u_cols = [c[1] for c in cursor.fetchall()]
        if "phone" not in u_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role, phone) VALUES ('admin', 'admin123', 'Admin', '01000000000')"
            )

        # Properties Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, location TEXT, price REAL, status TEXT,
                type TEXT, finishing TEXT
            )
        """)
        
        cursor.execute("PRAGMA table_info(properties)")
        p_cols = [c[1] for c in cursor.fetchall()]
        if "type" not in p_cols:
            cursor.execute("ALTER TABLE properties ADD COLUMN type TEXT")
        if "finishing" not in p_cols:
            cursor.execute("ALTER TABLE properties ADD COLUMN finishing TEXT")

        # Property Expenses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER,
                expense_type TEXT,
                amount REAL,
                notes TEXT,
                date TEXT,
                FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Employees Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
                hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
                workers_count INTEGER DEFAULT 1, craft_type TEXT
            )
        """)

        # Investors Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
            )
        """)

        # IT Tickets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS it_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, category TEXT, status TEXT, created_at TEXT
            )
        """)

        # Documents Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT, category TEXT, upload_date TEXT,
                file_data BLOB, file_type TEXT
            )
        """)

        conn.commit()

init_db()

# --- Helper Database Reader ---
def safe_read_sql(query, params=()):
    try:
        with sqlite3.connect("mh_group_erp.db") as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()

# --- Session Authentication & States ---
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
    st.session_state["reset_stage"] = "request" # request, verify, new_pass
if "otp_code" not in st.session_state:
    st.session_state["otp_code"] = None
if "reset_username" not in st.session_state:
    st.session_state["reset_username"] = ""

# --- LOGIN & PASSWORD RECOVERY PAGE ---
def login_page():
    cfg = st.session_state["login_config"]
    st.markdown(f"<h1 class='main-header'>{cfg['title']}</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Display persistent Login Logo/Image if configured
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
            # Forgot Password Flow via SMS OTP
            st.info("📱 استعادة كلمة السر عبر كود SMS")

            if st.session_state["reset_stage"] == "request":
                rec_username = st.text_input("اسم المستخدم:")
                rec_phone = st.text_input("رقم الهاتف المسجل للحساب:")
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("إرسال كود التحقق (SMS)", use_container_width=True):
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT phone FROM users WHERE username = ?", (rec_username,))
                            user_row = cursor.fetchone()

                        if user_row and user_row[0] == rec_phone:
                            generated_otp = str(random.randint(100000, 999999))
                            st.session_state["otp_code"] = generated_otp
                            st.session_state["reset_username"] = rec_username
                            st.session_state["reset_stage"] = "verify"
                            
                            # SMS Simulation Message
                            st.toast(f"📱 [SMS SIMULATION] تم إرسال كود التحقق لرقمك: {generated_otp}", icon="📩")
                            st.rerun()
                        else:
                            st.error("اسم المستخدم أو رقم الهاتف غير مطابق للسجلات!")
                
                with col_r2:
                    if st.button("الرجوع لتسجيل الدخول", use_container_width=True):
                        st.session_state["show_forgot_password"] = False
                        st.rerun()

            elif st.session_state["reset_stage"] == "verify":
                st.write(f"تم إرسال كود SMS مكون من 6 أرقام إلى هاتفك المسجل باسم **{st.session_state['reset_username']}**.")
                st.caption(f"💡 (الكود المكتوب للتجربة: {st.session_state['otp_code']})")
                
                user_otp = st.text_input("أدخل كود التحقق المكون من 6 أرقام:")
                
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    if st.button("تأكيد الكود", use_container_width=True):
                        if user_otp == st.session_state["otp_code"]:
                            st.success("✅ الكود صحيح! انتقلت لصفحة تعيين كلمة السر.")
                            st.session_state["reset_stage"] = "new_pass"
                            st.rerun()
                        else:
                            st.error("❌ الكود غير صحيح! يرجى التأكد وإعادة المحاولة.")
                
                with col_v2:
                    if st.button("إلغاء", use_container_width=True):
                        st.session_state["show_forgot_password"] = False
                        st.rerun()

            elif st.session_state["reset_stage"] == "new_pass":
                st.success("🔓 يرجى كتابة كلمة السر الجديدة لتحديث حسابك:")
                new_reset_pass = st.text_input("كلمة السر الجديدة:", type="password")
                confirm_reset_pass = st.text_input("تأكيد كلمة السر الجديدة:", type="password")

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
                        st.success("✅ تم تحديث كلمة السر بنجاح! يمكنك الآن تسجيل الدخول.")
                        st.session_state["show_forgot_password"] = False
                        st.session_state["reset_stage"] = "request"


if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")

    if st.session_state["profile_pic"]:
        st.sidebar.image(st.session_state["profile_pic"], width=90)

    st.sidebar.markdown(
        f"**المستخدم:** {st.session_state['username']}\n\n**الصلاحية:** {st.session_state['user_role']}"
    )

    # Developer mode toggle for Admin
    if st.session_state["user_role"] == "Admin":
        dev_toggle = st.sidebar.checkbox(
            "🛠️ وضع المطور (Developer Mode)",
            value=st.session_state["is_developer"],
        )
        st.session_state["is_developer"] = dev_toggle
    else:
        st.session_state["is_developer"] = False

    # Dynamic Navigation
    all_pages = [
        "📊 لوحة التحكم الرئيسية",
        "👤 الملف الشخصي (Profile)",
        "👥 إدارة المستخدمين والصلاحيات",
        "🏡 إدارة العقارات والوحدات",
        "👷 إدارة الموارد البشرية والعمالة",
        "💼 قسم المستثمرين والمالية",
        "💻 قسم تقنية المعلومات (IT Support)",
        "📑 التقارير وإدارة المستندات",
        "⚙️ إعدادات المطور والثيمات",
    ]

    current_role = st.session_state["user_role"]

    if st.session_state["is_developer"]:
        menu_options = all_pages
    else:
        menu_options = ["👤 الملف الشخصي (Profile)"]
        if current_role == "Admin":
            menu_options = [
                "📊 لوحة التحكم الرئيسية",
                "👤 الملف الشخصي (Profile)",
                "👥 إدارة المستخدمين والصلاحيات",
                "🏡 إدارة العقارات والوحدات",
                "👷 إدارة الموارد البشرية والعمالة",
                "💼 قسم المستثمرين والمالية",
                "💻 قسم تقنية المعلومات (IT Support)",
                "📑 التقارير وإدارة المستندات",
            ]
        elif current_role == "HR":
            menu_options.extend(["👷 إدارة الموارد البشرية والعمالة", "📑 التقارير وإدارة المستندات"])
        elif current_role == "Manager":
            menu_options.extend(["🏡 إدارة العقارات والوحدات", "📑 التقارير وإدارة المستندات"])
        elif current_role == "Accountant":
            menu_options.extend(["💼 قسم المستثمرين والمالية", "📑 التقارير وإدارة المستندات"])
        elif current_role == "IT":
            menu_options.extend(["💻 قسم تقنية المعلومات (IT Support)"])

    page = st.sidebar.radio("القائمة الرئيسية", menu_options)

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 1. Dashboard ---
    if page == "📊 لوحة التحكم الرئيسية":
        dash_cfg = st.session_state["dashboard_config"]
        st.markdown(f"<h1 class='main-header'>{dash_cfg['header_title']}</h1>", unsafe_allow_html=True)
        st.info(dash_cfg["custom_note"])

        if dash_cfg["show_metrics"]:
            prop_df = safe_read_sql("SELECT COUNT(*) as count FROM properties")
            prop_count = prop_df["count"][0] if not prop_df.empty else 0

            emp_df = safe_read_sql("SELECT COUNT(*) as count FROM employees")
            emp_count = emp_df["count"][0] if not emp_df.empty else 0

            inv_df = safe_read_sql("SELECT SUM(investment_amount) as sum FROM investors")
            total_inv = inv_df["sum"][0] if (not inv_df.empty and inv_df["sum"][0] is not None) else 0

            exp_df = safe_read_sql("SELECT SUM(amount) as sum FROM property_expenses")
            total_exp = exp_df["sum"][0] if (not exp_df.empty and exp_df["sum"][0] is not None) else 0

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
            emp_summary = safe_read_sql("SELECT emp_type as الفئة, COUNT(*) as العدد FROM employees GROUP BY emp_type")
            st.dataframe(emp_summary, use_container_width=True)

        with col_b:
            st.markdown("### 🏡 ملخص حالة العقارات")
            prop_summary = safe_read_sql("SELECT status as الحالة, COUNT(*) as العدد FROM properties GROUP BY status")
            st.dataframe(prop_summary, use_container_width=True)

    # --- 2. Profile Section ---
    elif page == "👤 الملف الشخصي (Profile)":
        st.title("👤 إدارة الملف الشخصي والحساب")
        col_img, col_info = st.columns([1, 2])

        with col_img:
            st.markdown("### 🖼️ الصورة الشخصية")
            if st.session_state["profile_pic"]:
                st.image(st.session_state["profile_pic"], width=180, caption="الصورة الحالية")
            else:
                st.info("لم يتم رفع صورة شخصية بعد.")

            uploaded_pic = st.file_uploader("رفع / تغيير الصورة", type=["jpg", "png", "jpeg"])
            if uploaded_pic:
                st.session_state["profile_pic"] = uploaded_pic.getvalue()
                st.success("تم تحديث الصورة الشخصية بنجاح!")
                st.rerun()

        with col_info:
            st.markdown("### ✏️ تعديل البيانات الشخصية")
            user_data = safe_read_sql("SELECT phone FROM users WHERE username = ?", (st.session_state["username"],))
            curr_phone = user_data["phone"][0] if not user_data.empty and user_data["phone"][0] else ""

            with st.form("edit_profile_form"):
                new_username = st.text_input("اسم المستخدم الحالي:", value=st.session_state["username"])
                new_phone = st.text_input("رقم الهاتف (لأكواد الاستعادة SMS):", value=curr_phone)
                st.text_input("الصلاحية الحالية (للقراءة فقط):", value=st.session_state["user_role"], disabled=True)

                if st.form_submit_button("حفظ التعديلات"):
                    try:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE users SET username = ?, phone = ? WHERE username = ?",
                                (new_username, new_phone, st.session_state["username"]),
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
        tab1, tab2, tab3, tab4 = st.tabs(["➕ إضافة مستخدم", "✏️ تعديل مستخدم", "📋 قائمة المستخدمين", "❌ حذف مستخدم"])

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
            users_list_df = safe_read_sql("SELECT id, username, role, phone FROM users")
            if not users_list_df.empty:
                selected_user_edit = st.selectbox("اختر المستخدم للتعديل:", users_list_df["username"])
                u_row = users_list_df[users_list_df["username"] == selected_user_edit].iloc[0]

                role_options = ["Admin", "Manager", "HR", "IT", "Accountant"]
                current_user_role = str(u_row["role"]).strip()
                default_role_index = role_options.index(current_user_role) if current_user_role in role_options else 0

                with st.form("edit_user_admin_form"):
                    e_role = st.selectbox("الصلاحية الجديدة:", role_options, index=default_role_index)
                    e_phone = st.text_input("رقم الهاتف:", value=str(u_row["phone"] or ""))
                    e_pass = st.text_input("كلمة مرور جديدة (اتركها فارغة للتجاهل):", type="password")

                    if st.form_submit_button("حفظ التعديلات"):
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET role = ?, phone = ? WHERE username = ?", (e_role, e_phone, selected_user_edit))
                            if e_pass:
                                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (e_pass, selected_user_edit))
                            conn.commit()
                        st.success(f"تم تحديث بيانات {selected_user_edit} بنجاح!")
                        st.rerun()

        with tab3:
            st.dataframe(safe_read_sql("SELECT id, username, role, phone FROM users"), use_container_width=True)

        with tab4:
            users_df = safe_read_sql("SELECT id, username FROM users WHERE username != 'admin'")
            if not users_df.empty:
                del_user = st.selectbox("اختر المستخدم للحذف:", users_df["username"])
                if st.button("حذف الحساب المحدد"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM users WHERE username = ?", (del_user,))
                        conn.commit()
                    st.success(f"تم حذف الحساب {del_user}")
                    st.rerun()

    # --- 4. Properties ---
    elif page == "🏡 إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات والمصاريف")
        tab1, tab2, tab3 = st.tabs(["➕ إضافة عقار", "💸 مصاريف العقارات", "❌ حذف عقار"])

        with tab1:
            with st.form("add_prop"):
                p_name = st.text_input("اسم العقار / الوحدة")
                p_type = st.selectbox("نوع العقار:", ["شقة", "فيلا", "محل تجاري", "أرض", "مبنى كامل", "مكتب"])
                p_loc = st.text_input("الموقع")
                p_price = st.number_input("السعر المقدر / الكلي", min_value=0.0)
                p_finishing = st.selectbox("نوع التشطيب:", ["بدون تشطيب", "لوكس", "سوبر لوكس", "ألترا سوبر لوكس"])
                p_stat = st.selectbox("الحالة", ["متاح", "تم البيع", "تحت الإنشاء", "محجوز"])

                if st.form_submit_button("حفظ العقار"):
                    if p_name:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO properties (name, location, price, status, type, finishing) VALUES (?, ?, ?, ?, ?, ?)",
                                (p_name, p_loc, float(p_price), p_stat, p_type, p_finishing),
                            )
                            conn.commit()
                        st.success("تم إضافة العقار بنجاح")
                        st.rerun()

        with tab2:
            st.subheader("💸 تسجيل مصاريف على العقارات")
            props_df = safe_read_sql("SELECT id, name FROM properties")
            if not props_df.empty:
                with st.form("add_expense_form"):
                    selected_p_id = st.selectbox("اختر العقار:", props_df["id"], format_func=lambda x: props_df[props_df["id"] == x]["name"].values[0])
                    exp_type = st.selectbox("نوع المصاريف / التشطيب:", ["دهانات", "نجارة", "كهرباء", "سباكة", "محارة وتأسيس", "سيراميك وأرضيات", "رسوم وإجراءات قانونية", "أخرى"])
                    exp_amount = st.number_input("المبلغ (EGP):", min_value=0.0)
                    exp_notes = st.text_input("ملاحظات / بيان المصروف:")

                    if st.form_submit_button("تسجيل المصروف"):
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO property_expenses (property_id, expense_type, amount, notes, date) VALUES (?, ?, ?, ?, ?)",
                                (selected_p_id, exp_type, float(exp_amount), exp_notes, str(datetime.date.today())),
                            )
                            conn.commit()
                        st.success("تم تسجيل المصروف بنجاح!")
                        st.rerun()

            st.markdown("#### 📜 سجل كافة مصاريف العقارات")
            exp_history = safe_read_sql("""
                SELECT pe.id, p.name as العقار, pe.expense_type as نوع_المصروف, pe.amount as المبلغ, pe.notes as الملاحظات, pe.date as التاريخ
                FROM property_expenses pe
                JOIN properties p ON pe.property_id = p.id
            """)
            st.dataframe(exp_history, use_container_width=True)

        with tab3:
            props_df = safe_read_sql("SELECT id, name FROM properties")
            if not props_df.empty:
                del_id = st.selectbox("اختر العقار للحذف", props_df["id"], format_func=lambda x: props_df[props_df["id"] == x]["name"].values[0])
                if st.button("حذف العقار"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM properties WHERE id = ?", (del_id,))
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        st.markdown("### 📋 قائمة كافة العقارات والوحدات")
        st.dataframe(safe_read_sql("SELECT id, name AS الاسم, type AS النوع, finishing AS التشطيب, location AS الموقع, price AS السعر, status AS الحالة FROM properties"), use_container_width=True)

    # --- 5. HR Section ---
    elif page == "👷 إدارة الموارد البشرية والعمالة":
        st.title("👷 إدارة العمالة والموظفين والموردين")
        tab1, tab2 = st.tabs(["➕ إضافة موظف / مورد عمالة", "❌ حذف فرد"])

        with tab1:
            e_type = st.selectbox("نوع الفئة المراد تسجيلها:", ["عامل", "مشرف", "مورد عمالة / مقاول"])

            with st.form("add_emp_form"):
                e_name = st.text_input("اسم الفرد / اسم توريد المقاول")
                e_pos = st.text_input("المسمى الوظيفي / اسم الشركة أو المقاولة")

                w_count = 1
                c_type = "عامل عادي"

                if e_type == "مورد عمالة / مقاول":
                    st.markdown("#### 🛠️ تفاصيل العمالة الموردة:")
                    col_w1, col_w2 = st.columns(2)
                    w_count = col_w1.number_input("عدد العمالة الموردة:", min_value=1, value=1, step=1)
                    c_type = col_w2.selectbox("نوع تخصص العمالة:", ["نحات", "مبيض محارة", "عامل عادي", "بناء", "سباك", "كهربائي", "نقاش", "حداد / نجار مسلح"])

                p_type = st.radio("نظام الحساب والماليات:", ["بالساعة", "يومية أساسية"])

                c1, c2 = st.columns(2)
                h_rate = c1.number_input("سعر الساعة", min_value=0.0)
                h_worked = c2.number_input("عدد الساعات", min_value=0.0)
                d_rate = st.number_input("سعر اليومية الأساسية", min_value=0.0)

                if st.form_submit_button("حفظ البيانات"):
                    tot_pay = (h_rate * h_worked) if p_type == "بالساعة" else d_rate
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute(
                            """INSERT INTO employees 
                            (name, emp_type, position, pay_type, hourly_rate, hours_worked, daily_rate, total_pay, hire_date, workers_count, craft_type) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                e_name, e_type, e_pos, p_type,
                                float(h_rate), float(h_worked), float(d_rate), float(tot_pay),
                                str(datetime.date.today()), int(w_count), c_type,
                            ),
                        )
                        conn.commit()
                    st.success(f"تم الحفظ بنجاح! إجمالي المستحق: {tot_pay} EGP")

        with tab2:
            emp_df = safe_read_sql("SELECT id, name FROM employees")
            if not emp_df.empty:
                del_emp_id = st.selectbox("اختر الفرد للحذف", emp_df["id"], format_func=lambda x: emp_df[emp_df["id"] == x]["name"].values[0])
                if st.button("حذف البيانات"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM employees WHERE id = ?", (del_emp_id,))
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        st.markdown("### 📋 سجل الموظفين والعمالة والموردين")
        st.dataframe(safe_read_sql("SELECT id, name AS الاسم, emp_type AS الفئة, position AS الوظيفة, craft_type AS التخصص, workers_count AS عدد_العمالة, total_pay AS المستحق_المالي, hire_date AS التاريخ FROM employees"), use_container_width=True)

    # --- 6. Investors ---
    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين والرسوم البيانية")
        tab1, tab2 = st.tabs(["➕ إضافة مستثمر", "❌ حذف مستثمر"])

        with tab1:
            with st.form("add_inv"):
                i_name = st.text_input("اسم المستثمر")
                i_amount = st.number_input("مبلغ الاستثمار", min_value=0.0)
                i_rate = st.number_input("نسبة العائد (%)", min_value=0.0)
                if st.form_submit_button("تسجيل المستثمر"):
                    if i_name:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                                (i_name, float(i_amount), float(i_rate), str(datetime.date.today())),
                            )
                            conn.commit()
                        st.success("تم التسجيل بنجاح")
                        st.rerun()

        with tab2:
            inv_df = safe_read_sql("SELECT id, name FROM investors")
            if not inv_df.empty:
                del_inv_id = st.selectbox("اختر المستثمر للحذف", inv_df["id"], format_func=lambda x: inv_df[inv_df["id"] == x]["name"].values[0])
                if st.button("حذف المستثمر"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM investors WHERE id = ?", (del_inv_id,))
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        st.subheader("📈 الرسوم التوضيحية للاستثمارات")
        df_inv = safe_read_sql("SELECT name, investment_amount, return_rate FROM investors")

        if not df_inv.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### توزيع حجم الاستثمارات")
                st.bar_chart(df_inv.set_index("name")["investment_amount"])
            with c2:
                st.markdown("#### نسبة العائد لكل مستثمر (%)")
                st.line_chart(df_inv.set_index("name")["return_rate"])
            st.dataframe(df_inv, use_container_width=True)

    # --- 7. IT Support ---
    elif page == "💻 قسم تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات والدعم الفني")
        tab1, tab2 = st.tabs(["➕ تذكرة جديدة", "❌ حذف تذكرة"])

        with tab1:
            with st.form("add_t"):
                t_title = st.text_input("عنوان المشكلة")
                t_cat = st.selectbox("التصنيف", ["شبكات", "برمجيات", "أجهزة", "صلاحيات"])
                t_stat = st.selectbox("الحالة", ["جديد", "قيد المعالجة", "مغلق"])
                if st.form_submit_button("إرسال التذكرة"):
                    if t_title:
                        with sqlite3.connect("mh_group_erp.db") as conn:
                            conn.execute(
                                "INSERT INTO it_tickets (title, category, status, created_at) VALUES (?, ?, ?, ?)",
                                (t_title, t_cat, t_stat, str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))),
                            )
                            conn.commit()
                        st.success("تم إرسال التذكرة بنجاح")
                        st.rerun()

        with tab2:
            t_df = safe_read_sql("SELECT id, title FROM it_tickets")
            if not t_df.empty:
                del_t_id = st.selectbox("اختر التذكرة للحذف", t_df["id"], format_func=lambda x: t_df[t_df["id"] == x]["title"].values[0])
                if st.button("حذف التذكرة"):
                    with sqlite3.connect("mh_group_erp.db") as conn:
                        conn.execute("DELETE FROM it_tickets WHERE id = ?", (del_t_id,))
                        conn.commit()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        st.dataframe(safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True)

    # --- 8. Reports & Documents ---
    elif page == "📑 التقارير وإدارة المستندات":
        st.title("📑 التقارير ورفع الأرشيف والمستندات")

        tabs_list = ["📤 رفع وأرشفة المستندات", "📊 استخراج التقارير"]
        if current_role == "Admin" or st.session_state["is_developer"]:
            tabs_list.insert(1, "👁️ معاينة المستندات والأرشيف")

        doc_tabs = st.tabs(tabs_list)

        with doc_tabs[0]:
            st.subheader("📤 رفع مستند جديد إلى النظام")
            doc_cat = st.selectbox("تصنيف المستند", ["عقود عمالة", "عقود مستثمرين", "أوراق عقارات", "فواتير ومستندات طوارئ"])
            uploaded_file = st.file_uploader("اختر الملف لرفعه", type=["pdf", "docx", "png", "jpg", "xlsx", "txt"])

            if uploaded_file and st.button("حفظ المستند بالمؤرشف"):
                file_bytes = uploaded_file.getvalue()
                file_type = uploaded_file.type

                with sqlite3.connect("mh_group_erp.db") as conn:
                    conn.execute(
                        "INSERT INTO documents (file_name, category, upload_date, file_data, file_type) VALUES (?, ?, ?, ?, ?)",
                        (uploaded_file.name, doc_cat, str(datetime.date.today()), file_bytes, file_type),
                    )
                    conn.commit()
                st.success(f"تم رفع المستند '{uploaded_file.name}' وأرشفته بنجاح!")

            st.markdown("---")
            st.subheader("📂 الأرشيف الحالي للمستندات")
            st.dataframe(safe_read_sql("SELECT id, file_name, category, upload_date FROM documents"), use_container_width=True)

        if current_role == "Admin" or st.session_state["is_developer"]:
            with doc_tabs[1]:
                st.subheader("👁️ معاينة وتحميل المستندات المؤرشفة")
                with sqlite3.connect("mh_group_erp.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, file_name, category, upload_date, file_data, file_type FROM documents")
                    all_docs = cursor.fetchall()

                if all_docs:
                    doc_dict = {f"[{doc[0]}] {doc[1]} - ({doc[2]})": doc for doc in all_docs}
                    selected_doc_key = st.selectbox("اختر المستند للمعاينة:", list(doc_dict.keys()))
                    d_id, d_name, d_cat, d_date, d_bytes, d_type = doc_dict[selected_doc_key]

                    st.write(f"**اسم الملف:** {d_name}")
                    st.write(f"**التصنيف:** {d_cat}")
                    st.write(f"**تاريخ الرفع:** {d_date}")

                    if d_bytes:
                        if d_type and "image" in d_type:
                            st.image(d_bytes, caption=d_name, use_container_width=True)
                        elif d_type and "text" in d_type:
                            st.text_area("محتوى الملف:", d_bytes.decode("utf-8", errors="ignore"), height=200)
                        else:
                            st.info("💡 يتطلب استعراض هذا الملف المتقدم التنزيل المباشر.")

                        st.download_button(
                            label=f"📥 تحميل المستند ({d_name})",
                            data=d_bytes,
                            file_name=d_name,
                            mime=d_type if d_type else "application/octet-stream",
                            use_container_width=True,
                        )

        report_tab_index = 2 if (current_role == "Admin" or st.session_state["is_developer"]) else 1
        with doc_tabs[report_tab_index]:
            st.subheader("📊 استخراج تصدير بيانات الأقسام (Excel / CSV)")

            target_table = st.selectbox(
                "اختر القسم/الجدول المراد تصديره:",
                [
                    "العقارات والوحدات (properties)",
                    "مصاريف العقارات (property_expenses)",
                    "العمالة والموظفين (employees)",
                    "المستثمرين والمالية (investors)",
                    "تذاكر الدعم الفني (it_tickets)",
                    "سجل المستندات (documents)",
                ],
            )

            table_map = {
                "العقارات والوحدات (properties)": "properties",
                "مصاريف العقارات (property_expenses)": "property_expenses",
                "العمالة والموظفين (employees)": "employees",
                "المستثمرين والمالية (investors)": "investors",
                "تذاكر الدعم الفني (it_tickets)": "it_tickets",
                "سجل المستندات (documents)": "documents",
            }

            selected_db_table = table_map[target_table]
            export_df = safe_read_sql(f"SELECT * FROM {selected_db_table}")

            if not export_df.empty:
                st.dataframe(export_df, use_container_width=True)
                col_exp1, col_exp2 = st.columns(2)

                csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
                col_exp1.download_button(
                    label="📥 تصدير إلى CSV",
                    data=csv_data,
                    file_name=f"{selected_db_table}_report.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    export_df.to_excel(writer, sheet_name="Data", index=False)
                excel_data = excel_buffer.getvalue()

                col_exp2.download_button(
                    label="📊 تصدير إلى Excel",
                    data=excel_data,
                    file_name=f"{selected_db_table}_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    # --- 9. Developer Settings ---
    elif page == "⚙️ إعدادات المطور والثيمات":
        st.title("⚙️ إعدادات المطور وتخصيص النظام واللوحة الرئيسية")

        dev_tab1, dev_tab2, dev_tab3 = st.tabs(
            ["📊 تخصيص اللوحة الرئيسية", "🎨 تخصيص الثيمات والواجهة", "🔐 تخصيص شاشة تسجيل الدخول"]
        )

        with dev_tab1:
            st.subheader("📊 التحكم وتعديل اللوحة الرئيسية (خاص بالمطور)")
            dash_cfg = st.session_state["dashboard_config"]

            with st.form("dev_dashboard_form"):
                d_header = st.text_input("عنوان اللوحة الرئيسية:", value=dash_cfg["header_title"])
                d_show_metrics = st.checkbox("عرض الإحصائيات والأرقام بالأعلى", value=dash_cfg["show_metrics"])
                d_note = st.text_area("الملاحظة / التنبيه الإداري العلوي:", value=dash_cfg["custom_note"])

                if st.form_submit_button("حفظ إعدادات اللوحة الرئيسية"):
                    st.session_state["dashboard_config"] = {
                        "header_title": d_header,
                        "show_metrics": d_show_metrics,
                        "custom_note": d_note,
                    }
                    st.success("تم تحديث إعدادات اللوحة الرئيسية بنجاح!")

        with dev_tab2:
            st.subheader("🎨 التحكم بثيم التطبيق وتجربة المستخدم")

            selected_theme_name = st.selectbox(
                "اختر الثيم العام المطبق للنظام:",
                list(THEMES.keys()),
                index=list(THEMES.keys()).index(st.session_state["selected_theme"]),
            )

            if selected_theme_name != st.session_state["selected_theme"]:
                st.session_state["selected_theme"] = selected_theme_name
                st.query_params["theme"] = selected_theme_name
                st.success(f"تم تطبيق ثيم: {selected_theme_name}")
                st.rerun()

            st.markdown("#### 🖌️ معاينة لوحة الألوان الحالية:")
            theme_cols = st.columns(len(current_theme))
            for idx, (color_key, color_hex) in enumerate(current_theme.items()):
                with theme_cols[idx]:
                    st.markdown(
                        f"**{color_key}**<br><div style='background-color:{color_hex};height:40px;border-radius:6px;border:1px solid #ccc;'></div><small>{color_hex}</small>",
                        unsafe_allow_html=True,
                    )

        with dev_tab3:
            st.subheader("🔐 إعدادات وتخصيص شاشة الدخول والصورة")
            cfg = st.session_state["login_config"]

            st.markdown("#### 🖼️ صورة / لوجو شاشة تسجيل الدخول:")
            if cfg.get("logo_bytes"):
                st.image(cfg["logo_bytes"], width=200, caption="الصورة المعتمدة حالياً")
                if st.button("🗑️ إزالة صورة شاشة الدخول"):
                    st.session_state["login_config"]["logo_bytes"] = None
                    st.success("تم إزالة الصورة!")
                    st.rerun()

            uploaded_login_logo = st.file_uploader("رفع صورة جديدة لشاشة تسجيل الدخول (تظهر دائماً للجميع):", type=["png", "jpg", "jpeg", "webp"])
            if uploaded_login_logo:
                st.session_state["login_config"]["logo_bytes"] = uploaded_login_logo.getvalue()
                st.success("تم تحديث وحفظ صورة شاشة الدخول بنجاح!")
                st.rerun()

            st.markdown("---")
            with st.form("login_config_form"):
                new_title = st.text_input("عنوان الشاشة الرئيسية", value=cfg["title"])
                new_subtitle = st.text_input("العنوان الفرعي", value=cfg["subtitle"])
                new_btn_text = st.text_input("نص زر الدخول", value=cfg["btn_text"])
                new_welcome_msg = st.text_area("رسالة الترحيب", value=cfg["welcome_msg"])
                new_rec_key = st.text_input("رمز استعادة النظام الإضافي", value=cfg["recovery_key"], type="password")

                if st.form_submit_button("حفظ كافة إعدادات شاشة الدخول"):
                    st.session_state["login_config"]["title"] = new_title
                    st.session_state["login_config"]["subtitle"] = new_subtitle
                    st.session_state["login_config"]["btn_text"] = new_btn_text
                    st.session_state["login_config"]["welcome_msg"] = new_welcome_msg
                    st.session_state["login_config"]["recovery_key"] = new_rec_key
                    st.success("تم حفظ إعدادات شاشة الدخول بنجاح!")
