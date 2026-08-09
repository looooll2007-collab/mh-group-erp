
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# MH GROUP ERP - Streamlit
# واجهة عربية RTL - نسخة جاهزة للرفع على GitHub / Streamlit Cloud
# =========================================================

st.set_page_config(
    page_title="MH Group ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# CSS - التصميم الرئيسي
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important;
}

.stApp {
    background: #0b111b;
}

.main .block-container {
    max-width: 1600px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101a28 0%, #0b111b 100%);
    border-right: 1px solid rgba(212,170,76,.20);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

h1, h2, h3, h4, p, label, div {
    direction: rtl;
}

.brand {
    display:flex;
    align-items:center;
    gap:12px;
    padding:10px 5px 22px 5px;
    border-bottom:1px solid rgba(255,255,255,.08);
    margin-bottom:15px;
}

.brand-logo {
    width:52px;
    height:52px;
    border-radius:14px;
    background:linear-gradient(145deg,#f5d47a,#b88624);
    color:#111;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:900;
    font-size:25px;
    box-shadow:0 8px 30px rgba(212,170,76,.22);
}

.brand-title {
    color:#fff;
    font-size:20px;
    font-weight:800;
    line-height:1.1;
}

.brand-sub {
    color:#d4aa4c;
    font-size:10px;
    letter-spacing:2px;
    margin-top:3px;
}

.page-title {
    font-size:31px;
    font-weight:800;
    color:#fff;
    margin-bottom:3px;
}

.page-subtitle {
    color:#8793a5;
    font-size:13px;
    margin-bottom:20px;
}

.gold {
    color:#d4aa4c !important;
}

.kpi {
    background:linear-gradient(145deg,#162232,#101a28);
    border:1px solid rgba(255,255,255,.07);
    border-radius:15px;
    padding:18px;
    min-height:145px;
    box-shadow:0 12px 35px rgba(0,0,0,.18);
}

.kpi-icon {
    width:42px;
    height:42px;
    border-radius:12px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:21px;
    margin-bottom:10px;
}

.kpi-title {
    color:#94a0b2;
    font-size:13px;
}

.kpi-value {
    color:#fff;
    font-size:25px;
    font-weight:800;
    margin-top:2px;
}

.kpi-change {
    color:#50c878;
    font-size:11px;
    margin-top:7px;
}

.card {
    background:#121d2b;
    border:1px solid rgba(255,255,255,.07);
    border-radius:15px;
    padding:18px;
    box-shadow:0 12px 35px rgba(0,0,0,.15);
}

.card-title {
    color:#fff;
    font-weight:700;
    font-size:16px;
    margin-bottom:14px;
}

.badge {
    padding:4px 9px;
    border-radius:20px;
    font-size:11px;
    font-weight:700;
}

.badge-green { background:rgba(58,201,128,.13); color:#55d98d; }
.badge-gold { background:rgba(212,170,76,.14); color:#e4bd62; }
.badge-blue { background:rgba(72,145,255,.13); color:#6ca8ff; }
.badge-red { background:rgba(255,80,80,.13); color:#ff7777; }

div[data-testid="stMetric"] {
    background:#121d2b;
    border:1px solid rgba(255,255,255,.07);
    padding:12px;
    border-radius:14px;
}

.stButton > button {
    border-radius:10px;
    border:1px solid rgba(212,170,76,.35);
    background:linear-gradient(145deg,#c99b37,#9f7422);
    color:#fff;
    font-weight:700;
}

.stButton > button:hover {
    border-color:#f0cf7b;
    color:#fff;
}

div[data-baseweb="select"] > div {
    background:#121d2b;
    border-color:rgba(255,255,255,.10);
}

input, textarea {
    background:#101a28 !important;
    color:#fff !important;
}

.stDataFrame {
    border-radius:12px;
}

.footer {
    text-align:center;
    color:#657286;
    border-top:1px solid rgba(255,255,255,.07);
    padding-top:20px;
    margin-top:35px;
    font-size:12px;
}

.sidebar-user {
    background:#121d2b;
    border:1px solid rgba(212,170,76,.15);
    padding:14px;
    border-radius:13px;
    margin-top:18px;
}

.sidebar-user strong { color:#fff; }
.sidebar-user span { color:#d4aa4c; font-size:12px; }

</style>
""", unsafe_allow_html=True)

# -----------------------------
# بيانات تجريبية
# -----------------------------
if "properties" not in st.session_state:
    st.session_state.properties = pd.DataFrame([
        ["A-001","فيلا النخبة","فيلا","5,200,000","650,000","5,850,000","7,500,000","متاح"],
        ["A-015","عمارة الشروق","عمارة","8,750,000","1,150,000","9,900,000","12,500,000","مباع"],
        ["A-021","قطعة أرض التجمع","أرض","3,100,000","320,000","3,420,000","4,600,000","متاح"],
        ["A-030","مول القاهرة الجديدة","مول","15,000,000","2,250,000","17,250,000","22,000,000","تحت التطوير"],
    ], columns=["الكود","اسم العقار","النوع","سعر الشراء","المصروفات","التكلفة النهائية","سعر البيع المتوقع","الحالة"])

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame([
        ["إيراد","شركة النصر","850,000","2026-08-08","مكتملة"],
        ["مصروف","مقاولات مصر","250,000","2026-08-08","مكتملة"],
        ["إيراد","أحمد محمود","1,200,000","2026-08-07","مكتملة"],
        ["مصروف","شركة الكهرباء","150,000","2026-08-07","مكتملة"],
    ], columns=["نوع العملية","الجهة","المبلغ","التاريخ","الحالة"])

if "employees" not in st.session_state:
    st.session_state.employees = pd.DataFrame([
        ["EMP-001","أحمد محمد","مدير مالي","160","150","24,000"],
        ["EMP-002","محمد علي","مشرف مشروعات","200","100","20,000"],
        ["EMP-003","عمر خالد","موظف IT","120","120","14,400"],
    ], columns=["الكود","الاسم","الوظيفة","الساعات","سعر الساعة","المستحق"])

if "docs" not in st.session_state:
    st.session_state.docs = []

# -----------------------------
# Helpers
# -----------------------------
def money(n):
    return f"{n:,.0f} ج.م"

def kpi(title, value, icon, icon_class, change):
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-icon {icon_class}">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-change">↗ {change}</div>
    </div>
    """, unsafe_allow_html=True)

def section_title(title, subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-logo">M</div>
        <div>
            <div class="brand-title">MH GROUP</div>
            <div class="brand-sub">ERP SYSTEM</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pages = {
        "🏠  لوحة التحكم": "dashboard",
        "🏢  العقارات والمشروعات": "properties",
        "💰  الإدارة المالية": "finance",
        "👥  الموارد البشرية": "hr",
        "🤝  الموردين": "suppliers",
        "💼  المستثمرين": "investors",
        "🖥️  IT Support": "it",
        "📄  المستندات": "documents",
        "📈  التقارير": "reports",
        "👤  المستخدمين والصلاحيات": "users",
        "⚙️  الإعدادات": "settings",
    }

    selected_label = st.radio("القائمة الرئيسية", list(pages.keys()), label_visibility="collapsed")
    page = pages[selected_label]

    st.markdown("""
    <div class="sidebar-user">
        <strong>المدير العام</strong><br>
        <span>admin@mhgroup.com</span>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Dashboard
# -----------------------------
if page == "dashboard":
    section_title("لوحة التحكم", "نظرة عامة على أداء M H Group المالي والعقاري")

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("إجمالي الإيرادات", "8,250,000", "💰", "", "12.5% عن الشهر الماضي")
    with c2: kpi("إجمالي المصروفات", "2,850,000", "🧾", "", "3.2% عن الشهر الماضي")
    with c3: kpi("صافي الأرباح", "5,400,000", "📈", "", "18.7% عن الشهر الماضي")
    with c4: kpi("قيمة العقارات", "45,750,000", "🏢", "", "إجمالي قيمة المحفظة")
    with c5: kpi("العقارات المباعة", "12", "🏠", "", "منذ بداية الشهر")

    st.write("")
    left, mid, right = st.columns([2.1, 1.25, .95])

    with left:
        st.markdown('<div class="card"><div class="card-title">📊 نظرة عامة على الأداء</div>', unsafe_allow_html=True)
        months = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو"]
        revenues = [6.0, 7.0, 6.5, 7.2, 7.8, 7.7, 9.2]
        expenses = [1.5, 1.8, 1.7, 2.3, 2.8, 2.7, 3.2]
        profits = [4.5, 5.2, 4.8, 4.9, 5.0, 5.0, 6.0]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months,y=revenues,name="الإيرادات",mode="lines+markers",line=dict(width=3)))
        fig.add_trace(go.Scatter(x=months,y=expenses,name="المصروفات",mode="lines+markers",line=dict(width=3)))
        fig.add_trace(go.Scatter(x=months,y=profits,name="الأرباح",mode="lines+markers",line=dict(width=3)))
        fig.update_layout(
            height=350,
            margin=dict(l=20,r=20,t=10,b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1", family="Cairo"),
            legend=dict(orientation="h", y=1.12, x=0),
            xaxis=dict(gridcolor="rgba(255,255,255,.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,.05)", title="مليون ج.م"),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with mid:
        st.markdown('<div class="card"><div class="card-title">📌 توزيع المصروفات</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Pie(
            labels=["شراء عقارات","مصروفات تطوير","مصروفات إدارية","رواتب وأجور","أخرى"],
            values=[40,25,15,10,10],
            hole=.62,
            textinfo="percent",
        ))
        fig2.update_layout(
            height=350,
            margin=dict(l=10,r=10,t=10,b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d7dee9", family="Cairo"),
            showlegend=True,
            legend=dict(font=dict(size=10)),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="card-title">⚡ آخر النشاط</div>', unsafe_allow_html=True)
        activities = [
            ("🏢","تم إضافة عقار جديد","منذ 10 دقائق"),
            ("💰","تم تسجيل إيراد جديد","منذ 30 دقيقة"),
            ("📄","تم رفع مستند جديد","منذ ساعتين"),
            ("👤","تم إضافة موظف جديد","منذ 3 ساعات"),
            ("🏢","تم تحديث بيانات عقار","منذ 5 ساعات"),
        ]
        for icon,title,time in activities:
            st.markdown(f"""
            <div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06)">
                <b style="color:#fff">{icon} {title}</b><br>
                <span style="color:#718096;font-size:11px">{time}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    a,b = st.columns(2)

    with a:
        st.markdown('<div class="card"><div class="card-title">🏢 آخر العقارات المضافة</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.properties.tail(4), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with b:
        st.markdown('<div class="card"><div class="card-title">💳 آخر المعاملات المالية</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.transactions.tail(4), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Properties
# -----------------------------
elif page == "properties":
    section_title("العقارات والمشروعات", "إدارة المحفظة العقارية وحساب التكلفة والربح تلقائيًا")

    t1,t2 = st.tabs(["📋 العقارات","➕ إضافة عقار"])

    with t1:
        st.dataframe(st.session_state.properties, use_container_width=True, hide_index=True)

        st.markdown("### 🔎 تحليل العقارات")
        p = st.session_state.properties.copy()
        p["تكلفة رقمية"] = p["التكلفة النهائية"].str.replace(",","").astype(float)
        p["بيع رقمي"] = p["سعر البيع المتوقع"].str.replace(",","").astype(float)
        p["الربح المتوقع"] = p["بيع رقمي"] - p["تكلفة رقمية"]
        st.dataframe(
            p[["الكود","اسم العقار","الحالة","تكلفة رقمية","بيع رقمي","الربح المتوقع"]],
            use_container_width=True,
            hide_index=True
        )

    with t2:
        with st.form("add_property"):
            c1,c2 = st.columns(2)
            with c1:
                code = st.text_input("كود العقار")
                name = st.text_input("اسم العقار")
                typ = st.selectbox("نوع العقار",["فيلا","شقة","عمارة","أرض","مول","مكتب","محل"])
            with c2:
                purchase = st.number_input("سعر الشراء", min_value=0.0, step=1000.0)
                expenses = st.number_input("المصروفات", min_value=0.0, step=1000.0)
                sale = st.number_input("سعر البيع المتوقع", min_value=0.0, step=1000.0)

            final_cost = purchase + expenses
            profit = sale - final_cost

            st.info(f"التكلفة النهائية: {money(final_cost)}   |   الربح المتوقع: {money(profit)}")
            submitted = st.form_submit_button("💾 حفظ العقار")

            if submitted:
                new_row = pd.DataFrame([[
                    code,name,typ,
                    f"{purchase:,.0f}",
                    f"{expenses:,.0f}",
                    f"{final_cost:,.0f}",
                    f"{sale:,.0f}",
                    "متاح"
                ]], columns=st.session_state.properties.columns)
                st.session_state.properties = pd.concat([st.session_state.properties,new_row], ignore_index=True)
                st.success("تم إضافة العقار بنجاح")
                st.rerun()

# -----------------------------
# Finance
# -----------------------------
elif page == "finance":
    section_title("الإدارة المالية", "الإيرادات والمصروفات والأرباح والمعاملات")

    revenue = 8250000
    expense = 2850000
    profit = revenue - expense

    c1,c2,c3 = st.columns(3)
    c1.metric("إجمالي الإيرادات", money(revenue), "12.5%")
    c2.metric("إجمالي المصروفات", money(expense), "3.2%")
    c3.metric("صافي الأرباح", money(profit), "18.7%")

    st.divider()

    with st.form("transaction"):
        st.markdown("### ➕ تسجيل معاملة مالية")
        c1,c2,c3 = st.columns(3)
        with c1:
            kind = st.selectbox("نوع العملية",["إيراد","مصروف"])
            entity = st.text_input("الجهة")
        with c2:
            amount = st.number_input("المبلغ",min_value=0.0,step=1000.0)
            date = st.date_input("التاريخ",datetime.now())
        with c3:
            status = st.selectbox("الحالة",["مكتملة","معلقة","ملغاة"])
            note = st.text_input("البيان")

        if st.form_submit_button("💾 حفظ العملية"):
            row = pd.DataFrame([[kind,entity,f"{amount:,.0f}",str(date),status]],
                               columns=st.session_state.transactions.columns)
            st.session_state.transactions = pd.concat([st.session_state.transactions,row],ignore_index=True)
            st.success("تم حفظ العملية")
            st.rerun()

    st.markdown("### 📋 سجل المعاملات")
    st.dataframe(st.session_state.transactions,use_container_width=True,hide_index=True)

# -----------------------------
# HR
# -----------------------------
elif page == "hr":
    section_title("الموارد البشرية", "الموظفون وساعات العمل والمستحقات")

    st.dataframe(st.session_state.employees,use_container_width=True,hide_index=True)

    st.markdown("### ➕ إضافة موظف")
    with st.form("employee"):
        c1,c2,c3 = st.columns(3)
        with c1:
            code = st.text_input("كود الموظف")
            name = st.text_input("اسم الموظف")
        with c2:
            job = st.text_input("الوظيفة")
            hours = st.number_input("عدد الساعات",min_value=0.0,step=1.0)
        with c3:
            rate = st.number_input("سعر الساعة",min_value=0.0,step=10.0)
            due = hours * rate
            st.metric("المستحق",money(due))

        if st.form_submit_button("💾 حفظ الموظف"):
            row = pd.DataFrame([[code,name,job,f"{hours:.0f}",f"{rate:,.0f}",f"{due:,.0f}"]],
                               columns=st.session_state.employees.columns)
            st.session_state.employees = pd.concat([st.session_state.employees,row],ignore_index=True)
            st.success("تمت إضافة الموظف")
            st.rerun()

# -----------------------------
# Suppliers
# -----------------------------
elif page == "suppliers":
    section_title("الموردين", "إدارة الموردين وكشوف الحساب والمستحقات")

    suppliers = pd.DataFrame([
        ["SUP-001","شركة النصر للمقاولات","مقاولات","850,000","250,000","600,000"],
        ["SUP-002","شركة الكهرباء","خدمات","450,000","150,000","300,000"],
        ["SUP-003","مؤسسة التشطيبات","تشطيبات","720,000","300,000","420,000"],
    ],columns=["الكود","المورد","النشاط","إجمالي المستحق","المدفوع","المتبقي"])
    st.dataframe(suppliers,use_container_width=True,hide_index=True)

# -----------------------------
# Investors
# -----------------------------
elif page == "investors":
    section_title("المستثمرين", "متابعة مساهمات المستثمرين والأرباح")

    investors = pd.DataFrame([
        ["INV-001","أحمد محمود","10,000,000","25%","1,350,000"],
        ["INV-002","محمد سامي","7,500,000","18%","972,000"],
        ["INV-003","عمر حسن","5,000,000","12%","648,000"],
    ],columns=["الكود","المستثمر","قيمة المساهمة","نسبة المشاركة","الأرباح"])
    st.dataframe(investors,use_container_width=True,hide_index=True)

# -----------------------------
# IT
# -----------------------------
elif page == "it":
    section_title("IT Support", "متابعة موظفي تقنية المعلومات والأعطال والمهام")

    c1,c2,c3 = st.columns(3)
    c1.metric("موظفو IT","3")
    c2.metric("ساعات العمل هذا الشهر","412")
    c3.metric("طلبات الدعم المفتوحة","7")

    tickets = pd.DataFrame([
        ["IT-001","مشكلة شبكة","مكتب الإدارة","عالية","مفتوحة"],
        ["IT-002","تثبيت برنامج","الحسابات","متوسطة","قيد التنفيذ"],
        ["IT-003","صيانة جهاز","الموارد البشرية","منخفضة","مغلقة"],
    ],columns=["رقم الطلب","المشكلة","القسم","الأولوية","الحالة"])
    st.dataframe(tickets,use_container_width=True,hide_index=True)

# -----------------------------
# Documents
# -----------------------------
elif page == "documents":
    section_title("المستندات", "رفع وتنظيم عقود وفواتير ومستندات الشركة")

    uploaded = st.file_uploader(
        "📤 ارفع مستندًا",
        type=["pdf","png","jpg","jpeg","xlsx","docx"],
        accept_multiple_files=True
    )

    if uploaded:
        for file in uploaded:
            if file.name not in st.session_state.docs:
                st.session_state.docs.append(file.name)
        st.success(f"تم استقبال {len(uploaded)} ملف")

    if st.session_state.docs:
        docs_df = pd.DataFrame({
            "اسم المستند":st.session_state.docs,
            "تاريخ الرفع":[datetime.now().strftime("%Y-%m-%d %H:%M")]*len(st.session_state.docs),
            "المستخدم":["admin"]*len(st.session_state.docs),
        })
        st.dataframe(docs_df,use_container_width=True,hide_index=True)

# -----------------------------
# Reports
# -----------------------------
elif page == "reports":
    section_title("التقارير", "تقارير الإدارة المالية والعقارية")

    report = st.selectbox("اختر التقرير",[
        "الأرباح والخسائر",
        "الإيرادات والمصروفات",
        "العقارات",
        "الموظفين",
        "الموردين",
        "المستثمرين"
    ])

    st.info(f"التقرير الحالي: {report}")

    if report == "العقارات":
        data = st.session_state.properties
    elif report == "الموظفين":
        data = st.session_state.employees
    else:
        data = st.session_state.transactions

    st.dataframe(data,use_container_width=True,hide_index=True)

    csv = data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ تحميل التقرير Excel/CSV",
        data=csv,
        file_name=f"mh_group_{report}.csv",
        mime="text/csv"
    )

# -----------------------------
# Users
# -----------------------------
elif page == "users":
    section_title("المستخدمين والصلاحيات", "إدارة مستخدمي النظام ومستويات الوصول")

    users = pd.DataFrame([
        ["USR-001","admin","المدير العام","كاملة","نشط"],
        ["USR-002","finance","الحسابات","مالية","نشط"],
        ["USR-003","hr","الموارد البشرية","HR","نشط"],
        ["USR-004","it","IT Support","IT","نشط"],
    ],columns=["الكود","اسم المستخدم","المسمى","الصلاحية","الحالة"])
    st.dataframe(users,use_container_width=True,hide_index=True)

# -----------------------------
# Settings
# -----------------------------
elif page == "settings":
    section_title("الإعدادات", "إعدادات الشركة والنظام والأمان")

    t1,t2,t3 = st.tabs(["🏢 الشركة","🔐 الأمان","🎨 الواجهة"])

    with t1:
        company = st.text_input("اسم الشركة","M H Group")
        activity = st.text_input("النشاط","الاستثمار والتطوير العقاري")
        email = st.text_input("البريد الإلكتروني","admin@mhgroup.com")
        phone = st.text_input("الهاتف","+20")
        if st.button("💾 حفظ بيانات الشركة"):
            st.success("تم حفظ الإعدادات")

    with t2:
        st.text_input("اسم المستخدم","admin")
        st.text_input("كلمة المرور الجديدة",type="password")
        st.text_input("تأكيد كلمة المرور",type="password")
        st.checkbox("تفعيل سجل العمليات")
        st.checkbox("السماح بالنسخ الاحتياطي")
        if st.button("🔐 تحديث إعدادات الأمان"):
            st.success("تم تحديث إعدادات الأمان")

    with t3:
        st.selectbox("النمط",["Dark Gold","Dark Blue","Light"])
        st.slider("حجم الواجهة",80,120,100)
        st.checkbox("تفعيل التنبيهات")

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<div class="footer">
    MH GROUP ERP • نظام إدارة الاستثمار والتطوير العقاري
    <br>
    جميع الحقوق محفوظة © 2026
</div>
""", unsafe_allow_html=True)
