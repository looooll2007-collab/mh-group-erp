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
# 1. إعدادات الصفحة والثيمات الديناميكية
# ==========================================
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = (
        "الداكن الملكي والذهبي (Royal Dark & Gold)"
    )

current_theme = THEMES[st.session_state["selected_theme"]]

# إعدادات جلسة التطبيق والنصوص
if "login_config" not in st.session_state:
    st.session_state["login_config"] = {
        "title": "🏢 نظام إدارة MH Group ERP",
        "subtitle": "🔐 تسجيل الدخول للنظام",
        "btn_text": "تسجيل الدخول",
        "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
    }

if "dashboard_config" not in st.session_state:
    st.session_state["dashboard_config"] = {
        "header_title": "📊 لوحة التحكم المتقدمة والملخص العام",
    }

# تطبيق تنسيقات الـ CSS
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
# 2. تهيئة قاعدة البيانات الآمنة مع Migration
# ==========================================
def get_db_connection():
    return sqlite3.connect("mh_group_erp.db", timeout=20)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. المستخدمين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            phone TEXT
        )
    """)

    # 2. الجلسات
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

    # 3. العقارات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, location TEXT, price REAL, status TEXT, type TEXT, finishing TEXT
        )
    """)

    # 4. مصروفات العقارات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER, expense_type TEXT, amount REAL, notes TEXT, date TEXT
        )
    """)

    # 5. الموظفين والعمالة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
            hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT,
            workers_count INTEGER DEFAULT 1, craft_type TEXT
        )
    """)

    # 6. المستثمرين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT, notes TEXT
        )
    """)

    # --- 🛠️ تحديث أوتوماتيكي للجدول في حال غياب عمود notes ---
    try:
        cursor.execute("SELECT notes FROM investors LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE investors ADD COLUMN notes TEXT")

    # 7. معاملات الأرباح/الخسائر للمستثمرين
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investor_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_id INTEGER,
            trans_type TEXT,
            amount REAL,
            description TEXT,
            date TEXT
        )
    """)

    # 8. الدعم الفني IT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, category TEXT, status TEXT, created_at TEXT
        )
    """)

    # 9. المستندات والأرشيف
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT, category TEXT, upload_date TEXT, file_data BLOB, file_type TEXT
        )
    """)

    # إضافة المسؤول الأساسي إن لم يوجد
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
# 3. إدارة تسجيل الدخول والجلسة
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "is_developer" not in st.session_state:
    st.session_state["is_developer"] = False


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
# 4. شريط الأقسام المكتمل والقائمة
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
        "👥 إدارة المستخدمين والصلاحيات والجلسات",
        "🏡 إدارة العقارات والوحدات",
        "👷 إدارة الموارد البشرية والعمالة",
        "💼 قسم المستثمرين والمالية",
        "💻 قسم تقنية المعلومات (IT Support)",
        "📑 التقارير وإدارة المستندات",
    ]

    page = st.sidebar.radio(" القائمة الرئيسية", all_pages)

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

    # -------------------------------------------------------------
    # 🔴 وضع المطور: تعديل النصوص والتصميم المباشر
    # -------------------------------------------------------------
    if st.session_state["is_developer"]:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ إعدادات وضع المطور")
        theme_choice = st.sidebar.selectbox(
            "اختيار ثيم التطبيق",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["selected_theme"]),
        )
        if theme_choice != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = theme_choice
            st.rerun()

        with st.sidebar.expander("✏️ تعديل نصوص الشاشات"):
            st.session_state["login_config"]["title"] = st.text_input(
                "عنوان صفحة الدخول", st.session_state["login_config"]["title"]
            )
            st.session_state["dashboard_config"]["header_title"] = (
                st.text_input(
                    "عنوان لوحة التحكم",
                    st.session_state["dashboard_config"]["header_title"],
                )
            )

    # -------------------------------------------------------------
    # 1. لوحة التحكم الرئيسية
    # -------------------------------------------------------------
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
        inv_df = safe_read_sql("SELECT investment_amount FROM investors")
        inv_sum = inv_df["investment_amount"].sum() if not inv_df.empty else 0
        c3.metric("إجمالي حجم الاستثمار", f"{inv_sum:,.0f} EGP")

        tickets_df = safe_read_sql(
            "SELECT id FROM it_tickets WHERE status != 'مغلق'"
        )
        c4.metric("تذاكر الدعم المفتوحة", f"{len(tickets_df)} تذكرة")

        st.markdown("---")
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🏡 توزيع حالة العقارات")
            prop_df = safe_read_sql("SELECT status, COUNT(*) as count FROM properties GROUP BY status")
            if not prop_df.empty:
                st.bar_chart(prop_df.set_index("status"))
            else:
                st.info("لا توجد بيانات عقارات مسجلة.")

        with col_right:
            st.subheader("👥 توزيع العمالة والموظفين")
            emp_df = safe_read_sql("SELECT emp_type, COUNT(*) as count FROM employees GROUP BY emp_type")
            if not emp_df.empty:
                st.bar_chart(emp_df.set_index("emp_type"))
            else:
                st.info("لا توجد بيانات عمالة مسجلة.")

    # -------------------------------------------------------------
    # 2. إدارة المستخدمين والأنشطة والجلسات
    # -------------------------------------------------------------
    elif page == "👥 إدارة المستخدمين والصلاحيات والجلسات":
        st.title("👥 إدارة المستخدمين والأنشطة")
        tab1, tab2, tab3 = st.tabs([
            "📋 قائمة المستخدمين",
            "➕ إضافة مستخدم جديد",
            "🌐 مراقبة الجلسات والـ IP",
        ])

        with tab1:
            st.dataframe(
                safe_read_sql("SELECT id, username, role, phone FROM users"),
                use_container_width=True,
            )

        with tab2:
            if "u_msg_succ" in st.session_state:
                st.success(st.session_state.pop("u_msg_succ"))
            if "u_msg_err" in st.session_state:
                st.error(st.session_state.pop("u_msg_err"))

            if "form_key_u" not in st.session_state:
                st.session_state["form_key_u"] = 0

            with st.form(f"add_user_form_{st.session_state['form_key_u']}"):
                u_n = st.text_input("اسم المستخدم")
                u_p = st.text_input("كلمة المرور", type="password")
                u_ph = st.text_input("رقم الهاتف")
                u_r = st.selectbox(
                    "الصلاحية", ["Admin", "Manager", "HR", "IT", "Accountant"]
                )

                if st.form_submit_button("إضافة المستخدم"):
                    clean_u = u_n.strip()
                    clean_p = u_p.strip()

                    if clean_u and clean_p:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "SELECT id FROM users WHERE LOWER(TRIM(username)) = LOWER(?)",
                                (clean_u,),
                            )
                            if cursor.fetchone():
                                st.session_state["u_msg_err"] = (
                                    f"❌ اسم المستخدم '{clean_u}' مسجل مسبقاً!"
                                )
                            else:
                                cursor.execute(
                                    "INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                    (clean_u, clean_p, u_r, u_ph.strip()),
                                )
                                conn.commit()
                                st.session_state["u_msg_succ"] = (
                                    f"✅ تم إضافة المستخدم '{clean_u}' بنجاح!"
                                )
                            conn.close()
                        except sqlite3.IntegrityError:
                            st.session_state["u_msg_err"] = (
                                f"❌ اسم المستخدم '{clean_u}' مسجل مسبقاً!"
                            )
                        except Exception as e:
                            st.session_state["u_msg_err"] = f"❌ حدث خطأ: {e}"

                        st.session_state["form_key_u"] += 1
                        st.rerun()
                    else:
                        st.error("يرجى كتابة اسم المستخدم وكلمة المرور!")

        with tab3:
            st.subheader("🌐 سجل الجلسات والعناوين IP")
            st.dataframe(
                safe_read_sql(
                    "SELECT username, ip_address, login_time, last_activity, status FROM user_sessions ORDER BY id DESC"
                ),
                use_container_width=True,
            )

    # -------------------------------------------------------------
    # 3. إدارة العقارات والوحدات والمصروفات
    # -------------------------------------------------------------
    elif page == "🏡 إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات")
        tab1, tab2, tab3 = st.tabs([
            "📋 سجل العقارات",
            "➕ إضافة عقار",
            "💸 مصروفات المشاريع",
        ])

        with tab1:
            st.dataframe(
                safe_read_sql("SELECT * FROM properties"),
                use_container_width=True,
            )

        with tab2:
            with st.form("add_prop_form"):
                p_name = st.text_input("اسم العقار/الوحدة")
                p_loc = st.text_input("الموقع")
                p_price = st.number_input("السعر (EGP)", min_value=0.0)
                p_status = st.selectbox(
                    "الحالة", ["متاح", "مباع", "قيد التشطيب", "محجوز"]
                )
                p_type = st.selectbox(
                    "النوع", ["شقة", "فيلا", "محل تجاري", "أرض"]
                )
                p_finishing = st.selectbox(
                    "التشطيب", ["بدون", "نصف تشطيب", "تشطيب كامل", "سوبر لوكس"]
                )

                if st.form_submit_button("إضافة العقار"):
                    if p_name.strip():
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                "INSERT INTO properties (name, location, price, status, type, finishing) VALUES (?, ?, ?, ?, ?, ?)",
                                (
                                    p_name.strip(),
                                    p_loc.strip(),
                                    p_price,
                                    p_status,
                                    p_type,
                                    p_finishing,
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("✅ تم حفظ العقار بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")
                    else:
                        st.error("يرجى كتابة اسم العقار!")

        with tab3:
            st.subheader("💸 سجل مصروفات العقارات")
            props_df = safe_read_sql("SELECT id, name FROM properties")
            if not props_df.empty:
                prop_map = dict(zip(props_df["name"], props_df["id"]))
                with st.form("add_exp_form"):
                    selected_prop = st.selectbox(
                        "اختر العقار", list(prop_map.keys())
                    )
                    exp_type = st.text_input(
                        "نوع المصروف (مواد بناء، تراخيص...)"
                    )
                    exp_amount = st.number_input("المبلغ", min_value=0.0)
                    exp_notes = st.text_input("ملاحظات")

                    if st.form_submit_button("تسجيل المصروف"):
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                "INSERT INTO property_expenses (property_id, expense_type, amount, notes, date) VALUES (?, ?, ?, ?, ?)",
                                (
                                    prop_map[selected_prop],
                                    exp_type.strip(),
                                    exp_amount,
                                    exp_notes.strip(),
                                    str(datetime.date.today()),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("✅ تم تسجيل المصروف!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")

            st.dataframe(
                safe_read_sql(
                    "SELECT pe.id, p.name as property, pe.expense_type, pe.amount, pe.notes, pe.date FROM property_expenses pe JOIN properties p ON pe.property_id = p.id"
                ),
                use_container_width=True,
            )

    # -------------------------------------------------------------
    # 4. إدارة الموارد البشرية والعمالة اليومية
    # -------------------------------------------------------------
    elif page == "👷 إدارة الموارد البشرية والعمالة":
        st.title("👷 إدارة العمالة والموظفين والساعات")
        tab1, tab2, tab3 = st.tabs([
            "📋 سجل العمالة والموظفين",
            "➕ إضافة فرد / طقم عمالة",
            "⏱️ حاسبة الساعات واليوميات",
        ])

        with tab1:
            st.dataframe(
                safe_read_sql("SELECT * FROM employees"),
                use_container_width=True,
            )

        with tab2:
            with st.form("add_emp_form"):
                e_name = st.text_input("الاسم / اسم المقاول")
                e_pos = st.text_input("الوظيفة / الحرفة (حداد، نجار...)")
                e_type = st.selectbox(
                    "نوع التعيين",
                    ["موظف ثابت", "عامل يومية", "طقم عمالة / مقاول"],
                )
                e_craft = st.text_input("نوع الحرفة التفصيلي")
                workers_cnt = st.number_input(
                    "عدد العمال (إذا كان طقم)", min_value=1, value=1
                )
                pay_type = st.selectbox(
                    "نظام الدفع", ["شهري", "يومي", "بالساعة"]
                )
                rate = st.number_input("القيمة / الأجر (EGP)", min_value=0.0)

                if st.form_submit_button("حفظ البيانات"):
                    if e_name.strip():
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                """
                                INSERT INTO employees (name, position, emp_type, pay_type, total_pay, hire_date, workers_count, craft_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                                (
                                    e_name.strip(),
                                    e_pos.strip(),
                                    e_type,
                                    pay_type,
                                    rate,
                                    str(datetime.date.today()),
                                    workers_cnt,
                                    e_craft.strip(),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("✅ تم الحفظ بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")
                    else:
                        st.error("يرجى كتابة الاسم!")

        with tab3:
            st.subheader("⏱️ حاسبة المستحقات والعمل الإضافي")
            emp_df = safe_read_sql(
                "SELECT id, name, pay_type, total_pay FROM employees"
            )
            if not emp_df.empty:
                emp_map = dict(zip(emp_df["name"], emp_df["id"]))
                selected_emp = st.selectbox(
                    "اختر العامل / الموظف", list(emp_map.keys())
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    hrs = st.number_input("عدد الساعات المستحقة", min_value=0.0)
                    hr_rate = st.number_input("أجر الساعة", min_value=0.0)
                with col_b:
                    days = st.number_input("عدد أيام العمل", min_value=0.0)
                    day_rate = st.number_input("أجر اليوم", min_value=0.0)

                calc_total = (hrs * hr_rate) + (days * day_rate)
                st.markdown(
                    f"### 💵 المستحق الإجمالي: **{calc_total:,.2f} EGP**"
                )

    # -------------------------------------------------------------
    # 5. قسم المستثمرين وحاسبة الأرباح والخسائر المعقدة
    # -------------------------------------------------------------
    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين وحاسبة الأرباح والخسائر")
        tab1, tab2, tab3 = st.tabs([
            "➕ إضافة مستثمر",
            "📈 حاسبة الأرباح والتوزيعات",
            "💸 تسجيل المعاملات المالية (أرباح/خسائر)",
        ])

        with tab1:
            if "inv_msg_succ" in st.session_state:
                st.success(st.session_state.pop("inv_msg_succ"))
            if "inv_msg_err" in st.session_state:
                st.error(st.session_state.pop("inv_msg_err"))

            if "inv_form_key" not in st.session_state:
                st.session_state["inv_form_key"] = 0

            with st.form(f"add_inv_form_{st.session_state['inv_form_key']}"):
                inv_name = st.text_input("اسم المستثمر")
                inv_amount = st.number_input(
                    "مبلغ الاستثمار (EGP)", min_value=0.0
                )
                inv_rate = st.number_input(
                    "نسبة الربح السنوية (%)", min_value=0.0
                )
                inv_notes = st.text_input("ملاحظات")

                if st.form_submit_button("إضافة المستثمر"):
                    clean_inv_name = inv_name.strip()
                    if clean_inv_name and inv_amount > 0:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO investors (name, investment_amount, return_rate, start_date, notes)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                                (
                                    clean_inv_name,
                                    float(inv_amount),
                                    float(inv_rate),
                                    str(datetime.date.today()),
                                    inv_notes.strip(),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.session_state["inv_msg_succ"] = (
                                f"✅ تم حفظ المستثمر '{clean_inv_name}' بنجاح!"
                            )
                        except Exception as e:
                            st.session_state["inv_msg_err"] = (
                                f"❌ تعذر الحفظ: {e}"
                            )

                        st.session_state["inv_form_key"] += 1
                        st.rerun()
                    else:
                        st.error("يرجى كتابة اسم المستثمر ومبلغ أكبر من صفر!")

        with tab2:
            st.subheader("📊 حاسبة الأرباح وسجل المستثمرين")
            inv_df = safe_read_sql("SELECT * FROM investors")
            if not inv_df.empty:
                inv_df["الربح السنوي المتوقع (EGP)"] = inv_df[
                    "investment_amount"
                ] * (inv_df["return_rate"] / 100.0)
                inv_df["الربح الشهري المتوقع (EGP)"] = (
                    inv_df["الربح السنوي المتوقع (EGP)"] / 12.0
                )
                st.dataframe(inv_df, use_container_width=True)

                st.markdown("---")
                st.subheader("🧮 محاكاة التوزيع المباشر")
                total_pool = inv_df["investment_amount"].sum()
                net_profit = st.number_input(
                    "إجمالي صافي أرباح المشروع الحالية (EGP)", value=100000.0
                )

                if total_pool > 0:
                    inv_df["حصة المستثمر من الأرباح (EGP)"] = (
                        inv_df["investment_amount"] / total_pool
                    ) * net_profit
                    st.table(
                        inv_df[
                            [
                                "name",
                                "investment_amount",
                                "حصة المستثمر من الأرباح (EGP)",
                            ]
                        ]
                    )
            else:
                st.info("لا يوجد مستثمرون مسجلون حالياً.")

        with tab3:
            st.subheader("💸 تسجيل أرباح أو خسائر مستثمر")
            inv_df = safe_read_sql("SELECT id, name FROM investors")
            if not inv_df.empty:
                inv_map = dict(zip(inv_df["name"], inv_df["id"]))
                with st.form("inv_trans_form"):
                    sel_inv = st.selectbox(
                        "اختر المستثمر", list(inv_map.keys())
                    )
                    tr_type = st.selectbox(
                        "نوع المعاملة", ["أرباح موازية", "خسائر", "سحب رأس مال"]
                    )
                    tr_amount = st.number_input("المبلغ", min_value=0.0)
                    tr_desc = st.text_input("البيان / السبب")

                    if st.form_submit_button("حفظ المعاملة"):
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                "INSERT INTO investor_transactions (investor_id, trans_type, amount, description, date) VALUES (?, ?, ?, ?, ?)",
                                (
                                    inv_map[sel_inv],
                                    tr_type,
                                    tr_amount,
                                    tr_desc.strip(),
                                    str(datetime.date.today()),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("✅ تم تسجيل المعاملة!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")

                st.dataframe(
                    safe_read_sql(
                        "SELECT it.id, i.name as investor, it.trans_type, it.amount, it.description, it.date FROM investor_transactions it JOIN investors i ON it.investor_id = i.id"
                    ),
                    use_container_width=True,
                )

    # -------------------------------------------------------------
    # 6. قسم الدعم الفني IT Support
    # -------------------------------------------------------------
    elif page == "💻 قسم تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات وتذاكر الدعم")
        tab1, tab2 = st.tabs(["📋 تذاكر الدعم", "➕ فتح تذكرة جديدة"])

        with tab1:
            st.dataframe(
                safe_read_sql("SELECT * FROM it_tickets"),
                use_container_width=True,
            )

        with tab2:
            with st.form("add_ticket_form"):
                t_title = st.text_input("عنوان المشكلة / الطلب")
                t_cat = st.selectbox(
                    "القسم", ["شبكات", "أجهزة", "برمجيات ERP", "صلاحيات"]
                )

                if st.form_submit_button("إرسال التذكرة"):
                    if t_title.strip():
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                "INSERT INTO it_tickets (title, category, status, created_at) VALUES (?, ?, 'مفتوح', ?)",
                                (
                                    t_title.strip(),
                                    t_cat,
                                    datetime.datetime.now().strftime(
                                        "%Y-%m-%d %H:%M"
                                    ),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("✅ تم فتح التذكرة بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")
                    else:
                        st.error("يرجى كتابة عنوان التذكرة!")

    # -------------------------------------------------------------
    # 7. الأرشيف الإلكتروني والتقارير والمستندات
    # -------------------------------------------------------------
    elif page == "📑 التقارير وإدارة المستندات":
        st.title("📑 الأرشيف الإلكتروني وإدارة المستندات")
        tab1, tab2 = st.tabs(["📋 المستندات المحفوظة", "📤 رفع مستند جديد"])

        with tab1:
            docs_df = safe_read_sql(
                "SELECT id, file_name, category, upload_date, file_type FROM documents"
            )
            st.dataframe(docs_df, use_container_width=True)

        with tab2:
            uploaded_file = st.file_uploader(
                "اختر ملفاً لرفعه للأرشيف",
                type=["pdf", "png", "jpg", "xlsx", "docx"],
            )
            doc_cat = st.selectbox(
                "تصنيف المستند", ["عقود", "تراخيص", "فواتير", "مستندات شخصية"]
            )

            if st.button("رفع الملف وحفظه"):
                if uploaded_file is not None:
                    try:
                        file_bytes = uploaded_file.read()
                        conn = get_db_connection()
                        conn.execute(
                            "INSERT INTO documents (file_name, category, upload_date, file_data, file_type) VALUES (?, ?, ?, ?, ?)",
                            (
                                uploaded_file.name,
                                doc_cat,
                                str(datetime.date.today()),
                                file_bytes,
                                uploaded_file.type,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.success("✅ تم رفع وحفظ الملف بنجاح في قاعدة البيانات!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء الرفع: {e}")
                else:
                        st.error("يرجى اختيار ملف أولاً!")
