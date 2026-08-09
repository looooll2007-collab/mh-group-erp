import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, flash, g, abort

app = Flask(__name__)
app.secret_key = 'mh_group_secret_key_2026'
DATABASE = 'mh_group_erp.db'

# ==========================================
# 1. تهيئة قاعدة البيانات والتحديث التلقائي
# ==========================================

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_and_migrate_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # جدول العقارات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                finishing TEXT,
                location TEXT,
                price REAL,
                status TEXT DEFAULT 'متاح',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # التحقق من الأعمدة وإضافتها إن كانت مفقودة
        cursor.execute("PRAGMA table_info(properties)")
        columns = [column[1] for column in cursor.fetchall()]
        required_columns = {
            'name': 'TEXT',
            'type': 'TEXT',
            'finishing': 'TEXT',
            'location': 'TEXT',
            'price': 'REAL',
            'status': "TEXT DEFAULT 'متاح'"
        }
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}")

        # جدول المعاملات والقبض
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                payment_method TEXT DEFAULT 'نقداً',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول العقود
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_name TEXT NOT NULL,
                contract_type TEXT NOT NULL,
                total_amount REAL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        db.commit()

init_and_migrate_db()


# ==========================================
# 2. قوالب الـ HTML (Embedded Templates)
# ==========================================

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>MH GROUP - نظام إدارة العقارات والسندات</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
<div class="container">
    <h1 class="mb-4 text-primary font-weight-bold">MH GROUP ERP</h1>

    <!-- التنبيهات -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="row">
        <!-- إضافة عقار -->
        <div class="col-md-6 mb-4">
            <div class="card shadow-sm">
                <div class="card-header bg-dark text-white">إضافة عقار جديد</div>
                <div class="card-body">
                    <form action="/add_property" method="POST">
                        <div class="mb-2"><input type="text" name="name" class="form-control" placeholder="اسم العقار / البرج" required></div>
                        <div class="mb-2"><input type="text" name="type" class="form-control" placeholder="النوع (شقة / محل / فيلا)"></div>
                        <div class="mb-2"><input type="text" name="finishing" class="form-control" placeholder="مستوى التشطيب"></div>
                        <div class="mb-2"><input type="text" name="location" class="form-control" placeholder="الموقع / العنوان"></div>
                        <div class="mb-2"><input type="number" name="price" class="form-control" placeholder="السعر" step="0.01"></div>
                        <button type="submit" class="btn btn-success w-100">حفظ العقار</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- إضافة سند / معاملة مالية -->
        <div class="col-md-6 mb-4">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">تسجيل سند قبض جديد</div>
                <div class="card-body">
                    <form action="/add_transaction" method="POST">
                        <div class="mb-2"><input type="text" name="client_name" class="form-control" placeholder="اسم العميل / المستثمر" required></div>
                        <div class="mb-2"><input type="number" name="amount" class="form-control" placeholder="المبلغ (ج.م)" required step="0.01"></div>
                        <div class="mb-2"><input type="text" name="description" class="form-control" placeholder="البيان / السبب"></div>
                        <div class="mb-2">
                            <select name="payment_method" class="form-select">
                                <option value="نقداً">نقداً</option>
                                <option value="تحويل بنكي">تحويل بنكي</option>
                                <option value="شيك">شيك</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">تسجيل السند</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- جدول السندات المتاحة للطباعة -->
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-secondary text-white">سندات القبض (جاهزة للطباعة / PDF)</div>
        <div class="card-body">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>اسم العميل</th>
                        <th>المبلغ</th>
                        <th>البيان</th>
                        <th>طريقة الدفع</th>
                        <th>الخيارات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in transactions %}
                    <tr>
                        <td>{{ item.id }}</td>
                        <td>{{ item.client_name }}</td>
                        <td>{{ item.amount }} ج.م</td>
                        <td>{{ item.description }}</td>
                        <td>{{ item.payment_method }}</td>
                        <td>
                            <a href="/print/receipt/{{ item.id }}" target="_blank" class="btn btn-sm btn-outline-primary">🖨️ طباعة السند / PDF</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="6" class="text-center">لا توجد سندات مسجلة حتى الآن</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

</div>
</body>
</html>
'''

RECEIPT_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>سند قبض #{{ receipt.id }} - MH Group</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f8f9fa; padding: 30px; }
        .receipt-card { max-width: 650px; margin: auto; background: #fff; padding: 30px; border: 2px solid #1a365d; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 15px; }
        .amount-box { background: #e2e8f0; font-size: 22px; font-weight: bold; text-align: center; padding: 12px; margin: 25px 0; color: #2b6cb0; border-radius: 6px; border: 1px solid #cbd5e0; }
        .row-item { margin-bottom: 15px; font-size: 16px; line-height: 1.6; }
        .signatures { display: flex; justify-content: space-between; margin-top: 50px; padding-top: 20px; border-top: 1px dashed #ccc; }
        .no-print { text-align: center; margin-bottom: 20px; }
        .btn-print { background: #2b6cb0; color: white; border: none; padding: 10px 25px; font-size: 16px; border-radius: 5px; cursor: pointer; }
        @media print { .no-print { display: none; } body { background: none; padding: 0; } .receipt-card { border: 1px solid #000; box-shadow: none; } }
    </style>
</head>
<body onload="window.print()">

    <div class="no-print">
        <button class="btn-print" onclick="window.print()">🖨️ طباعة السند / حفظ كـ PDF</button>
    </div>

    <div class="receipt-card">
        <div class="header">
            <div>
                <h2 style="margin:0; color:#1a365d;">MH GROUP</h2>
                <small>إدارة العقارات والخدمات الماليّة</small>
            </div>
            <div style="text-align: left;">
                <div style="font-weight: bold;">رقم السند: #{{ receipt.id }}</div>
                <small>التاريخ: {{ receipt.created_at }}</small>
            </div>
        </div>

        <h3 style="text-align: center; margin-top: 20px; color: #2d3748;">إيصال استلام نقدية (سند قبض)</h3>

        <div class="row-item"><strong>استلمنا من السيد / السادة:</strong> {{ receipt.client_name }}</div>
        
        <div class="amount-box">المبلغ المدفوع: {{ receipt.amount }} جنيه مصري</div>
        
        <div class="row-item"><strong>وذلك عن:</strong> {{ receipt.description or 'سداد دفعة حساب' }}</div>
        <div class="row-item"><strong>طريقة الدفع:</strong> {{ receipt.payment_method }}</div>

        <div class="signatures">
            <div><strong>اسم المستلم:</strong> ....................</div>
            <div><strong>التوقيع والختم:</strong> ....................</div>
        </div>
    </div>

</body>
</html>
'''

# ==========================================
# 3. مسارات التطبيق (Routes)
# ==========================================

@app.route('/')
def index():
    db = get_db()
    properties = db.execute('SELECT * FROM properties ORDER BY id DESC').fetchall()
    transactions = db.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
    return render_template_string(INDEX_HTML, properties=properties, transactions=transactions)

@app.route('/add_property', methods=['POST'])
def add_property():
    try:
        db = get_db()
        db.execute('''
            INSERT INTO properties (name, type, finishing, location, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            request.form.get('name'),
            request.form.get('type'),
            request.form.get('finishing'),
            request.form.get('location'),
            request.form.get('price')
        ))
        db.commit()
        flash('تم حفظ العقار بنجاح!', 'success')
    except Exception as e:
        flash(f'خطأ أثناء الحفظ: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        db = get_db()
        db.execute('''
            INSERT INTO transactions (client_name, amount, description, payment_method)
            VALUES (?, ?, ?, ?)
        ''', (
            request.form.get('client_name'),
            request.form.get('amount'),
            request.form.get('description'),
            request.form.get('payment_method')
        ))
        db.commit()
        flash('تم تسجيل السند بنجاح!', 'success')
    except Exception as e:
        flash(f'خطأ أثناء تسجيل السند: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/print/receipt/<int:transaction_id>')
def print_receipt(transaction_id):
    db = get_db()
    receipt = db.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    if not receipt:
        return "السند غير موجود", 404
    return render_template_string(RECEIPT_HTML, receipt=receipt)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
