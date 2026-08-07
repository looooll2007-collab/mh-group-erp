import streamlit as st

# 1. تهيئة إعدادات الصفحة
st.set_page_config(
    page_title="MH GROUP ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. كود الـ CSS المخصص
siteonic_style_css = """
<style>
/* إخفاء العناصر الافتراضية */
#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
}

/* 1. الشريط العلوي (Top Navbar) */
.navbar-container {
    background-color: #ffffff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 8%;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    direction: rtl;
}
.brand-logo {
    font-size: 1.8rem;
    font-weight: 800;
    color: #1e3a8a;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    letter-spacing: -0.5px;
}
.brand-logo span {
    display: block;
    font-size: 0.75rem;
    font-weight: 400;
    color: #64748b;
    margin-top: -4px;
}
.nav-links {
    display: flex;
    gap: 30px;
    list-style: none;
    margin: 0;
    padding: 0;
}
.nav-links a {
    text-decoration: none;
    color: #475569;
    font-size: 0.95rem;
    font-weight: 600;
    transition: color 0.2s ease;
}
.nav-links a:hover {
    color: #2563eb;
}

/* 2. قسم البطل الرئيسي (Hero Section) */
.hero-wrapper {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 50%, #1e40af 100%);
    min-height: 85vh;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8%;
    direction: rtl;
    position: relative;
    overflow: hidden;
}

/* المحتوى الأيمن */
.hero-content {
    max-width: 550px;
    color: #ffffff;
    z-index: 2;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: 15px;
    color: #ffffff !important;
}
.hero-subtitle {
    font-size: 1.2rem;
    font-weight: 600;
    color: #e0e7ff;
    margin-bottom: 10px;
}
.hero-description {
    font-size: 0.95rem;
    color: #c7d2fe;
    line-height: 1.6;
    margin-bottom: 30px;
}

/* الأزرار */
.cta-buttons {
    display: flex;
    gap: 15px;
}
.btn-primary {
    background-color: #ffffff;
    color: #1e40af !important;
    font-weight: 700;
    padding: 10px 24px;
    border-radius: 8px;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease;
}
.btn-primary:hover {
    background-color: #f8fafc;
    transform: translateY(-2px);
}
.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff !important;
    font-weight: 600;
    padding: 10px 24px;
    border-radius: 8px;
    text-decoration: none;
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(5px);
    transition: all 0.3s ease;
}
.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* 3. البطاقات الشفافة العائمة (Glassmorphic Cards) */
.glass-container {
    position: relative;
    width: 450px;
    height: 350px;
    z-index: 2;
}
.glass-badge {
    position: absolute;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 12px;
    padding: 12px 22px;
    color: #ffffff;
    font-weight: 700;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
}

.badge-1 { top: 40px; right: 20px; }
.badge-2 { top: 130px; right: 120px; }
.badge-3 { top: 220px; right: 200px; }
</style>
"""

st.markdown(siteonic_style_css, unsafe_allow_html=True)

# 3. بناء واجهة الـ HTML المحدثة
hero_html = """
<div class="navbar-container">
    <div class="brand-logo">
        ام اتش جروب
        <span>MH GROUP</span>
    </div>
    <ul class="nav-links">
        <li><a href="#">تواصل معنا</a></li>
        <li><a href="#">خدماتنا</a></li>
        <li><a href="#">عن الشركة</a></li>
    </ul>
</div>

<div class="hero-wrapper">
    <div class="hero-content">
        <div class="hero-title">مرحباً بكم في بوابة<br>فريق ام اتش جروب</div>
        <div class="hero-subtitle">بوابتكم نحو الإدارة العقارية والإنتاجية الفعالة</div>
        <div class="hero-description">
            انضموا إلى منصتنا المتكاملة واحصلوا على جميع الأدوات الذكية التي تحتاجونها لإدارة الموارد، الاستثمارات، والتحليلات بنجاح.
        </div>
        <div class="cta-buttons">
            <a href="#" class="btn-primary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M13 12H3"/></svg>
                تسجيل الدخول
            </a>
            <a href="#" class="btn-secondary">اعرف المزيد</a>
        </div>
    </div>

    <div class="glass-container">
        <div class="glass-badge badge-1">
            <span>التحليلات</span> 📈
        </div>
        <div class="glass-badge badge-2">
            <span>العمل الجماعي</span> 👥
        </div>
        <div class="glass-badge badge-3">
            <span>الإدارة</span> ⚙️
        </div>
    </div>
</div>
"""

st.markdown(hero_html, unsafe_allow_html=True)
