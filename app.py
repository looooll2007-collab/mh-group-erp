import base64
import datetime
import io
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

# --- Default Custom Login Settings in Session ---
if "login_config" not in st.session_state:
  st.session_state["login_config"] = {
      "title": "🏢 نظام إدارة MH Group ERP",
      "subtitle": "🔐 تسجيل الدخول للنظام",
      "btn_text": "تسجيل الدخول",
      "welcome_msg": "مرحباً بك! يرجى إدخال بياناتك للمتابعة.",
      "recovery_key": "123456",  # رمز استعادة كلمة السر الافتراضي
  }

# --- Preserve Theme Across Refresh via Query Params ---
if "theme" in st.query_params:
  saved_theme = st.query_params["theme"]
  if saved_theme in THEMES:
    st.session_state["selected_theme"] = saved_theme

if "selected_theme" not in st.session_state:
  st.session_state["selected_theme"] = "أزرق نيلي احترافي (Modern Indigo)"

current_theme = THEMES[st.session_state["selected_theme"]]

# --- Dynamic Inject Styles ---
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

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        """)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
      cursor.execute(
          "INSERT INTO users (username, password, role) VALUES ('admin',"
          " 'admin123', 'Admin')"
      )

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, location TEXT, price REAL, status TEXT
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

    # Auto Migration for Employees Table
    cursor.execute("PRAGMA table_info(employees)")
    columns = [col[1] for col in cursor.fetchall()]
    new_cols = {
        "emp_type": "TEXT",
        "pay_type": "TEXT",
        "hourly_rate": "REAL",
        "hours_worked": "REAL",
        "daily_rate": "REAL",
        "total_pay": "REAL",
        "workers_count": "INTEGER DEFAULT 1",
        "craft_type": "TEXT",
    }
    for col_name, col_type in new_cols.items():
      if col_name not in columns:
        cursor.execute(
            f"ALTER TABLE employees ADD COLUMN {col_name} {col_type}"
        )

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
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
                file_name TEXT, category TEXT, upload_date TEXT,
                file_data BLOB, file_type TEXT
            )
        """)

    # Auto Migration for Documents Table
    cursor.execute("PRAGMA table_info(documents)")
    doc_cols = [col[1] for col in cursor.fetchall()]
    if "file_data" not in doc_cols:
      cursor.execute("ALTER TABLE documents ADD COLUMN file_data BLOB")
    if "file_type" not in doc_cols:
      cursor.execute("ALTER TABLE documents ADD COLUMN file_type TEXT")

    conn.commit()


init_db()


# --- Safe Database Query Helper ---
def safe_read_sql(query):
  try:
    with sqlite3.connect("mh_group_erp.db") as conn:
      return pd.read_sql_query(query, conn)
  except Exception:
    return pd.DataFrame()


# --- Session Authentication State ---
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
  st.markdown(
      f"<h1 class='main-header'>{cfg['title']}</h1>", unsafe_allow_html=True
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.subheader(cfg["subtitle"])
    st.caption(cfg["welcome_msg"])

    if not st.session_state["show_forgot_password"]:
      # Normal Login Form
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
      # Recovery Form
      st.info("🔑 إعادة تعيين كلمة السر باستخدام رمز الاستعادة")
      rec_username = st.text_input("اسم المستخدم المتراد استعادة حسابه:")
      rec_key = st.text_input("رمز استعادة النظام (Recovery Key):", type="password", help="الرمز الافتراضي للنظام هو 123456")
      new_reset_pass = st.text_input("كلمة السر الجديدة:", type="password")
      confirm_reset_pass = st.text_input("تأكيد كلمة السر الجديدة:", type="password")

      rec_col1, rec_col2 = st.columns(2)
      with rec_col1:
        if st.button("تحديث كلمة السر", use_container_width=True):
          if not rec_username or not rec_key or not new_reset_pass:
            st.error("يرجى ملء جميع الحقول المطلوبة!")
          elif rec_key != cfg["recovery_key"]:
            st.error("رمز استعادة النظام غير صحيح!")
          elif new_reset_pass != confirm_reset_pass:
            st.error("كلمتا المرور غير متطابقتين!")
          else:
            with sqlite3.connect("mh_group_erp.db") as conn:
              cursor = conn.cursor()
              cursor.execute("SELECT id FROM users WHERE username = ?", (rec_username,))
              user_exists = cursor.fetchone()

              if user_exists:
                cursor.execute(
                    "UPDATE users SET password = ? WHERE username = ?",
                    (new_reset_pass, rec_username),
                )
                conn.commit()
                st.success("✅ تم تحديث كلمة السر بنجاح! يمكنك الان تسجيل الدخول.")
                st.session_state["show_forgot_password"] = False
              else:
                st.error("اسم المستخدم غير موجود بالنظام!")
      
      with rec_col2:
        if st.button("الرجوع لتسجيل الدخول", use_container_width=True):
          st.session_state["show_forgot_password"] = False
          st.rerun()


if not st.session_state["logged_in"]:
  login_page()
else:
  st.sidebar.title("🏢 MH Group ERP")

  # Sidebar Profile Picture & Info
  if st.session_state["profile_pic"]:
    st.sidebar.image(st.session_state["profile_pic"], width=90)

  st.sidebar.markdown(
      f"**المستخدم:** {st.session_state['username']}\n\n**الصلاحية:**"
      f" {st.session_state['user_role']}"
  )

  # 🔐 Role-Based Navigation Routing
  current_role = st.session_state["user_role"]

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
    dev_toggle = st.sidebar.checkbox(
        "🛠️ وضع المطور (Developer Mode)",
        value=st.session_state["is_developer"],
    )
    st.session_state["is_developer"] = dev_toggle
    if st.session_state["is_developer"]:
      menu_options.append("⚙️ إعدادات المطور والثيمات")

  elif current_role == "HR":
    menu_options.extend(
        ["👷 إدارة الموارد البشرية والعمالة", "📑 التقارير وإدارة المستندات"]
    )
    st.session_state["is_developer"] = False

  elif current_role == "Manager":
    menu_options.extend(
        ["🏡 إدارة العقارات والوحدات", "📑 التقارير وإدارة المستندات"]
    )
    st.session_state["is_developer"] = False

  elif current_role == "Accountant":
    menu_options.extend(
        ["💼 قسم المستثمرين والمالية", "📑 التقارير وإدارة المستندات"]
    )
    st.session_state["is_developer"] = False

  elif current_role == "IT":
    menu_options.extend(["💻 قسم تقنية المعلومات (IT Support)"])
    st.session_state["is_developer"] = False

  page = st.sidebar.radio("القائمة الرئيسية", menu_options)

  if st.sidebar.button("تسجيل الخروج"):
    st.session_state["logged_in"] = False
    st.rerun()

  # --- 1. Dashboard (Admin Only) ---
  if page == "📊 لوحة التحكم الرئيسية":
    st.markdown(
        "<h1 class='main-header'>📊 لوحة التحكم المتقدمة والملخص العام</h1>",
        unsafe_allow_html=True,
    )

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

    t_df = safe_read_sql(
        "SELECT COUNT(*) as count FROM it_tickets WHERE status != 'مغلق'"
    )
    open_tickets = t_df["count"][0] if not t_df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي العقارات المسجلة", f"{prop_count} وحدة")
    c2.metric("إجمالي العمالة والموظفين", f"{emp_count} فرد")
    c3.metric("حجم الاستثمارات", f"{total_inv:,.0f} EGP")
    c4.metric("تذاكر الدعم المفتوحة", f"{open_tickets} تذكرة")

    st.markdown("---")
    st.subheader("📌 التفاصيل السريعة للأقسام")
    col_a, col_b = st.columns(2)

    with col_a:
      st.markdown("### 👷 ملخص العمالة والموظفين")
      emp_summary = safe_read_sql(
          "SELECT emp_type as الفئة, COUNT(*) as العدد FROM employees GROUP BY"
          " emp_type"
      )
      st.dataframe(emp_summary, use_container_width=True)

    with col_b:
      st.markdown("### 🏡 ملخص حالة العقارات")
      prop_summary = safe_read_sql(
          "SELECT status as الحالة, COUNT(*) as العدد FROM properties GROUP BY"
          " status"
      )
      st.dataframe(prop_summary, use_container_width=True)

  # --- 2. Profile Section ---
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
      with st.form("edit_profile_form"):
        new_username = st.text_input(
            "اسم المستخدم الحالي:", value=st.session_state["username"]
        )
        st.text_input(
            "الصلاحية الحالية (للقراءة فقط):",
            value=st.session_state["user_role"],
            disabled=True,
        )

        if st.form_submit_button("حفظ التعديلات"):
          try:
            with sqlite3.connect("mh_group_erp.db") as conn:
              cursor = conn.cursor()
              cursor.execute(
                  "UPDATE users SET username = ? WHERE username = ?",
                  (new_username, st.session_state["username"]),
              )
              conn.commit()

            st.session_state["username"] = new_username
            st.success("تم تحديث اسم المستخدم بنجاح!")
            st.rerun()
          except sqlite3.IntegrityError:
            st.error("اسم المستخدم الجديد مستخدم بالفعل!")

    st.markdown("---")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
      st.markdown("### 🔐 تغيير كلمة المرور")
      with st.form("change_pass_form"):
        old_pass = st.text_input("كلمة المرور الحالية", type="password")
        new_pass = st.text_input("كلمة المرور الجديدة", type="password")
        confirm_pass = st.text_input(
            "تأكيد كلمة المرور الجديدة", type="password"
        )

        if st.form_submit_button("تحديث كلمة المرور"):
          if not old_pass or not new_pass or not confirm_pass:
            st.error("يرجى إدخال جميع الحقول!")
          elif new_pass != confirm_pass:
            st.error("كلمتا المرور غير متطابقتين!")
          else:
            with sqlite3.connect("mh_group_erp.db") as conn:
              cursor = conn.cursor()
              cursor.execute(
                  "SELECT password FROM users WHERE username = ?",
                  (st.session_state["username"],),
              )
              user_row = cursor.fetchone()

              if user_row and user_row[0] == old_pass:
                cursor.execute(
                    "UPDATE users SET password = ? WHERE username = ?",
                    (new_pass, st.session_state["username"]),
                )
                conn.commit()
                st.success("تم تحديث كلمة المرور بنجاح!")
              else:
                st.error("كلمة المرور الحالية غير صحيحة!")

    with col_p2:
      st.markdown("### 🎨 الثيم الشخصي المفضل")
      selected_theme_profile = st.selectbox(
          "اختر الثيم المفضل لحسابك:",
          list(THEMES.keys()),
          index=list(THEMES.keys()).index(st.session_state["selected_theme"]),
      )

      if selected_theme_profile != st.session_state["selected_theme"]:
        st.session_state["selected_theme"] = selected_theme_profile
        st.query_params["theme"] = selected_theme_profile
        st.success(f"تم حفظ وتطبيق ثيم: {selected_theme_profile}")
        st.rerun()

  # --- 3. Users Management (Admin Only) ---
  elif page == "👥 إدارة المستخدمين والصلاحيات":
    st.title("👥 إدارة المستخدمين والحسابات")
    tab1, tab2, tab3 = st.tabs(
        ["➕ إضافة مستخدم", "📋 قائمة المستخدمين", "❌ حذف مستخدم"]
    )

    with tab1:
      with st.form("add_user_form"):
        u_name = st.text_input("اسم المستخدم")
        u_pass = st.text_input("كلمة المرور", type="password")
        u_role = st.selectbox(
            "الصلاحية المحددة",
            ["Admin", "Manager", "HR", "IT", "Accountant"],
            help="تحدد الصلاحية الأقسام التي يمكن للمستخدم رؤيتها فقط.",
        )
        if st.form_submit_button("إضافة المستخدم"):
          if u_name and u_pass:
            try:
              with sqlite3.connect("mh_group_erp.db") as conn:
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?,"
                    " ?, ?)",
                    (u_name, u_pass, u_role),
                )
                conn.commit()
              st.success(
                  f"تم إضافة المستخدم '{u_name}' بصلاحية '{u_role}' بنجاح!"
              )
            except sqlite3.IntegrityError:
              st.error("اسم المستخدم مسجل مسبقاً!")

    with tab2:
      st.dataframe(
          safe_read_sql("SELECT id, username, role FROM users"),
          use_container_width=True,
      )

    with tab3:
      users_df = safe_read_sql(
          "SELECT id, username FROM users WHERE username != 'admin'"
      )
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
    st.title("🏡 إدارة العقارات والوحدات")
    tab1, tab2 = st.tabs(["➕ إضافة عقار", "❌ حذف عقار"])

    with tab1:
      with st.form("add_prop"):
        p_name = st.text_input("اسم العقار/الوحدة")
        p_loc = st.text_input("الموقع")
        p_price = st.number_input("السعر", min_value=0.0)
        p_stat = st.selectbox(
            "الحالة", ["متاح", "تم البيع", "تحت الإنشاء", "محجوز"]
        )
        if st.form_submit_button("حفظ"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute(
                "INSERT INTO properties (name, location, price, status) VALUES"
                " (?, ?, ?, ?)",
                (p_name, p_loc, p_price, p_stat),
            )
            conn.commit()
          st.success("تم الحفظ")

    with tab2:
      props_df = safe_read_sql("SELECT id, name FROM properties")
      if not props_df.empty:
        del_id = st.selectbox(
            "اختر العقار للحذف",
            props_df["id"],
            format_func=lambda x: props_df[props_df["id"] == x]["name"].values[
                0
            ],
        )
        if st.button("حذف العقار"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute("DELETE FROM properties WHERE id = ?", (del_id,))
            conn.commit()
          st.success("تم الحذف بنجاح")
          st.rerun()

    st.dataframe(
        safe_read_sql("SELECT * FROM properties"), use_container_width=True
    )

  # --- 5. HR Section (Updated for Workers & Crafts) ---
  elif page == "👷 إدارة الموارد البشرية والعمالة":
    st.title("👷 إدارة العمالة والموظفين والموردين")
    tab1, tab2 = st.tabs(["➕ إضافة موظف / مورد عمالة", "❌ حذف فرد"])

    with tab1:
      e_type = st.selectbox(
          "نوع الفئة المراد تسجيلها:", ["عامل", "مشرف", "مورد عمالة / مقاول"]
      )

      with st.form("add_emp_form"):
        e_name = st.text_input("اسم الفرد / اسم توريد المقاول")
        e_pos = st.text_input("المسمى الوظيفي / اسم الشركة أو المقاولة")

        w_count = 1
        c_type = "عامل عادي"

        if e_type == "مورد عمالة / مقاول":
          st.markdown("#### 🛠️ تفاصيل العمالة الموردة:")
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
                    e_name,
                    e_type,
                    e_pos,
                    p_type,
                    h_rate,
                    h_worked,
                    d_rate,
                    tot_pay,
                    str(datetime.date.today()),
                    w_count,
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
            format_func=lambda x: emp_df[emp_df["id"] == x]["name"].values[0],
        )
        if st.button("حذف البيانات"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute("DELETE FROM employees WHERE id = ?", (del_emp_id,))
            conn.commit()
          st.success("تم الحذف بنجاح")
          st.rerun()

    st.markdown("### 📋 سجل الموظفين والعمالة والموردين")
    st.dataframe(
        safe_read_sql(
            "SELECT id, name AS الاسم, emp_type AS الفئة, position AS الوظيفة,"
            " craft_type AS التخصص, workers_count AS عدد_العمالة, total_pay AS"
            " المستحق_المالي, hire_date AS التاريخ FROM employees"
        ),
        use_container_width=True,
    )

  # --- 6. Investors ---
  elif page == "💼 قسم المستثمرين والمالية":
    st.title("💼 قسم المستثمرين والرسوم البيانية")
    tab1, tab2 = st.tabs(["➕ إضافة مستثمر", "❌ حذف مستثمر"])

    with tab1:
      with st.form("add_inv"):
        i_name = st.text_input("اسم المستثمر")
        i_amount = st.number_input("مبلغ الاستثمار", min_value=0.0)
        i_rate = st.number_input("نسبة العائد (%)", min_value=0.0)
        if st.form_submit_button("تسجيل"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute(
                "INSERT INTO investors (name, investment_amount, return_rate,"
                " start_date) VALUES (?, ?, ?, ?)",
                (i_name, i_amount, i_rate, str(datetime.date.today())),
            )
            conn.commit()
          st.success("تم التسجيل")

    with tab2:
      inv_df = safe_read_sql("SELECT id, name FROM investors")
      if not inv_df.empty:
        del_inv_id = st.selectbox(
            "اختر المستثمر للحذف",
            inv_df["id"],
            format_func=lambda x: inv_df[inv_df["id"] == x]["name"].values[0],
        )
        if st.button("حذف المستثمر"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute("DELETE FROM investors WHERE id = ?", (del_inv_id,))
            conn.commit()
          st.success("تم الحذف")
          st.rerun()

    st.subheader("📈 الرسوم التوضيحية للاستثمارات")
    df_inv = safe_read_sql(
        "SELECT name, investment_amount, return_rate FROM investors"
    )

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
        t_cat = st.selectbox(
            "التصنيف", ["شبكات", "برمجيات", "أجهزة", "صلاحيات"]
        )
        t_stat = st.selectbox("الحالة", ["جديد", "قيد المعالجة", "مغلق"])
        if st.form_submit_button("إرسال"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute(
                "INSERT INTO it_tickets (title, category, status, created_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    t_title,
                    t_cat,
                    t_stat,
                    str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                ),
            )
            conn.commit()
          st.success("تم إرسال التذكرة")

    with tab2:
      t_df = safe_read_sql("SELECT id, title FROM it_tickets")
      if not t_df.empty:
        del_t_id = st.selectbox(
            "اختر التذكرة للحذف",
            t_df["id"],
            format_func=lambda x: t_df[t_df["id"] == x]["title"].values[0],
        )
        if st.button("حذف التذكرة"):
          with sqlite3.connect("mh_group_erp.db") as conn:
            conn.execute("DELETE FROM it_tickets WHERE id = ?", (del_t_id,))
            conn.commit()
          st.success("تم الحذف")
          st.rerun()

    st.dataframe(
        safe_read_sql("SELECT * FROM it_tickets"), use_container_width=True
    )

  # --- 8. Reports & Documents (Admin Preview Integrated) ---
  elif page == "📑 التقارير وإدارة المستندات":
    st.title("📑 التقارير ورفع الأرشيف والمستندات")

    tabs_list = ["📤 رفع وأرشفة المستندات", "📊 استخراج التقارير"]
    if current_role == "Admin":
      tabs_list.insert(1, "👁️ معاينة المستندات والأرشيف (خاص بالآدمن)")

    doc_tabs = st.tabs(tabs_list)

    # Tab 1: Uploading
    with doc_tabs[0]:
      st.subheader("📤 رفع مستند جديد إلى النظام")
      doc_cat = st.selectbox(
          "تصنيف المستند",
          [
              "عقود عمالة",
              "عقود مستثمرين",
              "أوراق عقارات",
              "فواتير ومستندات طوارئ",
          ],
      )
      uploaded_file = st.file_uploader(
          "اختر الملف لرفعه", type=["pdf", "docx", "png", "jpg", "xlsx", "txt"]
      )

      if uploaded_file and st.button("حفظ المستند بالمؤرشف"):
        file_bytes = uploaded_file.getvalue()
        file_type = uploaded_file.type

        with sqlite3.connect("mh_group_erp.db") as conn:
          conn.execute(
              "INSERT INTO documents (file_name, category, upload_date,"
              " file_data, file_type) VALUES (?, ?, ?, ?, ?)",
              (
                  uploaded_file.name,
                  doc_cat,
                  str(datetime.date.today()),
                  file_bytes,
                  file_type,
              ),
          )
          conn.commit()
        st.success(
            f"تم رفع المستند '{uploaded_file.name}' وأرشفته بنجاح!"
        )

      st.markdown("---")
      st.subheader("📂 الأرشيف الحالي للمستندات")
      docs_df = safe_read_sql(
          "SELECT id, file_name, category, upload_date FROM documents"
      )
      st.dataframe(docs_df, use_container_width=True)

    # Tab 2: Admin Preview ONLY
    if current_role == "Admin":
      with doc_tabs[1]:
        st.subheader("👁️ معاينة وتحميل المستندات المؤرشفة (خاص بالأدمن)")

        with sqlite3.connect("mh_group_erp.db") as conn:
          cursor = conn.cursor()
          cursor.execute(
              "SELECT id, file_name, category, upload_date, file_data,"
              " file_type FROM documents"
          )
          all_docs = cursor.fetchall()

        if all_docs:
          doc_dict = {
              f"[{doc[0]}] {doc[1]} - ({doc[2]})": doc for doc in all_docs
          }
          selected_doc_key = st.selectbox("اختر المستند للمعاينة:", list(doc_dict.keys()))
          doc_data = doc_dict[selected_doc_key]

          d_id, d_name, d_cat, d_date, d_bytes, d_type = doc_data

          st.write(f"**اسم الملف:** {d_name}")
          st.write(f"**التصنيف:** {d_cat}")
          st.write(f"**تاريخ الرفع:** {d_date}")

          if d_bytes:
            if d_type and "image" in d_type:
              st.image(
                  d_bytes, caption=d_name, use_container_width=True
              )
            elif d_type and "text" in d_type:
              st.text_area(
                  "محتوى الملف:",
                  d_bytes.decode("utf-8", errors="ignore"),
                  height=200,
              )
            else:
              st.info(
                  "لا تتوفر معاينة صوَرية مباشرة لهذا النوع من الملفات (PDF/Word/Excel)."
              )

            st.download_button(
                label=f"⬇️ تحميل الملف ({d_name})",
                data=d_bytes,
                file_name=d_name,
                mime=d_type if d_type else "application/octet-stream",
            )
          else:
            st.warning("الملف القديم لا يحتوي على بيانات باينري للمعاينة.")
        else:
          st.info("لا توجد مستندات مرفوعة في النظام حالياً.")

    # Tab 3: Reports
    report_tab_index = 2 if current_role == "Admin" else 1
    with doc_tabs[report_tab_index]:
      st.subheader("📊 استخراج التقرير الشامل")
      rep_type = st.selectbox(
          "اختر نوع التقرير",
          ["عقارات", "موظفين وعمالة", "مستثمرين", "دعم IT"],
      )

      if rep_type == "عقارات":
        df = safe_read_sql("SELECT * FROM properties")
      elif rep_type == "موظفين وعمالة":
        df = safe_read_sql(
            "SELECT id, name, emp_type, position, craft_type, workers_count,"
            " total_pay, hire_date FROM employees"
        )
      elif rep_type == "مستثمرين":
        df = safe_read_sql("SELECT * FROM investors")
      else:
        df = safe_read_sql("SELECT * FROM it_tickets")

      st.dataframe(df, use_container_width=True)
      st.download_button(
          "📥 تحميل التقرير بصيغة CSV",
          data=df.to_csv(index=False).encode("utf-8"),
          file_name=f"{rep_type}.csv",
      )

  # --- 9. Developer & Themes (Admin Only) ---
  elif page == "⚙️ إعدادات المطور والثيمات" and current_role == "Admin":
    st.title("⚙️ لوحة تحكم المطور والثيمات")

    tab_dev1, tab_dev2 = st.tabs(
        ["🎨 اختيار الثيم العام", "🔐 التعديل على شاشة الدخول والأمان"]
    )

    with tab_dev1:
      selected_theme_name = st.selectbox(
          "اختر ثيم لوحة التحكم (سيتم حفظه حتى بعد الـ Refresh):",
          list(THEMES.keys()),
          index=list(THEMES.keys()).index(st.session_state["selected_theme"]),
      )

      if selected_theme_name != st.session_state["selected_theme"]:
        st.session_state["selected_theme"] = selected_theme_name
        st.query_params["theme"] = selected_theme_name
        st.success(f"تم تطبيق وحفظ ثيم: {selected_theme_name}")
        st.rerun()

    with tab_dev2:
      st.subheader("🔑 تخصيص نصوص وشاشة تسجيل الدخول ورمز الاستعادة")
      cfg = st.session_state["login_config"]

      with st.form("custom_login_form"):
        title_in = st.text_input("العنوان الرئيسي لشاشة الدخول:", value=cfg["title"])
        subtitle_in = st.text_input(
            "العنوان الفرعي:", value=cfg["subtitle"]
        )
        welcome_in = st.text_input(
            "الرسالة الترحيبية / التعليمات:", value=cfg["welcome_msg"]
        )
        btn_in = st.text_input("نص زر الدخول:", value=cfg["btn_text"])
        rec_key_in = st.text_input("رمز استعادة النظام (Recovery Key):", value=cfg["recovery_key"], help="هذا الرمز يتم استخدامه في حالة نسيان كلمة المرور")

        if st.form_submit_button("حفظ إعدادات الأمان وشاشة الدخول"):
          st.session_state["login_config"] = {
              "title": title_in,
              "subtitle": subtitle_in,
              "btn_text": btn_in,
              "welcome_msg": welcome_in,
              "recovery_key": rec_key_in,
          }
          st.success(
              "تم حفظ إعدادات الأمان وشاشة الدخول بنجاح!"
          )
