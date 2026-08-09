import streamlit as st
import base64

# =========================================================
# MH GROUP ERP - LOGIN PAGE
# Streamlit
# =========================================================

st.set_page_config(
    page_title="MH Group ERP - تسجيل الدخول",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# لو عندك صورة مبنى، ضعها في نفس مجلد app.py باسم:
# building.jpg
# ---------------------------------------------------------

def image_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

building = image_to_base64("building.jpg")

if building:
    bg_image = f"data:image/jpeg;base64,{building}"
else:
    bg_image = ""

# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------

st.markdown(f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

* {{
    font-family: 'Cairo', sans-serif !important;
    box-sizing: border-box;
}}

html, body, [class*="css"] {{
    direction: rtl;
}}

.stApp {{
    background:
        radial-gradient(
            circle at 75% 45%,
            rgba(212,170,76,0.07),
            transparent 35%
        ),
        #070b12;
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
}}

section.main > div {{
    padding: 0 !important;
}}

.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

[data-testid="stSidebar"] {{
    display: none;
}}

.login-page {{
    min-height: 100vh;
    width: 100%;
    display: flex;
    overflow: hidden;
    position: relative;
    background: #080c13;
}}

.left-side {{
    width: 48%;
    min-height: 100vh;
    position: relative;
    overflow: hidden;

    background:
        linear-gradient(
            90deg,
            rgba(5,8,14,0.25),
            rgba(5,8,14,0.78)
        ),
        linear-gradient(
            180deg,
            rgba(7,10,17,0.15),
            rgba(7,10,17,0.92)
        ),
        url("{bg_image}");

    background-size: cover;
    background-position: center;
}}

.left-side::after {{
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(
            90deg,
            transparent 45%,
            rgba(7,10,17,0.7) 100%
        );
}}

.gold-line {{
    position: absolute;
    right: -25px;
    top: -10%;
    height: 125%;
    width: 3px;
    background: linear-gradient(
        180deg,
        transparent,
        #d4aa4c 15%,
        #f2cf72 50%,
        #a97820 85%,
        transparent
    );
    transform: rotate(-10deg);
    z-index: 5;
    box-shadow: 0 0 15px rgba(212,170,76,.4);
}}

.left-content {{
    position: absolute;
    z-index: 10;
    inset: 0;
    padding: 55px 70px;
    display: flex;
    flex-direction: column;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 14px;
}}

.brand-logo {{
    width: 60px;
    height: 60px;
    border-radius: 13px;

    background: linear-gradient(
        145deg,
        #f6d477,
        #a97920
    );

    color: #101010;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 35px;
    font-weight: 900;

    box-shadow:
        0 8px 35px rgba(212,170,76,.25);
}}

.brand-name {{
    color: white;
    font-size: 29px;
    font-weight: 800;
    letter-spacing: 1px;
}}

.brand-sub {{
    color: #d4aa4c;
    font-size: 11px;
    letter-spacing: 5px;
}}

.welcome {{
    margin-top: auto;
    margin-bottom: 100px;
    max-width: 600px;
}}

.welcome-small {{
    color: white;
    font-size: 32px;
    font-weight: 400;
}}

.welcome-title {{
    color: #d9ad45;
    font-size: 48px;
    font-weight: 800;
    margin-top: 4px;
}}

.welcome-text {{
    color: #d2d6dd;
    font-size: 17px;
    line-height: 2;
    max-width: 520px;
    margin-top: 10px;
}}

.features {{
    display: flex;
    gap: 45px;
    margin-top: 35px;
}}

.feature {{
    text-align: center;
    color: white;
}}

.feature-icon {{
    font-size: 28px;
    color: #d4aa4c;
    margin-bottom: 5px;
}}

.feature-title {{
    font-size: 14px;
    font-weight: 700;
}}

.feature-text {{
    font-size: 10px;
    color: #a9b0bc;
}}

.right-side {{
    width: 52%;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 45px;
    background:
        radial-gradient(
            circle at center,
            rgba(212,170,76,.035),
            transparent 50%
        ),
        #080d15;
}}

.login-card {{
    width: min(610px, 100%);
    min-height: 690px;

    padding: 45px 55px;

    background:
        linear-gradient(
            145deg,
            rgba(24,29,38,.96),
            rgba(12,16,23,.97)
        );

    border:
        1px solid rgba(255,255,255,.13);

    border-radius: 18px;

    box-shadow:
        0 30px 90px rgba(0,0,0,.45),
        inset 0 1px rgba(255,255,255,.03);

    text-align: right;
}}

.login-logo {{
    width: 88px;
    height: 88px;
    margin: 0 auto 15px;

    border-radius: 20px;

    background: linear-gradient(
        145deg,
        #f5d275,
        #a77720
    );

    color: #101010;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 55px;
    font-weight: 900;

    box-shadow:
        0 10px 35px rgba(212,170,76,.2);
}}

.login-title {{
    text-align: center;
    color: #e0b651;
    font-size: 39px;
    font-weight: 800;
    margin-top: 5px;
}}

.login-subtitle {{
    text-align: center;
    color: #969fac;
    font-size: 14px;
    margin-bottom: 35px;
}}

.field-label {{
    color: white;
    font-size: 14px;
    font-weight: 600;
    margin: 17px 0 7px;
}}

.stTextInput > div > div {{
    background: #171d27 !important;
    border: 1px solid rgba(255,255,255,.12) !important;
    border-radius: 10px !important;
}}

.stTextInput input {{
    color: white !important;
    background: transparent !important;
    text-align: right !important;
    direction: rtl !important;
    font-family: 'Cairo', sans-serif !important;
    height: 48px !important;
}}

.stTextInput input::placeholder {{
    color: #737c8b !important;
}}

.options {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
    margin-bottom: 22px;
}}

.remember {{
    color: #c1c7d0;
    font-size: 13px;
}}

.forgot {{
    color: #d4aa4c;
    font-size: 13px;
}}

.login-button {{
    width: 100%;
    height: 56px;

    border: none;
    border-radius: 10px;

    background:
        linear-gradient(
            145deg,
            #e1b94f,
            #a77820
        );

    color: white;

    font-family: 'Cairo', sans-serif;
    font-size: 18px;
    font-weight: 800;

    cursor: pointer;

    box-shadow:
        0 8px 25px rgba(212,170,76,.18);

    transition: .2s;
}}

.login-button:hover {{
    transform: translateY(-1px);

    box-shadow:
        0 12px 30px rgba(212,170,76,.3);
}}

.divider {{
    display: flex;
    align-items: center;
    gap: 15px;
    color: #777f8d;
    font-size: 12px;
    margin: 25px 0;
}}

.divider::before,
.divider::after {{
    content: "";
    height: 1px;
    flex: 1;
    background: rgba(255,255,255,.10);
}}

.social-row {{
    display: flex;
    gap: 15px;
}}

.social {{
    flex: 1;
    height: 52px;

    border:
        1px solid rgba(255,255,255,.10);

    border-radius: 9px;

    background: #151b24;

    color: white;

    display: flex;
    align-items: center;
    justify-content: center;
    gap: 9px;

    font-size: 14px;
}}

.footer {{
    text-align: center;
    color: #6f7785;
    font-size: 11px;
    margin-top: 30px;
}}

@media(max-width: 900px) {{

    .login-page {{
        display: block;
        overflow: auto;
    }}

    .left-side {{
        display: none;
    }}

    .right-side {{
        width: 100%;
        min-height: 100vh;
        padding: 20px;
    }}

    .login-card {{
        padding: 35px 25px;
    }}

}}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Login Interface
# ---------------------------------------------------------

st.markdown("""
<div class="login-page">

    <div class="left-side">

        <div class="gold-line"></div>

        <div class="left-content">

            <div class="brand">

                <div class="brand-logo">
                    M
                </div>

                <div>
                    <div class="brand-name">
                        MH GROUP
                    </div>

                    <div class="brand-sub">
                        ERP SYSTEM
                    </div>
                </div>

            </div>


            <div class="welcome">

                <div class="welcome-small">
                    مرحباً بك في
                </div>

                <div class="welcome-title">
                    MH GROUP ERP
                </div>

                <div class="welcome-text">
                    نظام متكامل لإدارة أعمال الاستثمار
                    والتطوير العقاري بكفاءة واحترافية عالية.
                </div>


                <div class="features">

                    <div class="feature">
                        <div class="feature-icon">▥</div>
                        <div class="feature-title">
                            إدارة شاملة
                        </div>
                        <div class="feature-text">
                            جميع عملياتك في مكان واحد
                        </div>
                    </div>


                    <div class="feature">
                        <div class="feature-icon">♢</div>
                        <div class="feature-title">
                            أمان عالي
                        </div>
                        <div class="feature-text">
                            حماية بياناتك على أعلى مستوى
                        </div>
                    </div>


                    <div class="feature">
                        <div class="feature-icon">◷</div>
                        <div class="feature-title">
                            تقارير دقيقة
                        </div>
                        <div class="feature-text">
                            تقارير وتحليلات لحظية
                        </div>
                    </div>


                    <div class="feature">
                        <div class="feature-icon">▦</div>
                        <div class="feature-title">
                            إدارة ذكية
                        </div>
                        <div class="feature-text">
                            لوحة تحكم متكاملة
                        </div>
                    </div>

                </div>

            </div>

        </div>

    </div>


    <div class="right-side">

        <div class="login-card">

            <div class="login-logo">
                M
            </div>

            <div class="login-title">
                تسجيل الدخول
            </div>

            <div class="login-subtitle">
                مرحباً بك، يرجى تسجيل الدخول للوصول إلى حسابك
            </div>

""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Inputs
# ---------------------------------------------------------

username = st.text_input(
    "اسم المستخدم",
    placeholder="أدخل اسم المستخدم",
    key="login_username"
)

password = st.text_input(
    "كلمة المرور",
    type="password",
    placeholder="أدخل كلمة المرور",
    key="login_password"
)


st.markdown("""
<div class="options">

    <div class="remember">
        ☐ تذكرني
    </div>

    <div class="forgot">
        نسيت كلمة المرور؟
    </div>

</div>
""", unsafe_allow_html=True)


login = st.button(
    "تسجيل الدخول  →",
    use_container_width=True
)


if login:

    # -----------------------------------------------------
    # مؤقت للتجربة
    # اربطه بعد ذلك بقاعدة البيانات PostgreSQL
    # -----------------------------------------------------

    if username == "admin" and password == "ChangeMe123!":

        st.session_state["logged_in"] = True
        st.session_state["username"] = username

        st.success("تم تسجيل الدخول بنجاح")
        st.rerun()

    else:

        st.error(
            "اسم المستخدم أو كلمة المرور غير صحيحة"
        )


st.markdown("""
<div class="divider">
    أو تسجيل الدخول باستخدام
</div>

<div class="social-row">

    <div class="social">
        🪟 Microsoft
    </div>

    <div class="social">
        🔵 Google
    </div>

</div>

<div class="footer">
    جميع الحقوق محفوظة © 2026 MH Group
</div>

</div>

</div>
""", unsafe_allow_html=True)
