import sqlite3, hashlib, secrets, uuid, os
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

# ⚙️ إعداد الصفحة
st.set_page_config(page_title="M H Group ERP", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

# ========== قاعدة البيانات ==========
DATABASE = "mhgroup_erp.db"

def get_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, code TEXT UNIQUE NOT NULL,
            logo TEXT, address TEXT, phone TEXT, email TEXT, tax_id TEXT, is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, full_name TEXT NOT NULL, email TEXT,
            role TEXT NOT NULL CHECK(role IN ('super_admin','admin','manager','accountant','hr','it','viewer')),
            is_active INTEGER DEFAULT 1, last_login TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, module TEXT NOT NULL,
            can_view INTEGER DEFAULT 1, can_create INTEGER DEFAULT 0, can_edit INTEGER DEFAULT 0, can_delete INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, UNIQUE(user_id, module)
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT, user_agent TEXT, login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP, last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, ip_address TEXT, success INTEGER DEFAULT 0,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reason TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, company_id INTEGER DEFAULT 1,
            module TEXT NOT NULL, action TEXT NOT NULL, record_id INTEGER, details TEXT,
            ip_address TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS revenues (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, reference TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, payment_method TEXT,
            received_from TEXT, revenue_date DATE NOT NULL, notes TEXT, created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id), FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, reference TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, payment_method TEXT,
            paid_to TEXT, expense_date DATE NOT NULL, notes TEXT, created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id), FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, employee_id INTEGER, worker_id INTEGER,
            amount REAL NOT NULL, remaining REAL NOT NULL, loan_date DATE NOT NULL, due_date DATE,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','paid','overdue')), notes TEXT,
            created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id), FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS loan_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, loan_id INTEGER NOT NULL, amount REAL NOT NULL,
            payment_date DATE NOT NULL, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES loans(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, employee_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL, position TEXT, department TEXT, email TEXT, phone TEXT,
            salary REAL, hire_date DATE, status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive','terminated')),
            address TEXT, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, worker_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL, trade TEXT, hourly_rate REAL DEFAULT 0, daily_rate REAL DEFAULT 0,
            phone TEXT, status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive')),
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS worker_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, worker_id INTEGER NOT NULL, work_date DATE NOT NULL,
            hours_worked REAL DEFAULT 0, rate_applied REAL DEFAULT 0,
            amount_due REAL GENERATED ALWAYS AS (hours_worked * rate_applied) STORED,
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE, UNIQUE(worker_id, work_date)
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, supplier_id TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL, contact_person TEXT, phone TEXT, email TEXT,
            category TEXT, address TEXT, tax_id TEXT, status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive')),
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, property_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, property_type TEXT NOT NULL, location TEXT, area REAL,
            finishing_status TEXT CHECK(finishing_status IN ('not_started','in_progress','semi_finished','fully_finished')),
            purchase_cost REAL DEFAULT 0, total_expenses REAL DEFAULT 0, selling_price REAL,
            sale_date DATE, buyer_name TEXT,
            profit REAL GENERATED ALWAYS AS (COALESCE(selling_price, 0) - purchase_cost - total_expenses) STORED,
            status TEXT DEFAULT 'available' CHECK(status IN ('available','under_renovation','listed','sold','rented')),
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS property_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, property_id INTEGER NOT NULL, description TEXT NOT NULL,
            amount REAL NOT NULL, expense_date DATE NOT NULL, category TEXT, supplier_id INTEGER, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, item_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, category TEXT, quantity REAL DEFAULT 0, unit TEXT, unit_price REAL DEFAULT 0,
            total_value REAL GENERATED ALWAYS AS (quantity * unit_price) STORED,
            property_id INTEGER, min_quantity REAL DEFAULT 0, location TEXT, notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        );
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
            movement_type TEXT CHECK(movement_type IN ('in','out','adjustment')),
            quantity REAL NOT NULL, reference TEXT, notes TEXT, created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, investor_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive')),
            total_invested REAL DEFAULT 0, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, investor_id INTEGER NOT NULL, property_id INTEGER,
            amount REAL NOT NULL, percentage REAL NOT NULL, expected_return REAL,
            actual_return REAL DEFAULT 0, investment_date DATE NOT NULL, maturity_date DATE,
            status TEXT DEFAULT 'active' CHECK(status IN ('active','completed','cancelled')),
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (investor_id) REFERENCES investors(id) ON DELETE CASCADE,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, document_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL, file_name TEXT, file_data BLOB, file_type TEXT, file_size INTEGER,
            related_type TEXT, related_id INTEGER, uploaded_by INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, notes TEXT,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS it_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER DEFAULT 1, ticket_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL, description TEXT,
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low','medium','high','urgent')),
            status TEXT DEFAULT 'open' CHECK(status IN ('open','in_progress','resolved','closed')),
            reported_by INTEGER, assigned_to INTEGER, resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, resolved_at TIMESTAMP,
            FOREIGN KEY (reported_by) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        );
    ''')
    c.execute("SELECT COUNT(*) FROM companies")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO companies (name, code) VALUES (?, ?)", ('M H Group', 'MHG'))
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (company_id, username, password_hash, full_name, role, email) VALUES (1, 'admin', ?, 'مدير النظام', 'super_admin', 'admin@mhgroup.com')", (pw,))
        user_id = c.lastrowid
        for mod in ['dashboard','users','revenues','expenses','loans','employees','workers',
                    'suppliers','properties','inventory','investors','documents','it_tickets',
                    'audit_log','account_statement','companies','worker_attendance']:
            c.execute("INSERT INTO permissions (user_id, module, can_view, can_create, can_edit, can_delete) VALUES (?,?,1,1,1,1)", (user_id, mod))
    conn.commit()
    conn.close()

init_db()

# ========== دوال مساعدة ==========
def add_audit(user_id, module, action, record_id=None, details=None):
    try:
        conn = get_db()
        ctx = get_script_run_ctx()
        ip = ctx.session_id if ctx else "streamlit"
        conn.execute("INSERT INTO audit_log (user_id, module, action, record_id, details, ip_address) VALUES (?,?,?,?,?,?)",
                     (user_id, module, action, record_id, details, ip))
        conn.commit()
        conn.close()
    except:
        pass

def check_perm(module, action='view'):
    if st.session_state.get('role') == 'super_admin':
        return True
    conn = get_db()
    perm = conn.execute("SELECT * FROM permissions WHERE user_id=? AND module=?",
                        (st.session_state.user_id, module)).fetchone()
    conn.close()
    if not perm:
        return False
    action_map = {'view':'can_view','create':'can_create','edit':'can_edit','delete':'can_delete'}
    return bool(perm[action_map.get(action, 'can_view')])

# ========== CSS مخصص ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; }
    .stApp { background-color: #0d1117; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-left: 2px solid #d4a574; }
    .stButton>button {
        background: #d4a574; color: #0d1117; border: none; border-radius: 8px; font-weight: bold; transition: all 0.3s;
    }
    .stButton>button:hover { background: #e2c5a5; box-shadow: 0 0 15px rgba(212,167,116,0.4); }
    .stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #21262d; border: 1px solid #30363d; color: #e6edf3; border-radius: 8px;
    }
    .stDataFrame { background-color: #1c2333; }
    .metric-card {
        background: #1c2333; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center;
        margin-bottom: 10px;
    }
    .metric-value { font-size: 2em; font-weight: bold; color: #d4a574; }
    .metric-label { color: #8b949e; font-size: 0.9em; }
    h1, h2, h3, h4 { color: #e2c5a5; }
</style>
""", unsafe_allow_html=True)

# ========== حالة الجلسة ==========
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.full_name = None
    st.session_state.role = None
    st.session_state.company_id = 1

# ========== صفحة تسجيل الدخول ==========
def login_page():
    st.markdown("<h1 style='text-align:center;color:#d4a574;'>M H GROUP</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#8b949e;'>نظام تخطيط موارد المؤسسات</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 اسم المستخدم")
            password = st.text_input("🔒 كلمة المرور", type="password")
            submitted = st.form_submit_button("تسجيل الدخول")
            if submitted:
                conn = get_db()
                pw_hash = hashlib.sha256(password.encode()).hexdigest()
                user = conn.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,)).fetchone()
                ctx = get_script_run_ctx()
                ip = ctx.session_id if ctx else "streamlit"
                if user and user['password_hash'] == pw_hash:
                    # نجاح
                    token = secrets.token_hex(32)
                    conn.execute("INSERT INTO sessions (user_id, session_token, ip_address) VALUES (?,?,?)",
                                 (user['id'], token, ip))
                    conn.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user['id'],))
                    conn.execute("INSERT INTO login_attempts (username, ip_address, success) VALUES (?,?,1)", (username, ip))
                    conn.commit()
                    conn.close()
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.full_name = user['full_name']
                    st.session_state.role = user['role']
                    st.session_state.company_id = user['company_id']
                    st.session_state.session_token = token
                    add_audit(user['id'], 'auth', 'login', details=f'IP:{ip}')
                    st.success(f"مرحباً {user['full_name']}!")
                    st.rerun()
                else:
                    conn.execute("INSERT INTO login_attempts (username, ip_address, success, reason) VALUES (?,?,0,?)",
                                 (username, ip, 'بيانات خاطئة' if user else 'المستخدم غير موجود'))
                    conn.commit()
                    conn.close()
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

def logout():
    if st.session_state.get('session_token'):
        conn = get_db()
        conn.execute("UPDATE sessions SET logout_time=CURRENT_TIMESTAMP, is_active=0 WHERE session_token=?",
                     (st.session_state.session_token,))
        conn.commit()
        conn.close()
    add_audit(st.session_state.get('user_id'), 'auth', 'logout')
    for key in ['logged_in','user_id','full_name','role','company_id','session_token']:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

# ========== لوحة التحكم ==========
def dashboard():
    st.title("📊 لوحة التحكم")
    cid = st.session_state.company_id
    conn = get_db()
    rev = conn.execute("SELECT COALESCE(SUM(amount),0) FROM revenues WHERE company_id=?",(cid,)).fetchone()[0]
    exp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE company_id=?",(cid,)).fetchone()[0]
    loans_active = conn.execute("SELECT COALESCE(SUM(remaining),0) FROM loans WHERE company_id=? AND status='active'",(cid,)).fetchone()[0]
    emp_cnt = conn.execute("SELECT COUNT(*) FROM employees WHERE company_id=? AND status='active'",(cid,)).fetchone()[0]
    wrk_cnt = conn.execute("SELECT COUNT(*) FROM workers WHERE company_id=? AND status='active'",(cid,)).fetchone()[0]
    prop_cnt = conn.execute("SELECT COUNT(*) FROM properties WHERE company_id=?",(cid,)).fetchone()[0]
    prop_sold = conn.execute("SELECT COUNT(*) FROM properties WHERE company_id=? AND status='sold'",(cid,)).fetchone()[0]
    inv_val = conn.execute("SELECT COALESCE(SUM(amount),0) FROM investments i JOIN investors inv ON i.investor_id=inv.id WHERE inv.company_id=? AND i.status='active'",(cid,)).fetchone()[0]
    inv_cnt = conn.execute("SELECT COUNT(*) FROM investors WHERE company_id=? AND status='active'",(cid,)).fetchone()[0]
    inv_total = conn.execute("SELECT COALESCE(SUM(total_value),0) FROM inventory_items WHERE company_id=?",(cid,)).fetchone()[0]
    open_tickets = conn.execute("SELECT COUNT(*) FROM it_tickets WHERE company_id=? AND status IN ('open','in_progress')",(cid,)).fetchone()[0]
    conn.close()

    cols = st.columns(4)
    cols[0].metric("📥 الإيرادات", f"{rev:,.0f} ج.م")
    cols[1].metric("📤 المصروفات", f"{exp:,.0f} ج.م")
    cols[2].metric("💰 الصافي", f"{rev-exp:,.0f} ج.م")
    cols[3].metric("💳 السلف النشطة", f"{loans_active:,.0f} ج.م")

    cols2 = st.columns(4)
    cols2[0].metric("👔 موظفين", emp_cnt)
    cols2[1].metric("👷 عمال", wrk_cnt)
    cols2[2].metric("🏢 عقارات", f"{prop_cnt} ({prop_sold} مباع)")
    cols2[3].metric("📦 مخزون", f"{inv_total:,.0f} ج.م")

    cols3
