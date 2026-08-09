import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- Theme Palette Configuration ---
THEMES = {
    "أزرق نيلي احترافي (Modern Indigo)": {
        "primary": "#4F46E5",
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "text": "#1E293B",
        "accent": "#6366F1",
        "border": "#E2E8F0"
    },
    "الداكن الملكي والذهبي (Royal Dark & Gold)": {
        "primary": "#D97706",
        "bg": "#0F172A",
        "card": "#1E293B",
        "text": "#F8FAFC",
        "accent": "#F59E0B",
        "border": "#334155"
    },
    "أخضر زمردي فخم (Emerald Slate)": {
        "primary": "#059669",
        "bg": "#F4FBF7",
        "card": "#FFFFFF",
        "text": "#064E3B",
        "accent": "#10B981",
        "border": "#D1FAE5"
    },
    "عنابي فاخر (Burgundy Premium)": {
        "primary": "#881337",
        "bg": "#FFF1F2",
        "card": "#FFFFFF",
        "text": "#4C0519",
        "accent": "#E11D48",
        "border": "#FFE4E6"
    }
}

# --- Preserve Theme Across Refresh via Query Params ---
query_params = st.query_params
saved_theme = query_params.get("theme", "أزرق نيلي احترافي (Modern Indigo)")

if saved_theme not in THEMES:
    saved_theme = "أزرق نيلي احترافي (Modern Indigo)"

if "selected_theme" not in st.session_state:
    st.session_state["selected_theme"] = saved_theme

current_theme = THEMES[st.session_state["selected_theme"]]

# --- Page Configuration ---
st.set_page_config(
    page_title="MH Group ERP System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Dynamic Inject Styles ---
st.markdown(f"""
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
""", unsafe_allow_html=True)

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect("mh_group_erp.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, location TEXT, price REAL, status TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, emp_type TEXT, position TEXT, pay_type TEXT,
            hourly_rate REAL, hours_worked REAL, daily_rate REAL, total_pay REAL, hire_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, investment_amount REAL, return_rate REAL, start_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, category TEXT, status TEXT, created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT, category TEXT, upload_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- Session Authentication State ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "is_developer" not in st.session_state:
    st.session_state["is_developer"] = False

def login_page():
    st.markdown("<h1 class='main-header'>🏢 نظام إدارة MH Group ERP</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 تسجيل الدخول")
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        login_btn = st.button("دخول", use_container_width=True)
        
        if login_btn:
            conn = sqlite3.connect("mh_group_erp.db")
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username_input, password_input))
            res = cursor.fetchone()
            conn.close()
            
            if res:
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = res[0]
                st.session_state["username"] = username_input
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة!")

if not st.session_state["logged_in"]:
    login_page()
else:
    st.sidebar.title("🏢 MH Group ERP")
    st.sidebar.markdown(f"**المستخدم:** {st.session_state['username']} ({st.session_state['user_role']})")
    
    dev_toggle = st.sidebar.checkbox("🛠️ وضع المطور (Developer Mode)", value=st.session_state["is_developer"])
    st.session_state["is_developer"] = dev_toggle

    menu_options = [
        "📊 لوحة التحكم الرئيسية",
        "👥 إدارة المستخدمين والصلاحيات",
        "🏡 إدارة العقارات والوحدات",
        "👷 إدارة الموارد البشرية والعمالة",
        "💼 قسم المستثمرين والمالية",
        "💻 قسم تقنية المعلومات (IT Support)",
        "📑 التقارير وإدارة المستندات"
    ]

    if st.session_state["is_developer"]:
        menu_options.append("⚙️ إعدادات المطور والثيمات")

    page = st.sidebar.radio("القائمة الرئيسية", menu_options)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- 1. Dashboard ---
    if page == "📊 لوحة التحكم الرئيسية":
        st.markdown("<h1 class='main-header'>📊 لوحة التحكم المتقدمة والملخص العام</h1>", unsafe_allow_html=True)
        
        conn = sqlite3.connect("mh_group_erp.db")
        prop_count = pd.read_sql_query("SELECT COUNT(*) as count FROM properties", conn)['count'][0]
        emp_count = pd.read_sql_query("SELECT COUNT(*) as count FROM employees", conn)['count'][0]
        total_inv = pd.read_sql_query("SELECT SUM(investment_amount) as sum FROM investors", conn)['sum'][0] or 0
        open_tickets = pd.read_sql_query("SELECT COUNT(*) as count FROM it_tickets WHERE status != 'مغلق'", conn)['count'][0]
        conn.close()

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
            conn = sqlite3.connect("mh_group_erp.db")
            emp_summary = pd.read_sql_query("SELECT emp_type, COUNT(*) as العدد FROM employees GROUP BY emp_type", conn)
            conn.close()
            st.dataframe(emp_summary, use_container_width=True)

        with col_b:
            st.markdown("### 🏡 ملخص حالة العقارات")
            conn = sqlite3.connect("mh_group_erp.db")
            prop_summary = pd.read_sql_query("SELECT status as الحالة, COUNT(*) as العدد FROM properties GROUP BY status", conn)
            conn.close()
            st.dataframe(prop_summary, use_container_width=True)

    # --- 2. Users Management ---
    elif page == "👥 إدارة المستخدمين والصلاحيات":
        st.title("👥 إدارة المستخدمين والحسابات")
        tab1, tab2, tab3 = st.tabs(["➕ إضافة مستخدم", "📋 قائمة المستخدمين", "❌ حذف مستخدم"])
        
        with tab1:
            with st.form("add_user_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة المرور", type="password")
                u_role = st.selectbox("الصلاحية", ["Admin", "Manager", "HR", "IT", "Accountant"])
                if st.form_submit_button("إضافة"):
                    if u_name and u_pass:
                        conn = sqlite3.connect("mh_group_erp.db")
                        try:
                            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (u_name, u_pass, u_role))
                            conn.commit()
                            st.success("تم إضافة المستخدم بنجاح")
                        except:
                            st.error("اسم المستخدم مسجل مسبقاً")
                        finally:
                            conn.close()

        with tab2:
            conn = sqlite3.connect("mh_group_erp.db")
            st.dataframe(pd.read_sql_query("SELECT id, username, role FROM users", conn), use_container_width=True)
            conn.close()

        with tab3:
            conn = sqlite3.connect("mh_group_erp.db")
            users_df = pd.read_sql_query("SELECT id, username FROM users WHERE username != 'admin'", conn)
            conn.close()
            if not users_df.empty:
                del_user = st.selectbox("اختر المستخدم للحذف:", users_df["username"])
                if st.button("حذف الحساب المحدد"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("DELETE FROM users WHERE username = ?", (del_user,))
                    conn.commit()
                    conn.close()
                    st.success(f"تم حذف الحساب {del_user}")
                    st.rerun()

    # --- 3. Properties ---
    elif page == "🏡 إدارة العقارات والوحدات":
        st.title("🏡 إدارة العقارات والوحدات")
        tab1, tab2 = st.tabs(["➕ إضافة عقار", "❌ حذف عقار"])
        
        with tab1:
            with st.form("add_prop"):
                p_name = st.text_input("اسم العقار/الوحدة")
                p_loc = st.text_input("الموقع")
                p_price = st.number_input("السعر", min_value=0.0)
                p_stat = st.selectbox("الحالة", ["متاح", "تم البيع", "تحت الإنشاء", "محجوز"])
                if st.form_submit_button("حفظ"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("INSERT INTO properties (name, location, price, status) VALUES (?, ?, ?, ?)", (p_name, p_loc, p_price, p_stat))
                    conn.commit()
                    conn.close()
                    st.success("تم الحفظ")

        with tab2:
            conn = sqlite3.connect("mh_group_erp.db")
            props_df = pd.read_sql_query("SELECT id, name FROM properties", conn)
            conn.close()
            if not props_df.empty:
                del_id = st.selectbox("اختر العقار للحذف", props_df["id"], format_func=lambda x: props_df[props_df['id']==x]['name'].values[0])
                if st.button("حذف العقار"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("DELETE FROM properties WHERE id = ?", (del_id,))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف بنجاح")
                    st.rerun()

        conn = sqlite3.connect("mh_group_erp.db")
        st.dataframe(pd.read_sql_query("SELECT * FROM properties", conn), use_container_width=True)
        conn.close()

    # --- 4. HR Section ---
    elif page == "👷 إدارة الموارد البشرية والعمالة":
        st.title("👷 إدارة العمالة والموظفين والموردين")
        tab1, tab2 = st.tabs(["➕ إضافة موظف/عامل/مورد", "❌ حذف فرد"])
        
        with tab1:
            with st.form("add_emp"):
                e_name = st.text_input("الاسم")
                e_type = st.selectbox("نوع الفئة", ["عامل", "مشرف", "مورد"])
                e_pos = st.text_input("المسمى الوظيفي / مجال التوريد")
                p_type = st.radio("نظام الحساب", ["بالساعة", "يومية أساسية"])
                
                c1, c2 = st.columns(2)
                h_rate = c1.number_input("سعر الساعة", min_value=0.0)
                h_worked = c2.number_input("عدد الساعات", min_value=0.0)
                d_rate = st.number_input("سعر اليومية الأساسية", min_value=0.0)
                
                if st.form_submit_button("حفظ البيانات"):
                    tot_pay = (h_rate * h_worked) if p_type == "بالساعة" else d_rate
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute('''INSERT INTO employees 
                        (name, emp_type, position, pay_type, hourly_rate, hours_worked, daily_rate, total_pay, hire_date) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (e_name, e_type, e_pos, p_type, h_rate, h_worked, d_rate, tot_pay, str(datetime.date.today())))
                    conn.commit()
                    conn.close()
                    st.success(f"تم الحفظ! إجمالي المستحق: {tot_pay} EGP")

        with tab2:
            conn = sqlite3.connect("mh_group_erp.db")
            emp_df = pd.read_sql_query("SELECT id, name FROM employees", conn)
            conn.close()
            if not emp_df.empty:
                del_emp_id = st.selectbox("اختر الفرد للحذف", emp_df["id"], format_func=lambda x: emp_df[emp_df['id']==x]['name'].values[0])
                if st.button("حذف البيانات"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("DELETE FROM employees WHERE id = ?", (del_emp_id,))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف")
                    st.rerun()

        conn = sqlite3.connect("mh_group_erp.db")
        st.dataframe(pd.read_sql_query("SELECT * FROM employees", conn), use_container_width=True)
        conn.close()

    # --- 5. Investors ---
    elif page == "💼 قسم المستثمرين والمالية":
        st.title("💼 قسم المستثمرين والرسوم البيانية")
        tab1, tab2 = st.tabs(["➕ إضافة مستثمر", "❌ حذف مستثمر"])
        
        with tab1:
            with st.form("add_inv"):
                i_name = st.text_input("اسم المستثمر")
                i_amount = st.number_input("مبلغ الاستثمار", min_value=0.0)
                i_rate = st.number_input("نسبة العائد (%)", min_value=0.0)
                if st.form_submit_button("تسجيل"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("INSERT INTO investors (name, investment_amount, return_rate, start_date) VALUES (?, ?, ?, ?)",
                                 (i_name, i_amount, i_rate, str(datetime.date.today())))
                    conn.commit()
                    conn.close()
                    st.success("تم التسجيل")

        with tab2:
            conn = sqlite3.connect("mh_group_erp.db")
            inv_df = pd.read_sql_query("SELECT id, name FROM investors", conn)
            conn.close()
            if not inv_df.empty:
                del_inv_id = st.selectbox("اختر المستثمر للحذف", inv_df["id"], format_func=lambda x: inv_df[inv_df['id']==x]['name'].values[0])
                if st.button("حذف المستثمر"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("DELETE FROM investors WHERE id = ?", (del_inv_id,))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف")
                    st.rerun()

        st.subheader("📈 الرسوم التوضيحية للاستثمارات")
        conn = sqlite3.connect("mh_group_erp.db")
        df_inv = pd.read_sql_query("SELECT name, investment_amount, return_rate FROM investors", conn)
        conn.close()
        
        if not df_inv.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### توزيع حجم الاستثمارات")
                st.bar_chart(df_inv.set_index("name")["investment_amount"])
            with c2:
                st.markdown("#### نسبة العائد لكل مستثمر (%)")
                st.line_chart(df_inv.set_index("name")["return_rate"])
            st.dataframe(df_inv, use_container_width=True)

    # --- 6. IT Support ---
    elif page == "💻 قسم تقنية المعلومات (IT Support)":
        st.title("💻 قسم تقنية المعلومات والدعم الفني")
        tab1, tab2 = st.tabs(["➕ تذكرة جديدة", "❌ حذف تذكرة"])
        
        with tab1:
            with st.form("add_t"):
                t_title = st.text_input("عنوان المشكلة")
                t_cat = st.selectbox("التصنيف", ["شبكات", "برمجيات", "أجهزة", "صلاحيات"])
                t_stat = st.selectbox("الحالة", ["جديد", "قيد المعالجة", "مغلق"])
                if st.form_submit_button("إرسال"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("INSERT INTO it_tickets (title, category, status, created_at) VALUES (?, ?, ?, ?)",
                                 (t_title, t_cat, t_stat, str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))))
                    conn.commit()
                    conn.close()
                    st.success("تم إرسال التذكرة")

        with tab2:
            conn = sqlite3.connect("mh_group_erp.db")
            t_df = pd.read_sql_query("SELECT id, title FROM it_tickets", conn)
            conn.close()
            if not t_df.empty:
                del_t_id = st.selectbox("اختر التذكرة للحذف", t_df["id"], format_func=lambda x: t_df[t_df['id']==x]['title'].values[0])
                if st.button("حذف التذكرة"):
                    conn = sqlite3.connect("mh_group_erp.db")
                    conn.execute("DELETE FROM it_tickets WHERE id = ?", (del_t_id,))
                    conn.commit()
                    conn.close()
                    st.success("تم الحذف")
                    st.rerun()

        conn = sqlite3.connect("mh_group_erp.db")
        st.dataframe(pd.read_sql_query("SELECT * FROM it_tickets", conn), use_container_width=True)
        conn.close()

    # --- 7. Reports & Documents ---
    elif page == "📑 التقارير وإدارة المستندات":
        st.title("📑 التقارير ورفع المستندات")
        
        tab1, tab2 = st.tabs(["📤 رفع وأرشفة المستندات", "📊 استخراج التقارير"])
        
        with tab1:
            st.subheader("📤 رفع مستند جديد إلى النظام")
            doc_cat = st.selectbox("تصنيف المستند", ["عقود عمالة", "عقود مستثمرين", "أوراق عقارات", "فواتير ومستندات طوارئ"])
            uploaded_file = st.file_uploader("اختر الملف لرفعه", type=["pdf", "docx", "png", "jpg", "xlsx"])
            
            if uploaded_file and st.button("حفظ المستند"):
                conn = sqlite3.connect("mh_group_erp.db")
                conn.execute("INSERT INTO documents (file_name, category, upload_date) VALUES (?, ?, ?)",
                             (uploaded_file.name, doc_cat, str(datetime.date.today())))
                conn.commit()
                conn.close()
                st.success(f"تم رفع المستند '{uploaded_file.name}' وأرشفته بنجاح!")

            st.markdown("---")
            st.subheader("📂 الأرشيف الحالي للمستندات")
            conn = sqlite3.connect("mh_group_erp.db")
            docs_df = pd.read_sql_query("SELECT * FROM documents", conn)
            conn.close()
            st.dataframe(docs_df, use_container_width=True)

        with tab2:
            st.subheader("📊 استخراج التقرير الشامل")
            rep_type = st.selectbox("اختر نوع التقرير", ["عقارات", "موظفين وعمالة", "مستثمرين", "دعم IT"])
            conn = sqlite3.connect("mh_group_erp.db")
            
            if rep_type == "عقارات":
                df = pd.read_sql_query("SELECT * FROM properties", conn)
            elif rep_type == "موظفين وعمالة":
                df = pd.read_sql_query("SELECT * FROM employees", conn)
            elif rep_type == "مستثمرين":
                df = pd.read_sql_query("SELECT * FROM investors", conn)
            else:
                df = pd.read_sql_query("SELECT * FROM it_tickets", conn)
            conn.close()
            
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 تحميل التقرير بصيغة CSV", data=df.to_csv(index=False).encode('utf-8'), file_name=f"{rep_type}.csv")

    # --- Developer & Themes ---
    elif page == "⚙️ إعدادات المطور والثيمات":
        st.title("⚙️ إعدادات المطور والثيمات")
        selected_theme_name = st.selectbox(
            "اختر ثيم لوحة التحكم (سيتم حفظه حتى بعد الـ Refresh):",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["selected_theme"])
        )
        
        if selected_theme_name != st.session_state["selected_theme"]:
            st.session_state["selected_theme"] = selected_theme_name
            st.query_params["theme"] = selected_theme_name
            st.success(f"تم تطبيق وحفظ ثيم: {selected_theme_name}")
            st.rerun()
