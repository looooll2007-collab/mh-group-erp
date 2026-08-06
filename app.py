import streamlit as st
import sqlite3
import pandas as pd

# 1. إعدادات الصفحة الرئيسية
st.set_page_config(
    page_title="MH GROUP ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. كود ה-CSS المعدل لمنع مشكلة visibility وإخفاء النصوص
custom_css = """
<style>
/* الاتجاه العام واللون الخلفي */
html, body, [data-testid="stAppViewContainer"] {
    direction: rtl;
    text-align: right;
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
}

[data-testid="stHeader"] {
    background-color: transparent !important;
}

[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-left: 1px solid #30363d !important;
}

/* الأزرار الرئيسية */
.stButton > button {
    background-color: #d4af37 !important;
    color: #0d1117 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    background-color: #f1c40f !important;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.4) !important;
}

/* إصلاح حقول الإدخال ومنع طفح كلمة visibility/visibili */
div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}

div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
    color: #ffffff !important;
    background-color: transparent !important;
}

/* إصلاح أيقونة إظهار/إخفاء كلمة المرور */
button[aria-label="Show password"], 
button[aria-label="Hide password"],
[data-aria-label="Show password"] {
    color: #8b949e !important;
    background: transparent !important;
}

button[aria-label="Show password"] *, 
button[aria-label="Hide password"] * {
    font-size: 0 !important;
}

/* جداول البيانات والعناوين */
[data-testid="stDataFrame"] {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
}

h1, h2, h3, h4 {
    color: #ffffff !important;
    font-weight: 700 !important;
    text-align: center;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 3. إدارة جلسة التسجيل (Session State)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 4. شاشة تسجيل الدخول
def login_page():
    st.markdown("<h1 style='margin-bottom: 0px;'>للاستثمار والتطوير العقاري MH GROUP</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #8b949e !important; font-size: 1.1rem; margin-bottom: 30px;'>نظام إدارة الموارد المؤسسية ERP</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول"):
            # يمكنك ربط بيانات الدخول بنظام الموظفين أو قواعد البيانات
            if username == "admin" and password == "123456":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# 5. لوحة التحكم الرئيسية بعد تسجيل الدخول
def main_app():
    st.sidebar.title(f"مرحباً، {st.session_state.username}")
    
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "لوحة التحكم", 
        "إدارة الموارد البشرية (HR)", 
        "الحسابات والمالية", 
        "المشاريع والعقارات", 
        "الدعم الفني والتقني"
    ])
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()

    st.title(f"قسم: {menu}")
    st.info("تم تحميل النظام وتطبيق الإصلاحات بنجاح.")

# 6. التوجيه حسب حالة التسجيل
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
