import streamlit as st
import sqlite3
import random
import string

# ==========================================
# 1. إعداد وإصلاح قاعدة البيانات (Database Setup)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect("mh_group.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جدول المستخدمين (يحتوي على رقم الهاتف وكود إعادة التعيين)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT,
            reset_code TEXT
        )
    ''')
    
    # جدول العقارات (شامل التفاصيل والمصاريف)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            property_type TEXT,
            finishing_type TEXT,
            price REAL DEFAULT 0,
            expenses REAL DEFAULT 0,
            expense_type TEXT,
            status TEXT DEFAULT 'متاح'
        )
    ''')
    
    # جدول المستثمرين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            investment_amount REAL DEFAULT 0,
            notes TEXT
        )
    ''')
    
    # جدول إعدادات اللوحة الرئيسية (خاص بحساب المطور)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # إضافة حساب المطور الافتراضي
    cursor.execute("SELECT * FROM users WHERE username = 'developer'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                       ('developer', 'admin123', 'المطور', '01000000000'))

    # إضافة حساب المدير (Admin) الافتراضي
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                       ('admin', 'admin123', 'مدير', '01000000000'))

    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. وظيفة محاكاة إرسال SMS
# ==========================================
def send_sms_otp(phone, code):
    st.info(f"📱 [محاكاة SMS] تم إرسال كود التحقق ({code}) إلى الرقم: {phone}")
    return True

# ==========================================
# 3. واجهة التطبيق الرئيسية
# ==========================================
st.set_page_config(page_title="MH GROUP - نظام الإدارة", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "reset_stage" not in st.session_state:
    st.session_state.reset_stage = "request" # request, verify, change

st.title("🏢 نظام MH GROUP للاستثمار والتطوير العقاري")

# ------------------------------------------
# نظام تسجيل الدخول واستعادة كلمة السر
# ------------------------------------------
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📲 نسيت كلمة السر؟"])
    
    with tab1:
        st.subheader("تسجيل الدخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
            conn.close()
            if user:
                st.session_state.logged_in = True
                st.session_state.user = dict(user)
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة.")

    with tab2:
        st.subheader("استعادة كلمة السر عبر SMS")
        
        # المرحلة الأولى: طلب اسم المستخدم وإرسال الكود
        if st.session_state.reset_stage == "request":
            reset_username = st.text_input("أدخل اسم المستخدم للتحقق", key="reset_user")
            if st.button("إرسال كود التحقق"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE username = ?", (reset_username,)).fetchone()
                if user:
                    user_dict = dict(user)
                    if user_dict.get("phone"):
                        otp = "".join(random.choices(string.digits, k=6))
                        conn.execute("UPDATE users SET reset_code = ? WHERE id = ?", (otp, user_dict["id"]))
                        conn.commit()
                        conn.close()
                        
                        st.session_state.reset_target_user = user_dict["username"]
                        send_sms_otp(user_dict["phone"], otp)
                        st.session_state.reset_stage = "verify"
                        st.rerun()
                    else:
                        conn.close()
                        st.error("هذا المستخدم لا يملك رقم هاتف مسجل!")
                else:
                    conn.close()
                    st.error("المستخدم غير موجود!")

        # المرحلة الثانية: أدخال كود SMS والتحقق منه
        elif st.session_state.reset_stage == "verify":
            st.info(f"تم إرسال كود التحقق للمستخدم: {st.session_state.get('reset_target_user')}")
            input_code = st.text_input("أدخل الكود المكون من 6 أرقام", max_chars=6)
            
            if st.button("تحقق من الكود"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE username = ?", (st.session_state.reset_target_user,)).fetchone()
                conn.close()
                
                if user:
                    user_dict = dict(user)
                    if user_dict.get("reset_code") == input_code and input_code != "":
                        st.success("الكود صحيح! جاري الانتقال لصفحة تغيير كلمة السر...")
                        st.session_state.reset_stage = "change"
                        st.rerun()
                    else:
                        st.error("❌ الكود غير صحيح! يرجى التأكد وإعادة المحاولة.")

        # المرحلة الثالثة: تعيين كلمة سر جديدة
        elif st.session_state.reset_stage == "change":
            st.subheader("🔒 تعيين كلمة سر جديدة")
            new_pass = st.text_input("كلمة السر الجديدة", type="password")
            confirm_pass = st.text_input("تأكيد كلمة السر الجديدة", type="password")
            
            if st.button("حفظ كلمة السر"):
                if new_pass and new_pass == confirm_pass:
                    conn = get_db_connection()
                    conn.execute("UPDATE users SET password = ?, reset_code = NULL WHERE username = ?", 
                                 (new_pass, st.session_state.reset_target_user))
                    conn.commit()
                    conn.close()
                    st.success("تم تغيير كلمة السر بنجاح! يمكنك الآن تسجيل الدخول.")
                    st.session_state.reset_stage = "request"
                else:
                    st.error("كلمتا السر غير متطابقتين!")

else:
    # ------------------------------------------
    # القائمة الجانبية وإدارة التنقل والأقسام
    # ------------------------------------------
    current_user = st.session_state.user if isinstance(st.session_state.user, dict) else dict(st.session_state.user)
    u_name = current_user.get('username', '')
    u_role = current_user.get('role', '')

    st.sidebar.write(f"مرحباً، **{u_name}** ({u_role})")
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    menu = ["اللوحة الرئيسية", "قسم العقارات", "قسم المستثمرين"]
    
    # تحديد الأقسام المتاحة بناءً على الصلاحيات
    if u_role == "المطور":
        menu.append("💻 قسم المطور (الإعدادات)")
        menu.append("👥 إدارة المستخدمين والصلاحيات")
    elif u_role == "مدير":
        menu.append("👥 إدارة المستخدمين والصلاحيات")

    choice = st.sidebar.selectbox("الانتقال إلى القسم", menu)

    # ------------------------------------------
    # 1. اللوحة الرئيسية
    # ------------------------------------------
    if choice == "اللوحة الرئيسية":
        conn = get_db_connection()
        welcome_msg = conn.execute("SELECT value FROM system_settings WHERE key = 'welcome_message'").fetchone()
        conn.close()
        
        msg = welcome_msg["value"] if welcome_msg else "أهلاً بك في لوحة تحكم MH GROUP"
        st.header(msg)
        
        col1, col2 = st.columns(2)
        conn = get_db_connection()
        prop_count = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        inv_count = conn.execute("SELECT COUNT(*) FROM investors").fetchone()[0]
        conn.close()
        
        col1.metric("إجمالي العقارات", prop_count)
        col2.metric("إجمالي المستثمرين", inv_count)

    # ------------------------------------------
    # 2. قسم العقارات
    # ------------------------------------------
    elif choice == "قسم العقارات":
        st.header("🏠 إدارة العقارات")
        
        with st.expander("➕ إضافة عقار جديد"):
            with st.form("add_property_form"):
                col1, col2 = st.columns(2)
                title = col1.text_input("اسم / عنوان العقار*")
                prop_type = col2.selectbox("نوع العقار", ["شقة", "فيلا", "محل تجاري", "مكتب", "أرض", "عمارة"])
                
                finishing = col1.selectbox("مستوى التشطيب", ["لوكس", "سوبر لوكس", "ألترا سوبر لوكس", "بدون تشطيب"])
                price = col2.number_input("سعر العقار (ج.م)", min_value=0.0, step=1000.0)
                
                st.markdown("---")
                st.subheader("🛠️ مصاريف العقار")
                expense_amount = st.number_input("مبلغ المصاريف (ج.م)", min_value=0.0, step=100.0)
                expense_type = st.selectbox("نوع المصاريف", ["دهانات", "نجارة", "كهرباء", "سباكة", "تشطيب متكامل", "أخرى"])
                
                submit = st.form_submit_button("حفظ العقار")
                
                if submit:
                    if not title:
                        st.error("يرجى إدخال اسم العقار!")
                    else:
                        try:
                            conn = get_db_connection()
                            conn.execute("""
                                INSERT INTO properties (title, property_type, finishing_type, price, expenses, expense_type)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (title, prop_type, finishing, price, expense_amount, expense_type))
                            conn.commit()
                            conn.close()
                            st.success("تمت إضافة العقار بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء الإضافة: {e}")

        st.subheader("📜 قائمة العقارات المسجلة")
        conn = get_db_connection()
        props = conn.execute("SELECT * FROM properties").fetchall()
        conn.close()
        
        if props:
            st.dataframe([dict(p) for p in props], use_container_width=True)
        else:
            st.info("لا توجد عقارات مسجلة حالياً.")

    # ------------------------------------------
    # 3. قسم المستثمرين
    # ------------------------------------------
    elif choice == "قسم المستثمرين":
        st.header("💼 إدارة المستثمرين")
        
        with st.expander("➕ إضافة مستثمر جديد"):
            with st.form("add_investor_form"):
                col1, col2 = st.columns(2)
                name = col1.text_input("اسم المستثمر*")
                phone = col2.text_input("رقم الهاتف*")
                amount = st.number_input("مبلغ الاستثمار (ج.م)", min_value=0.0, step=5000.0)
                notes = st.text_area("ملاحظات")
                
                submit_inv = st.form_submit_button("حفظ المستثمر")
                
                if submit_inv:
                    if not name or not phone:
                        st.error("يرجى إدخال اسم ورقم هاتف المستثمر!")
                    else:
                        try:
                            conn = get_db_connection()
                            conn.execute("""
                                INSERT INTO investors (name, phone, investment_amount, notes)
                                VALUES (?, ?, ?, ?)
                            """, (name, phone, amount, notes))
                            conn.commit()
                            conn.close()
                            st.success("تمت إضافة المستثمر بنجاح!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء الإضافة: {e}")

        st.subheader("📜 قائمة المستثمرين")
        conn = get_db_connection()
        investors = conn.execute("SELECT * FROM investors").fetchall()
        conn.close()
        
        if investors:
            st.dataframe([dict(i) for i in investors], use_container_width=True)
        else:
            st.info("لا يوجد مستثمرون مسجلون حالياً.")

    # ------------------------------------------
    # 4. قسم المطور (خاص بالمطور فقط)
    # ------------------------------------------
    elif choice == "💻 قسم المطور (الإعدادات)":
        st.header("💻 لوحة تحكم المطور")
        st.subheader("تعديل اللوحة الرئيسية")
        
        conn = get_db_connection()
        current_msg = conn.execute("SELECT value FROM system_settings WHERE key = 'welcome_message'").fetchone()
        conn.close()
        
        default_val = current_msg["value"] if current_msg else "أهلاً بك في لوحة تحكم MH GROUP"
        new_msg = st.text_input("رسالة الترحيب الرئيسية", value=default_val)
        
        if st.button("حفظ إعدادات اللوحة"):
            conn = get_db_connection()
            conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('welcome_message', ?)", (new_msg,))
            conn.commit()
            conn.close()
            st.success("تم تحديث إعدادات اللوحة الرئيسية بنجاح!")

    # ------------------------------------------
    # 5. إدارة المستخدمين والصلاحيات (إضافة + حذف)
    # ------------------------------------------
    elif choice == "👥 إدارة المستخدمين والصلاحيات":
        st.header("👥 إدارة المستخدمين والصلاحيات")
        
        tab_add, tab_delete = st.tabs(["➕ إضافة مستخدم", "🗑️ حذف مستخدم"])
        
        with tab_add:
            with st.form("add_user_form"):
                u_name = st.text_input("اسم المستخدم")
                u_pass = st.text_input("كلمة السر", type="password")
                u_phone = st.text_input("رقم الهاتف (لاستلام كود استعادة كلمة السر)")
                u_role = st.selectbox("الصلاحية", ["مستخدم", "مدير", "المطور"])
                
                submit_user = st.form_submit_button("إضافة المستخدم")
                if submit_user:
                    if u_name and u_pass and u_phone:
                        try:
                            conn = get_db_connection()
                            conn.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)",
                                         (u_name, u_pass, u_role, u_phone))
                            conn.commit()
                            conn.close()
                            st.success("تمت إضافة المستخدم بنجاح!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم موجود بالفعل!")
                    else:
                        st.warning("يرجى ملء جميع الحقول المطلوب بما فيها رقم الهاتف!")

        with tab_delete:
            conn = get_db_connection()
            all_users = conn.execute("SELECT id, username, role FROM users").fetchall()
            conn.close()
            
            user_options = {f"{u['username']} ({u['role']})": u['id'] for u in all_users if u['username'] != u_name}
            
            if user_options:
                selected_user = st.selectbox("اختر المستخدم المراد حذفه", list(user_options.keys()))
                if st.button("❌ حذف المستخدم المحدد", type="primary"):
                    user_id_to_del = user_options[selected_user]
                    conn = get_db_connection()
                    conn.execute("DELETE FROM users WHERE id = ?", (user_id_to_del,))
                    conn.commit()
                    conn.close()
                    st.success("تم حذف المستخدم بنجاح!")
                    st.rerun()
            else:
                st.info("لا يوجد مستخدمون آخرون يمكن حذفهم.")

        st.markdown("---")
        st.subheader("📜 قائمة كافة المستخدمين")
        conn = get_db_connection()
        users = conn.execute("SELECT id, username, role, phone FROM users").fetchall()
        conn.close()
        st.dataframe([dict(u) for u in users], use_container_width=True)
