import os
import random
import re
import sqlite3
import requests
import streamlit as st

# ==========================================
# 1. إعدادات الصفحة والتصميم (MH Group Theme)
# ==========================================
st.set_page_config(
    page_title="MH Group ERP System - OTP", page_icon="🔐", layout="centered"
)

# تطبيق الألوان الملكية الداكنة والذهبية عبر CSS custom
custom_css = """
<style>
    /* خلفية التطبيق داكنة */
    .stApp {
        background-color: #0d1b2a;
        color: #ffffff;
    }
    /* تنسيق كارت تسجيل الدخول */
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
    /* إخفاء عنصر التحكم السفلي إن وجد */
    footer {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 2. إدارة قاعدة البيانات وقراءة هاتف المستخدم
# ==========================================
DB_PATH = "mh_group_erp.db"  # استبدل بمسار قاعدة بياناتك


def get_user_phone(email):
    """استرجاع رقم هاتف المستخدم المسجل بناءً على بريده الإلكتروني"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
    except Exception as e:
        pass
    # رقم افتراضي للتجربة في حالة عدم وجود قاعدة بيانات محلياً
    return "+201000000000"


# ==========================================
# 3. دالة إرسال الـ SMS (SMS Misr / Twilio)
# ==========================================
def send_sms_via_provider(phone_number, otp):
    """
    إرسال كود التحقق عبر بوابة SMS.
    ملاحظة: يمكنك ضبط المفاتيح من Streamlit Secrets أو المتغيرات.
    """
    # مثال باستخدام بوابة SMS Misr المحلية:
    sms_misr_username = st.secrets.get("SMS_USER", "YOUR_USERNAME")
    sms_misr_password = st.secrets.get("SMS_PASS", "YOUR_PASSWORD")
    sms_misr_sender = st.secrets.get("SMS_SENDER", "MHGroup")

    url = "https://smsmisr.com/api/SMS/"
    payload = {
        "environment": "1",  # 1 للبيئة الفعليه / 2 للبيئة التجريبية
        "username": sms_misr_username,
        "password": sms_misr_password,
        "language": "2",  # 2 للغة العربية
        "sender": sms_misr_sender,
        "mobile": phone_number,
        "message": f"كود التحقق الخاص بك لدخول نظام MH Group هو: {otp}",
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        res_data = response.json()
        if res_data.get("code") == "1901":  # كود النجاح في SMS Misr
            return True, "تم الإرسال بنجاح"
        else:
            return False, f"رمز الاستجابة: {res_data.get('code')}"
    except Exception as e:
        # تحويل محلي مؤقت إذا لم تكن المفاتيح مضبوطة
        return True, "محاكاة الإرسال"


# ==========================================
# 4. تهيئة جلسة المستخدم (Session State)
# ==========================================
target_email = "hr@mhgroup.com"

if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = str(random.randint(100000, 999999))

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False

user_phone = get_user_phone(target_email)

# إرسال الرسالة تلقائياً مرة واحدة عند فتح الواجهة
if not st.session_state.otp_sent:
    status, msg = send_sms_via_provider(
        user_phone, st.session_state.generated_otp
    )
    if status:
        st.session_state.otp_sent = True


# ==========================================
# 5. واجهة المستخدم (UI Engine)
# ==========================================
st.markdown(
    "<h2 style='text-align: center;'>تسجيل الدخول للنظام 🔐</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #bdc3c7;'>مرحباً بك! يرجى إدخال بياناتك للمتابعة.</p>",
    unsafe_allow_html=True,
)

st.write("")

# صندوق التنبيه الداكن
st.info("📱 SMS استعادة كلمة السر عبر كود")

# نص توضيحي بدون كشف الكود
st.markdown(
    f"إلى هاتفك المسجل باسم **{target_email}** تم إرسال كود SMS.",
    unsafe_allow_html=True,
)

# 🛑 تم حذف السطر القديم الذي يحتوي على: (الكود المكتوب للتجربة: XXXXXX) 🛑

st.write("")

# حقل إدخال كود التحقق
otp_input = st.text_input(
    ":أدخل كود التحقق المكون من 6 أرقام",
    max_chars=6,
    placeholder="أدخل 6 أرقام هنا",
    key="otp_field",
)

st.write("")

# أزرار التحكم (تأكيد الكود / إلغاء)
col_confirm, col_cancel = st.columns(2)

with col_confirm:
    if st.button("تأكيد الكود", use_container_width=True):
        if not otp_input:
            st.warning("يرجى إدخال كود التحقق أولاً.")
        elif otp_input.strip() == st.session_state.generated_otp:
            st.success("✅ تم التأكد من الكود بنجاح! جاري التوجيه...")
            # هنا تضع كود الانتقال للصفحة الرئيسية لنظام الـ ERP
            # st.switch_page("pages/dashboard.py")
        else:
            st.error("❌ كود التحقق غير صحيح، يرجى التأكد وإعادة المحاولة.")

with col_cancel:
    if st.button("إلغاء", use_container_width=True):
        st.info("تم إلغاء عملية التحقق.")
        # إعادة التوجيه لصفحة تسجيل الدخول الرئيسية
