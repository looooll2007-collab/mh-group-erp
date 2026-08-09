import os
import random
import sqlite3
import requests
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والتصميم (MH Group Theme)
# ==========================================
st.set_page_config(
    page_title="MH Group ERP System", page_icon="🔐", layout="centered"
)

# CSS Custom Styling
custom_css = """
<style>
    .stApp {
        background-color: #0d1b2a;
        color: #ffffff;
    }
    div.stButton > button {
        background-color: #d4af37 !important;
        color: #0d1b2a !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        height: 45px !important;
    }
    div.stButton > button:hover {
        background-color: #f1c40f !important;
        color: #000000 !important;
    }
    /* زر الإلغاء */
    div[data-testid="column"]:nth-child(2) div.stButton > button {
        background-color: #e67e22 !important;
        color: #ffffff !important;
    }
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 2. إدارة الجلسة (Session State Manager)
# ==========================================
# التحكم في حالة الصفحة: 'login' لصفحة الدخول أو 'verify_otp' لصفحة التحقق
if "page" not in st.session_state:
    st.session_state.page = "login"

if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None


# ==========================================
# 3. صفحة تسجيل الدخول الرئيسية (Login Page)
# ==========================================
def render_login_page():
    st.markdown(
        "<h2 style='text-align: center;'>تسجيل الدخول للنظام 🔐</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #bdc3c7;'>مرحباً بك! يرجى إدخال بياناتك للمتابعة.</p>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        email = st.text_input("البريد الإلكتروني", value="hr@mhgroup.com")
        password = st.text_input("كلمة السر", type="password")
        submit = st.form_submit_button("تسجيل الدخول", use_container_width=True)

        if submit:
            if email and password:
                # التحقق المباشر أو الانتقال للتحقق برمز SMS
                st.session_state.target_email = email
                st.session_state.generated_otp = str(
                    random.randint(100000, 999999)
                )
                st.session_state.page = "verify_otp"
                st.rerun()
            else:
                st.error("يرجى إدخال البريد الإلكتروني وكلمة السر.")


# ==========================================
# 4. صفحة كود التحقق (OTP Verification Page)
# ==========================================
def render_otp_page():
    target_email = st.session_state.get("target_email", "hr@mhgroup.com")

    st.markdown(
        "<h2 style='text-align: center;'>تسجيل الدخول للنظام 🔐</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #bdc3c7;'>مرحباً بك! يرجى إدخال بياناتك للمتابعة.</p>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.info("📱 استعادة كلمة السر عبر كود SMS")

    # النص المطلوب مع إخفاء الكود نهائياً
    st.markdown(
        f"تم إرسال كود SMS إلى هاتفك المسجل باسم **{target_email}**.",
        unsafe_allow_html=True,
    )

    st.write("")

    # مدخل الكود
    otp_input = st.text_input(
        "أدخل كود التحقق المكون من 6 أرقام:",
        max_chars=6,
        placeholder="أدخل 6 أرقام هنا",
        key="otp_input_field",
    )

    st.write("")

    col_confirm, col_cancel = st.columns(2)

    with col_confirm:
        if st.button("تأكيد الكود", use_container_width=True):
            if not otp_input:
                st.warning("يرجى إدخال كود التحقق أولاً.")
            elif (
                otp_input.strip() == st.session_state.generated_otp
                or otp_input.strip() == "123456"
            ):  # 123456 للاختبار السريع
                st.success("✅ تم التأكد من الكود بنجاح! جاري التوجيه...")
                # st.session_state.page = "dashboard" # التوجيه للوحة التحكم
            else:
                st.error("❌ كود التحقق غير صحيح، يرجى المحاولة مرة أخرى.")

    with col_cancel:
        if st.button("إلغاء", use_container_width=True):
            # عند الضغط على إلغاء يتم إرجاع المستخدم لصفحة الدخول
            st.session_state.page = "login"
            st.rerun()


# ==========================================
# 5. الموجه الرئيسي (Router)
# ==========================================
if st.session_state.page == "login":
    render_login_page()
elif st.session_state.page == "verify_otp":
    render_otp_page()
