import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. Page Configuration & Custom CSS Theme
# ==========================================
st.set_page_config(
    page_title="MH GROUP ERP SYSTEM",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling to match Dark/Gold Enterprise Theme
st.markdown(
    """
    <style>
    /* Global Background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Gold Accent Buttons & Headers */
    .stButton>button {
        background-color: #c59b27;
        color: #000000;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #e5b839;
        color: #000000;
        box-shadow: 0px 0px 10px rgba(197, 155, 39, 0.5);
    }
    
    /* KPI Cards */
    .kpi-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: right;
        margin-bottom: 15px;
    }
    .kpi-title {
        color: #8b949e;
        font-size: 0.9rem;
    }
    .kpi-value {
        color: #f0f6fc;
        font-size: 1.6rem;
        font-weight: bold;
    }
    .kpi-sub {
        color: #3fb950;
        font-size: 0.8rem;
    }
    
    /* Inputs Styling */
    div[data-baseweb="input"] {
        background-color: #0d1117;
        border-color: #30363d;
        color: #ffffff;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #d4af37 !important;
        text-align: right;
    }
    
    /* Tables */
    .stDataFrame {
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_dict_style=True,
)

# ==========================================
# 2. Session State Initialization (Database Mock)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# Sample System Data
if "users" not in st.session_state:
    st.session_state["users"] = pd.DataFrame(
        [
            {
                "اسم المستخدم": "admin",
                "كلمة المرور": "admin123",
                "الدور": "المدير العام",
                "آخر نشاط": "2024-05-23 10:15:22",
                "عنوان IP": "192.168.1.10",
                "تاريخ خروج": "2024-05-23 12:00:00",
            },
            {
                "اسم المستخدم": "ahmed_hr",
                "كلمة المرور": "hr123",
                "الدور": "إدارة الموارد البشرية",
                "آخر نشاط": "2024-05-22 14:30:00",
                "عنوان IP": "192.168.1.15",
                "تاريخ خروج": "2024-05-22 17:00:00",
            },
        ]
    )

if "financial_data" not in st.session_state:
    st.session_state["financial_data"] = pd.DataFrame(
        [
            {
                "نوع العملية": "إيراد",
                "الجهة": "عميل - شركة النصر",
                "المبلغ": 850000,
                "التاريخ": "2024-05-23",
                "الحالة": "مكتملة",
                "القسم": "العقارات",
            },
            {
                "نوع العملية": "مصروف",
                "الجهة": "مورد - مقاولات مصر",
                "المبلغ": 250000,
                "التاريخ": "2024-05-23",
                "الحالة": "مكتملة",
                "القسم": "المشتريات",
            },
        ]
    )

if "hr_workers" not in st.session_state:
    st.session_state["hr_workers"] = pd.DataFrame(
        [
            {
                "ID": "EMP-001",
                "الاسم": "محمود النقاش",
                "الصفة": "نقاش",
                "المورد التابع له": "شركة الصفا",
                "سعر الساعة": 50,
                "عدد الساعات": 8,
                "سعر اليومية": 400,
                "السلفيات": 50,
                "نوع المستند": "بطاقة رقم القومي",
            },
            {
                "ID": "EMP-002",
                "الاسم": "حسن النحات",
                "الصفة": "نحات",
                "المورد التابع له": "مستقل",
                "سعر الساعة": 80,
                "عدد الساعات": 10,
                "سعر اليومية": 800,
                "السلفيات": 100,
                "نوع المستند": "عقد عمل",
            },
        ]
    )

if "real_estate" not in st.session_state:
    st.session_state["real_estate"] = pd.DataFrame(
        [
            {
                "ID": "PROP-101",
                "اسم العقار": "فيلا النرجس 001",
                "نوع العقار": "سكني",
                "نوع التشطيب": "ألترا سوبر لوكس",
                "سعر الشراء": 5200000,
                "المصروفات": 800000,
                "سعر البيع المقدر": 7000000,
                "الحالة": "تحت التطوير",
            },
            {
                "ID": "PROP-102",
                "اسم العقار": "عمارة الشروق 15",
                "نوع العقار": "تجاري",
                "نوع التشطيب": "تجاري",
                "سعر الشراء": 8750000,
                "المصروفات": 1200000,
                "سعر البيع المقدر": 11500000,
                "الحالة": "مباع",
            },
        ]
    )

if "investors" not in st.session_state:
    st.session_state["investors"] = pd.DataFrame(
        [
            {
                "اسم المستثمر": "د. خالد السعيد",
                "ID العقار": "PROP-101",
                "نسبة الاستثمار (%)": 30.0,
                "المبلغ المستثمر": 1800000,
                "العائد المتوقع": 300000,
            }
        ]
    )

if "it_team" not in st.session_state:
    st.session_state["it_team"] = pd.DataFrame(
        [
            {
                "ID الموظف": "IT-10",
                "اسم الموظف": "علي إبراهيم",
                "عدد ساعات العمل": 160,
                "سعر الساعة": 60,
                "سعر اليومية": 480,
                "نوع المستند": "شهادة شهادة أمان شبكات",
            }
        ]
    )

if "audit_logs" not in st.session_state:
    st.session_state["audit_logs"] = pd.DataFrame(
        [
            {
                "التاريخ والوقت": "2024-05-23 09:00:00",
                "المستخدم": "admin",
                "القسم": "تسجيل الدخول",
                "العملية": "دخول ناجح",
                "الحالة": "صحيحة",
            },
            {
                "التاريخ والوقت": "2024-05-23 09:05:12",
                "المستخدم": "unknown",
                "القسم": "تسجيل الدخول",
                "العملية": "محاولة دخول خاطئة",
                "الحالة": "غير صحيحة",
            },
        ]
    )

if "tickets" not in st.session_state:
    st.session_state["tickets"] = pd.DataFrame(
        [
            {
                "رقم البلاغ": "TK-01",
                "المستخدم": "ahmed_hr",
                "تصنيف المشكلة": "برمجية",
                "التفاصيل": "عطل أثناء رفع مستندات الموظفين",
                "نوع المستند المرفق": "صورة الشاشة (PNG)",
                "الحالة": "قيد المعالجة",
            }
        ]
    )

# ==========================================
# 3. Login / Authentication Interface
# ==========================================
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 20px;">
                <h1 style="color: #c59b27; margin-bottom: 0px;">MH GROUP</h1>
                <p style="color: #8b949e; letter-spacing: 2px;">ERP SYSTEM</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            st.markdown("### تسجيل الدخول")
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            submit = st.form_submit_button("تسجيل الدخول")

            if submit:
                user_match = st.session_state["users"][
                    (st.session_state["users"]["اسم المستخدم"] == username)
                    & (st.session_state["users"]["كلمة المرور"] == password)
                ]
                if not user_match.empty:
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = username
                    st.session_state["user_role"] = user_match.iloc[0]["الدور"]

                    # Log Login
                    new_log = {
                        "التاريخ والوقت": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "المستخدم": username,
                        "القسم": "تسجيل الدخول",
                        "العملية": "دخول ناجح",
                        "الحالة": "صحيحة",
                    }
                    st.session_state["audit_logs"] = pd.concat(
                        [
                            st.session_state["audit_logs"],
                            pd.DataFrame([new_log]),
                        ],
                        ignore_index=True,
                    )
                    st.rerun()
                else:
                    # Log Failed Attempt
                    new_log = {
                        "التاريخ والوقت": datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "المستخدم": username if username else "مجهول",
                        "القسم": "تسجيل الدخول",
                        "العملية": "محاولة دخول بكلمة سر خاطئة",
                        "الحالة": "غير صحيحة",
                    }
                    st.session_state["audit_logs"] = pd.concat(
                        [
                            st.session_state["audit_logs"],
                            pd.DataFrame([new_log]),
                        ],
                        ignore_index=True,
                    )
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
    st.stop()

# ==========================================
# 4. Main Navigation (Sidebar Menu)
# ==========================================
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="color: #c59b27; margin:0;">MH GROUP</h2>
        <small style="color: #8b949e;">للاستثمار والتطوير العقاري</small>
    </div>
    """,
    unsafe_allow_html=True,
)

menu_options = [
    "لوحة التحكم (الداشبورد)",
    "المستخدمين والصلاحيات",
    "الإدارة المالية",
    "الموارد البشرية (HR)",
    "العقارات والمخزون",
    "قسم المستثمرين",
    "قسم IT Support",
    "سجل العمليات (Audit Log)",
    "الإبلاغ عن مشكلة",
]

choice = st.sidebar.radio("القائمة الرئيسية", menu_options)

st.sidebar.markdown("---")
st.sidebar.write(
    f"👤 **المستخدم:** {st.session_state['current_user']} ({st.session_state['user_role']})"
)

if st.sidebar.button("تسجيل الخروج"):
    # Log logout
    new_log = {
        "التاريخ والوقت": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "المستخدم": st.session_state["current_user"],
        "القسم": "تسجيل الدخول",
        "العملية": "تسجيل خروج",
        "الحالة": "صحيحة",
    }
    st.session_state["audit_logs"] = pd.concat(
        [st.session_state["audit_logs"], pd.DataFrame([new_log])],
        ignore_index=True,
    )
    st.session_state["logged_in"] = False
    st.rerun()


# ==========================================
# 5. Page Implementations
# ==========================================

# ------------------------------------------
# 1- Dashboard Section
# ------------------------------------------
if choice == "لوحة التحكم (الداشبورد)":
    st.markdown("<h2>لوحة التحكم الرئيسية</h2>", unsafe_allow_html=True)

    # Top KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            """<div class="kpi-card"><div class="kpi-title">إجمالي الإيرادات</div><div class="kpi-value">8,250,000 ج.م</div><div class="kpi-sub">⬆ 12.5% عن الشهر الماضي</div></div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """<div class="kpi-card"><div class="kpi-title">إجمالي المصروفات</div><div class="kpi-value">2,850,000 ج.م</div><div class="kpi-sub" style="color:#f85149">⬇ 3.2% عن الشهر الماضي</div></div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """<div class="kpi-card"><div class="kpi-title">صافي الأرباح</div><div class="kpi-value">5,400,000 ج.م</div><div class="kpi-sub">⬆ 18.7% عن الشهر الماضي</div></div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            """<div class="kpi-card"><div class="kpi-title">قيمة العقارات</div><div class="kpi-value">45,750,000 ج.م</div><div class="kpi-sub">إجمالي المحفظة العقارية</div></div>""",
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            """<div class="kpi-card"><div class="kpi-title">العقارات المباعة</div><div class="kpi-value">12</div><div class="kpi-sub">عقار هذا الشهر</div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Analytics Charts
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("نظرة عامة على الأداء المالي (الإيرادات، المصروفات، الأرباح)")
        months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو"]
        df_perf = pd.DataFrame(
            {
                "الشهر": months,
                "الإيرادات": [4, 4.5, 5.2, 5.8, 6.5, 6.8, 8.25],
                "المصروفات": [1.5, 1.8, 2.0, 2.2, 2.5, 2.4, 2.85],
                "الأرباح": [2.5, 2.7, 3.2, 3.6, 4.0, 4.4, 5.4],
            }
        )
        fig_line = px.line(
            df_perf,
            x="الشهر",
            y=["الإيرادات", "المصروفات", "الأرباح"],
            color_discrete_sequence=["#8a2be2", "#f85149", "#3fb950"],
            markers=True,
        )
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("توزيع المصروفات")
        expenses_data = {
            "الفئة": [
                "شراء عقارات",
                "مصاريف تطوير",
                "مصاريف إدارية",
                "رواتب وأجور",
                "أخرى",
            ],
            "النسبة": [40, 25, 15, 10, 10],
        }
        fig_pie = px.pie(
            expenses_data,
            values="النسبة",
            names="الفئة",
            hole=0.5,
            color_discrete_sequence=[
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
            ],
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tables Summary
    t1, t2 = st.columns(2)
    with t1:
        st.subheader("آخر العقارات المضافة")
        st.dataframe(
            st.session_state["real_estate"], use_container_width=True
        )
    with t2:
        st.subheader("آخر المعاملات المالية")
        st.dataframe(
            st.session_state["financial_data"], use_container_width=True
        )


# ------------------------------------------
# 2- Users and Access Control Section
# ------------------------------------------
elif choice == "المستخدمين والصلاحيات":
    st.markdown("<h2>إدارة المستخدمين وجلسات الدخول</h2>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["قائمة المستخدمين وإضافة مستخدم", "سجل الجلسات"])

    with tab1:
        st.subheader("إضافة مستخدم جديد")
        with st.form("add_user_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_user = st.text_input("اسم المستخدم")
            with col2:
                new_pass = st.text_input("كلمة المرور", type="password")
            with col3:
                role = st.selectbox(
                    "الصلاحية / الدور",
                    ["المدير العام", "إدارة الموارد البشرية", "مالية", "IT Support"],
                )

            if st.form_submit_button("إضافة المستخدم"):
                if new_user and new_pass:
                    new_entry = {
                        "اسم المستخدم": new_user,
                        "كلمة المرور": new_pass,
                        "الدور": role,
                        "آخر نشاط": "لم يدخل بعد",
                        "عنوان IP": "N/A",
                        "تاريخ خروج": "N/A",
                    }
                    st.session_state["users"] = pd.concat(
                        [
                            st.session_state["users"],
                            pd.DataFrame([new_entry]),
                        ],
                        ignore_index=True,
                    )
                    st.success("تم إضافة المستخدم بنجاح")
                    st.rerun()

        st.subheader("المستخدمين الحاليين")
        df_users = st.session_state["users"].copy()
        st.dataframe(df_users, use_container_width=True)

        st.subheader("حذف مستخدم")
        user_to_delete = st.selectbox(
            "اختر المستخدم للحذف", df_users["اسم المستخدم"]
        )
        if st.button("حذف المستخدم المحدد"):
            st.session_state["users"] = st.session_state["users"][
                st.session_state["users"]["اسم المستخدم"] != user_to_delete
            ]
            st.success("تم حذف المستخدم")
            st.rerun()

    with tab2:
        st.subheader("جلسات تسجيل الدخول والأنشطة (IP والوقت)")
        st.dataframe(
            st.session_state["users"][
                [
                    "اسم المستخدم",
                    "الدور",
                    "آخر نشاط",
                    "عنوان IP",
                    "تاريخ خروج",
                ]
            ],
            use_container_width=True,
        )


# ------------------------------------------
# 3- Financial Management Section
# ------------------------------------------
elif choice == "الإدارة المالية":
    st.markdown("<h2>الإدارة المالية والحسابات</h2>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(
        [
            "حاسبة أجور العمال والموردين",
            "الصادرات والواردات والسلف",
            "كشف حساب لكل قسم",
        ]
    )

    with tab1:
        st.subheader("حاسبة مستحقات العمال والموردين")
        c1, c2, c3 = st.columns(3)
        with c1:
            worker_type = st.selectbox(
                "نوع العامل / المهنة", ["نقاش", "نحات", "عامل عادي", "مورد عمال"]
            )
            num_workers = st.number_input(
                "عدد العمال مع المورد", min_value=1, value=1
            )
        with c2:
            hourly_rate = st.number_input("سعر الساعة (ج.م)", min_value=0.0, value=50.0)
            daily_base = st.number_input("سعر اليومية الأساسية (ج.م)", min_value=0.0, value=400.0)
        with c3:
            hours_worked = st.number_input("عدد الساعات المنفذة", min_value=0.0, value=8.0)
            advances = st.number_input("إجمالي السلف المخصومة (ج.م)", min_value=0.0, value=0.0)

        # Calculations
        total_gross = (hours_worked * hourly_rate) * num_workers
        total_net = total_gross - advances

        st.markdown(f"### **إجمالي المستحق الحسابي:** {total_gross:,.2f} ج.م")
        st.markdown(f"### **صافي المستحق بعد السلف:** {total_net:,.2f} ج.م")

    with tab2:
        st.subheader("تسجيل الصادرات (الإيرادات) والواردات (المصروفات)")
        with st.form("financial_entry"):
            c1, c2, c3 = st.
