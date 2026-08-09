import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="MH GROUP ERP SYSTEM",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",  # إخفاء القائمة الجانبية أثناء تسجيل الدخول
)

# ==========================================
# 2. تصميم CSS مطاطي ودقيق يطابق الصورة 100%
# ==========================================
st.markdown(
    """
<style>
    /* خلفية الصفحة كاملة باللون الأسود الملكي */
    .stApp {
        background-color: #0B0E14 !important;
        color: #F8FAFC !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* إخفاء الهيدر الافتراضي لـ Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* تصميم الحاوية اليسرى (بطاقة التعريف والترحيب) */
    .hero-container {
        padding: 40px 20px;
    }
    .brand-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 40px;
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 1px;
    }
    .brand-sub {
        font-size: 0.8rem;
        color: #D97706;
        font-weight: 600;
        letter-spacing: 2px;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 900;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .hero-title-gold {
        font-size: 2.8rem;
        font-weight: 900;
        color: #D97706;
        margin-top: 0px;
        margin-bottom: 15px;
    }
    .hero-desc {
        color: #94A3B8;
        font-size: 1.1rem;
        line-height: 1.6;
        margin-bottom: 40px;
    }

    /* بطاقات المزايا الأربع أسفل اليسار */
    .feature-card {
        background-color: #121824;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        border-color: #D97706;
    }
    .feature-icon {
        font-size: 1.4rem;
        color: #D97706;
        margin-bottom: 6px;
    }
    .feature-head {
        font-weight: 700;
        font-size: 0.85rem;
        color: #F8FAFC;
    }
    .feature-sub {
        font-size: 0.7rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* كرت نموذج تسجيل الدخول (اليمين) */
    .login-card {
        background-color: #111622;
        border: 1px solid #1E293B;
        border-radius: 20px;
        padding: 40px 35px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    
    /* تخصيص مدخلات النصوص لتبدو مطابقة للصورة */
    .stTextInput input {
        background-color: #1A202C !important;
        color: #FFFFFF !important;
        border: 1px solid #2D3748 !important;
        border-radius: 10px !important;
        height: 50px !important;
        padding-right: 15px !important;
    }
    .stTextInput input:focus {
        border-color: #D97706 !important;
        box-shadow: 0 0 0 1px #D97706 !important;
    }
    
    /* الزر الذهبي العريض للتسجيل */
    .stButton>button {
        background: linear-gradient(90deg, #B45309 0%, #D97706 50%, #F59E0B 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        height: 52px !important;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3) !important;
    }

    /* الشريط الجانبي بعد الدخول */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. إعداد قاعدة البيانات الدائمة وقيم الصلاحيات الحقيقية
# ==========================================
DB_FILE = "mh_group_erp.db"


def init_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # جدول المستخدمين الحقيقي
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password TEXT NOT NULL,
                department TEXT NOT NULL
            )
        """)

        # جدول بيانات العقارات الدائم
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT,
                price REAL,
                status TEXT,
                created_by TEXT
            )
        """)

        # إنشاء الحساب الرئيسي إذا لم يكن موجوداً
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (username, email, phone, password, department)
                VALUES ('admin', 'admin@mhgroup.com', '01000000000', 'admin123', 'المدير العام')
            """)
        conn.commit()


init_database()

# ==========================================
# 4. التحكم بحالة الجلسة
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_data" not in st.session_state:
    st.session_state["user_data"] = {}


# ==========================================
# 5. واجهة تسجيل الدخول (المطابقة للصورة)
# ==========================================
def render_login_view():
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_space, c_right = st.columns([1.2, 0.1, 1])

    # --- الجزء الأيسر: الشعار والمميزات والترحيب ---
    with c_left:
        st.markdown(
            """
        <div class="hero-container">
            <div class="brand-logo">
                <div style="font-size: 2.2rem; color: #D97706; font-weight: bold;">M</div>
                <div>
                    <div class="brand-title">MH GROUP</div>
                    <div class="brand-sub">ERP SYSTEM</div>
                </div>
            </div>
            
            <div class="hero-title">مرحباً بك في</div>
            <div class="hero-title-gold">MH GROUP ERP</div>
            <div class="hero-desc">
                نظام متكامل لإدارة أعمال الاستثمار والتطوير العقاري بكفاءة واحترافية عالية.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # المزايا الـ 4 السفليّة
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            st.markdown(
                """<div class="feature-card"><div class="feature-icon">🏢</div><div class="feature-head">إدارة شاملة</div><div class="feature-sub">جميع عملياتك في مكان واحد</div></div>""",
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                """<div class="feature-card"><div class="feature-icon">🕒</div><div class="feature-head">تقارير دقيقة</div><div class="feature-sub">تقارير وتحليلات لحظية</div></div>""",
                unsafe_allow_html=True,
            )
        with f3:
            st.markdown(
                """<div class="feature-card"><div class="feature-icon">🛡️</div><div class="feature-head">أمان عالٍ</div><div class="feature-sub">حماية بياناتك على أعلى مستوى</div></div>""",
                unsafe_allow_html=True,
            )
        with f4:
            st.markdown(
                """<div class="feature-card"><div class="feature-icon">📊</div><div class="feature-head">إدارة ذكية</div><div class="feature-sub">لوحة تحكم متكاملة</div></div>""",
                unsafe_allow_html=True,
            )

    # --- الجزء الأيمن: نموذج الدخول ---
    with c_right:
        st.markdown(
            """
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 2.5rem; color: #D97706;">👑</div>
            <h2 style="color: #FFFFFF; font-weight: 800; margin: 0;">تسجيل الدخول</h2>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 5px;">مرحباً بك، يرجى تسجيل الدخول للوصول إلى حسابك</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # مدخلات البيانات الحقيقية
        user_input = st.text_input(
            "اسم المستخدم أو البريد الإلكتروني",
            placeholder="أدخل اسم المستخدم أو البريد",
        )
        pass_input = st.text_input(
            "كلمة المرور", type="password", placeholder="أدخل كلمة المرور"
        )

        r_col, f_col = st.columns(2)
        with r_col:
            st.checkbox("تذكرني")
        with f_col:
            st.markdown(
                "<div style='text-align: left;'><a href='#' style='color: #D97706; text-decoration: none; font-size: 0.85rem;'>نسيت كلمة المرور؟</a></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # زر الدخول والتحقق من قاعدة البيانات
        if st.button("تسجيل الدخول ➔", use_container_width=True):
            if not user_input or not pass_input:
                st.error("يرجى ملء جميع الحقول المطلوب!")
            else:
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT username, email, phone, department FROM users 
                        WHERE (username = ? OR email = ?) AND password = ?
                    """,
                        (user_input, user_input, pass_input),
                    )
                    user = cursor.fetchone()

                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user_data"] = {
                        "username": user[0],
                        "email": user[1],
                        "phone": user[2],
                        "department": user[3],
                    }
                    st.success("تم التوثيق بنجاح! جاري التوجيه...")
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة!")

        st.markdown(
            """
        <div style="text-align: center; margin: 20px 0 10px 0; color: #64748B; font-size: 0.8rem;">
            أو تسجيل الدخول باستخدام
        </div>
        """,
            unsafe_allow_html=True,
        )

        g_btn, m_btn = st.columns(2)
        with g_btn:
            st.button("🌐 Google", use_container_width=True)
        with m_btn:
            st.button("💻 Microsoft", use_container_width=True)

        st.markdown(
            """
        <div style="text-align: center; margin-top: 25px; color: #475569; font-size: 0.75rem;">
            جميع الحقوق محفوظة © MH Group 2026
        </div>
        """,
            unsafe_allow_html=True,
        )


# ==========================================
# 6. الداشبورد بعد الدخول وتوزيع الصلاحيات الأقسام
# ==========================================
if not st.session_state["logged_in"]:
    render_login_view()
else:
    user_dept = st.session_state["user_data"]["department"]
    username = st.session_state["user_data"]["username"]

    # القائمة الجانبية المخصصة للموظف
    st.sidebar.title("MH GROUP ERP")
    st.sidebar.markdown(f"👤 **المستخدم:** {username}")
    st.sidebar.markdown(f"🏢 **القسم:** `{user_dept}`")
    st.sidebar.markdown("---")

    # تحديد الشاشات المتاحة حسب صلاحيات القسم
    if user_dept == "المدير العام":
        allowed_pages = [
            "لوحة التحكم العامة",
            "إدارة العقارات",
            "الإدارة المالية",
            "الموارد البشرية",
            "إدارة حسابات وصلاحيات الموظفين",
        ]
    else:
        allowed_pages = ["لوحة التحكم", user_dept]

    selected_page = st.sidebar.radio("أقسام النظام", allowed_pages)

    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.session_state["user_data"] = {}
        st.rerun()

    # --- الشاشات بناء على الاختيار ---
    if "إدارة حسابات وصلاحيات الموظفين" in selected_page:
        st.title("🔐 إدارة صلاحيات الموظفين والحسابات")
        st.subheader("إضافة موظف جديد وتحديد قسمه")

        with st.form("create_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                u_name = st.text_input("اسم المستخدم (Username)")
                u_email = st.text_input("البريد الإلكتروني")
                u_phone = st.text_input("رقم الهاتف")
            with col2:
                u_pass = st.text_input("كلمة السر", type="password")
                u_dept = st.selectbox(
                    "القسم المخصص له",
                    [
                        "قسم العقارات والمشروعات",
                        "قسم الإدارة المالية",
                        "قسم الموارد البشرية",
                        "قسم IT Support",
                        "المدير العام",
                    ],
                )

            if st.form_submit_button("حفظ الحساب وتفعيل الصلاحية"):
                if u_name and u_email and u_pass:
                    try:
                        with sqlite3.connect(DB_FILE) as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO users (username, email, phone, password, department)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                                (u_name, u_email, u_phone, u_pass, u_dept),
                            )
                            conn.commit()
                        st.success(
                            f"تم تسجيل الموظف '{u_name}' وتخصيص قسم '{u_dept}' له بنجاح!"
                        )
                    except Exception as e:
                        st.error("خطأ: اسم المستخدم أو البريد مسجل مسبقاً!")

        st.subheader("سجل الموظفين المسجلين حالياً")
        with sqlite3.connect(DB_FILE) as conn:
            df_users = pd.read_sql_query(
                "SELECT id, username AS 'اسم المستخدم', email AS 'البريد', phone AS 'الهاتف', department AS 'القسم المخصص' FROM users",
                conn,
            )
        st.dataframe(df_users, use_container_width=True)

    else:
        st.title(f"📍 {selected_page}")
        st.info(
            f"مرحباً بك في {selected_page}. تم تصفية الواجهة خصيصاً بناءً على قسمك المسجل: ({user_dept})."
        )
