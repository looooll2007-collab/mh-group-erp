import streamlit as st
import sqlite3
import pandas as pd
import os

# ==========================================
# 1. إعدادات الصفحة وقاعدة البيانات
# ==========================================
st.set_page_config(
    page_title="MH GROUP ERP",
    page_icon="🏢",
    layout="wide"
)

# الاتصال بقاعدة البيانات
conn = sqlite3.connect("mh_group_erp.db", check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول الأساسية لو مش موجودة
cursor.execute("""
    CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        category TEXT,
        description TEXT,
        date TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prop_code TEXT,
        prop_type TEXT,
        base_price REAL,
        expenses REAL,
        total_price REAL,
        selling_price REAL,
        status TEXT
    )
""")
conn.commit()

# ==========================================
# 2. القائمة الجانبية (Sidebar Navigation)
# ==========================================
st.sidebar.title("🏢 MH GROUP ERP")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    ":الأقسام المتاحة",
    [
        "الرئيسية (Dashboard)",
        "الملف الشخصي",
        "إدارة المستخدمين والصلاحيات",
        "رفع المستندات",
        "(HR) الموارد البشرية",
        "المالية والأجور",
        "المخزون العقاري",
        "(IT) قسم تكنولوجيا المعلومات",
        "أسهم المستثمرين"
    ]
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.info("تم تسجيل الخروج بنجاح.")

# ==========================================
# 3. محتوى الأقسام (Routing)
# ==========================================

# ------------------------------------------
# أ. الرئيسية (Dashboard)
# ------------------------------------------
if menu == "الرئيسية (Dashboard)":
    st.header("📊 لوحة التحكم الرئيسية")
    st.write("أهلاً بك في نظام MH GROUP ERP ليدارة العقارات والأعمال.")
    
    col1, col2, col3 = st.columns(3)
    
    df_fin = pd.read_sql_query("SELECT * FROM finance", conn)
    if not df_fin.empty:
        inc = df_fin[df_fin['type'] == 'إيراد']['amount'].sum()
        exp = df_fin[df_fin['type'] == 'مصروف']['amount'].sum()
        col1.metric("إجمالي الإيرادات", f"{inc:,.2f} ج.م")
        col2.metric("إجمالي المصروفات", f"{exp:,.2f} ج.م")
        col3.metric("الرصيد الصافي", f"{(inc - exp):,.2f} ج.م")
    else:
        col1.metric("إجمالي الإيرادات", "0.00 ج.م")
        col2.metric("إجمالي المصروفات", "0.00 ج.م")
        col3.metric("الرصيد الصافي", "0.00 ج.م")

# ------------------------------------------
# ب. الملف الشخصي
# ------------------------------------------
elif menu == "الملف الشخصي":
    st.header("👤 الملف الشخصي")
    st.write("بيانات حسابك الحالي والصلاحيات المتاحة.")

# ------------------------------------------
# ج. إدارة المستخدمين والصلاحيات
# ------------------------------------------
elif menu == "إدارة المستخدمين والصلاحيات":
    st.header("🔐 إدارة المستخدمين والصلاحيات")
    st.write("إدارة حسابات الموظفين والصلاحيات الممنوحة لهم.")

# ------------------------------------------
# د. قسم رفع المستندات (مع المعاينة والتصنيف)
# ------------------------------------------
elif menu == "رفع المستندات":
    st.header("📑 قسم إدارة ورفع المستندات")

    doc_types = [
        "عقود (Sales Contracts)",
        "صور تحويلات مالية (Bank Transfers)",
        "إيصالات استلام (Receipts)",
        "هوية / بطاقات شخصية (IDs)",
        "مستندات أخرى (Others)"
    ]

    with st.form("upload_doc_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            doc_type = st.selectbox("تصنيف المستند:", doc_types)
        with col2:
            uploaded_file = st.file_uploader("اختر الملف:", type=["pdf", "png", "jpg", "jpeg", "docx"])
            
        doc_note = st.text_input("ملاحظات / وصف للمستند:")
        submit_doc = st.form_submit_button("رفع المستند", use_container_width=True)

        if submit_doc and uploaded_file is not None:
            st.success(f"✅ تم رفع الملف '{uploaded_file.name}' بنجاح تحت تصنيف [{doc_type}]")

    st.markdown("---")
    st.subheader("📂 معاينة وتنزيل المستندات")
    if 'uploaded_file' in locals() and uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_ext = uploaded_file.name.split('.')[-1].lower()

        st.write(f"**اسم الملف:** {uploaded_file.name} | **التصنيف:** {doc_type}")

        if file_ext in ["png", "jpg", "jpeg"]:
            st.image(file_bytes, caption="معاينة الصورة", width=400)
        elif file_ext == "pdf":
            st.download_button(
                label="📥 تحميل ومعاينة ملف الـ PDF",
                data=file_bytes,
                file_name=uploaded_file.name,
                mime="application/pdf"
            )
        else:
            st.download_button(
                label="📥 تحميل الملف",
                data=file_bytes,
                file_name=uploaded_file.name
            )

# ------------------------------------------
# هـ. الموارد البشرية (HR)
# ------------------------------------------
elif menu == "(HR) الموارد البشرية":
    st.header("👥 قسم الموارد البشرية (HR)")
    st.write("إدارة الموظفين والغياب والحضور.")

# ------------------------------------------
# و. المالية والأجور (Finance & Payroll)
# ------------------------------------------
elif menu == "المالية والأجور":
    st.header("💰 قسم المالية والأجور")

    tab1, tab2, tab3 = st.tabs(["📊 نظرة عامة", "الرواتب والسلف", "💳 الخزينة العامة والإيرادات / المصروفات"])

    with tab1:
        st.subheader("📊 ملخص الحسابات")
        df_fin_summary = pd.read_sql_query("SELECT * FROM finance", conn)
        if not df_fin_summary.empty:
            total_income = df_fin_summary[df_fin_summary['type'] == 'إيراد']['amount'].sum()
            total_expense = df_fin_summary[df_fin_summary['type'] == 'مصروف']['amount'].sum()
            net_balance = total_income - total_expense

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("إجمالي الإيرادات", f"{total_income:,.2f} ج.م")
            col_b.metric("إجمالي المصروفات", f"{total_expense:,.2f} ج.م")
            col_c.metric("صافي الرصيد", f"{net_balance:,.2f} ج.م")
        else:
            st.info("لا توجد بيانات مالية للعرض حالياً.")

    with tab2:
        st.subheader("📑 إدارة السلف والرواتب")
        st.write("إدارة مسيرات الرواتب والسلفيات الخاص بالعمال والموظفين.")

    with tab3:
        st.subheader("💳 الخزينة العامة والإيرادات / المصروفات")
        
        with st.form("fin_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fin_type = st.selectbox("نوع المعاملة:", ["إيراد", "مصروف"])
                amount = st.number_input("المبلغ (ج.م):", min_value=0.0, step=100.0)
                category = st.text_input("التصنيف (مثال: صيانة، توريدات، بيع عقار):")
            with col2:
                trans_date = st.date_input("تاريخ المعاملة:")
                description = st.text_area("تفاصيل المعاملة:")

            submit_fin = st.form_submit_button("تسجيل المعاملة", use_container_width=True)

        if submit_fin:
            if amount <= 0:
                st.warning("⚠️ يرجى إدخال مبلغ أكبر من صفر.")
            else:
                try:
                    cursor.execute(
                        "INSERT INTO finance (type, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
                        (fin_type, amount, category, description, str(trans_date))
                    )
                    conn.commit()
                    st.success("✅ تم تسجيل المعاملة المالية بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء حفظ المعاملة: {e}")

        st.markdown("---")
        st.subheader("📋 سجل المعاملات المالية المسجلة")
        
        df_fin = pd.read_sql_query("SELECT id as 'رقم المعاملة (ID)', type as 'النوع', amount as 'المبلغ', category as 'التصنيف', description as 'التفاصيل', date as 'التاريخ' FROM finance ORDER BY id DESC", conn)
        
        if not df_fin.empty:
            st.dataframe(df_fin, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🗑️ حذف معاملة مالية")
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                fin_to_delete = st.number_input("أدخل رقم المعاملة (ID) المراد حذفها:", min_value=1, step=1)
            with col_del2:
                st.write("")
                st.write("")
                delete_btn = st.button("حذف المعاملة", use_container_width=True)

            if delete_btn:
                cursor.execute("DELETE FROM finance WHERE id = ?", (fin_to_delete,))
                conn.commit()
                st.success(f"✅ تم حذف المعاملة رقم {fin_to_delete} بنجاح!")
                st.rerun()
        else:
            st.info("ℹ️ لا توجد معاملات مالية مسجلة حتى الآن.")

# ------------------------------------------
# ز. المخزون العقاري
# ------------------------------------------
elif menu == "المخزون العقاري":
    st.header("🏠 إدارة المخزون العقاري والتكاليف")
    tab1, tab2, tab3 = st.tabs(["إضافة عقار جديد ➕", "قائمة العقارات وتعديلها 📋", "تعديل وحذف عقار ✏️"])
    
    with tab1:
        with st.form("prop_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                prop_code = st.text_input("كود العقار:")
                prop_type = st.selectbox("نوع العقار:", ["شقة", "فيلا", "محل تجاري", "أرض", "مبنى كامل"])
                base_price = st.number_input("سعر الشراء / التكلفة الأساسية:", min_value=0.0, step=1000.0)
            with col2:
                expenses = st.number_input("المصاريف والتطوير:", min_value=0.0, step=500.0)
                selling_price = st.number_input("سعر البيع المستهدف:", min_value=0.0, step=1000.0)
                status = st.selectbox("حالة العقار:", ["متاح", "مباع", "قيد التطوير"])
            
            submit_prop = st.form_submit_button("حفظ العقار", use_container_width=True)
            
            if submit_prop:
                total_price = base_price + expenses
                try:
                    cursor.execute("""
                        INSERT INTO properties (prop_code, prop_type, base_price, expenses, total_price, selling_price, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (prop_code, prop_type, base_price, expenses, total_price, selling_price, status))
                    conn.commit()
                    st.success("✅ تم إدراج العقار في المخزون بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ أثناء الحفظ: {e}")

    with tab2:
        df_props = pd.read_sql_query("SELECT * FROM properties", conn)
        if not df_props.empty:
            st.dataframe(df_props, use_container_width=True)
        else:
            st.info("لا توجد عقارات مسجلة.")

    with tab3:
        st.write("حذف وتعديل العقارات المسجلة.")

# ------------------------------------------
# ح. قسم IT
# ------------------------------------------
elif menu == "(IT) قسم تكنولوجيا المعلومات":
    st.header("💻 قسم تكنولوجيا المعلومات")
    st.write("إدارة النسخ الاحتياطي والسيرفرات.")

# ------------------------------------------
# ط. أسهم المستثمرين
# ------------------------------------------
elif menu == "أسهم المستثمرين":
    st.header("📈 أسهم المستثمرين")
    st.write("إدارة رأس المال وحصص المستثمرين في المشاريع.")
