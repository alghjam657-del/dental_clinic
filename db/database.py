"""
إدارة قاعدة البيانات - الاتصال والتهيئة
Database Connection and Initialization
"""

import sqlite3
import os
from flask import g, current_app


def get_db():
    """الحصول على اتصال بقاعدة البيانات للطلب الحالي"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  # النتائج كـ dict
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """إغلاق الاتصال بقاعدة البيانات"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = sqlite3.connect(app.config['DATABASE'])
        db.execute("PRAGMA foreign_keys = ON")
        cursor = db.cursor()

        # ─── جدول المستخدمين ───────────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                password    TEXT    NOT NULL,
                full_name   TEXT    NOT NULL,
                role        TEXT    NOT NULL DEFAULT 'staff',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        ''')

        # ─── جدول المرضى ──────────────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name     TEXT    NOT NULL,
                phone         TEXT    NOT NULL,
                email         TEXT,
                date_of_birth TEXT,
                gender        TEXT    DEFAULT 'male',
                address       TEXT,
                notes         TEXT,
                is_deleted    INTEGER NOT NULL DEFAULT 0,
                deleted_at    TEXT,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        ''')

        # ─── جدول خطط العلاج ─────────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS treatment_plans (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id          INTEGER NOT NULL,
                description         TEXT    NOT NULL,
                total_cost          REAL    NOT NULL DEFAULT 0,
                initial_payment     REAL    NOT NULL DEFAULT 0,
                installments_count  INTEGER NOT NULL DEFAULT 1,
                amount_paid         REAL    NOT NULL DEFAULT 0,
                remaining           REAL    GENERATED ALWAYS AS (total_cost - amount_paid) VIRTUAL,
                status              TEXT    NOT NULL DEFAULT 'active',
                created_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')

        # ─── جدول المدفوعات ───────────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id       INTEGER NOT NULL,
                treatment_plan_id INTEGER,
                amount           REAL    NOT NULL,
                payment_date     TEXT    NOT NULL DEFAULT (date('now','localtime')),
                payment_method   TEXT    NOT NULL DEFAULT 'cash',
                notes            TEXT,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (patient_id)        REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (treatment_plan_id) REFERENCES treatment_plans(id) ON DELETE SET NULL
            )
        ''')

        # ─── ترحيل جدول خطط العلاج (قواعد قديمة) ─────────────────
        plan_cols = {row[1]: row for row in cursor.execute("PRAGMA table_info(treatment_plans)").fetchall()}
        if 'initial_payment' not in plan_cols:
            cursor.execute("ALTER TABLE treatment_plans ADD COLUMN initial_payment REAL NOT NULL DEFAULT 0")
        if 'installments_count' not in plan_cols:
            cursor.execute("ALTER TABLE treatment_plans ADD COLUMN installments_count INTEGER NOT NULL DEFAULT 1")
        if 'amount_paid' not in plan_cols:
            cursor.execute("ALTER TABLE treatment_plans ADD COLUMN amount_paid REAL NOT NULL DEFAULT 0")
        if 'status' not in plan_cols:
            cursor.execute("ALTER TABLE treatment_plans ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")

        # ─── ترحيل جدول المدفوعات (قواعد قديمة) ───────────────────
        pay_cols = {row[1]: row for row in cursor.execute("PRAGMA table_info(payments)").fetchall()}
        if 'treatment_plan_id' not in pay_cols:
            cursor.execute("ALTER TABLE payments ADD COLUMN treatment_plan_id INTEGER")

        # ─── ترحيل جدول المرضى ────────────────────────────────────
        patient_cols = {row[1]: row for row in cursor.execute("PRAGMA table_info(patients)").fetchall()}
        if 'is_deleted' not in patient_cols:
            cursor.execute("ALTER TABLE patients ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0")
        if 'deleted_at' not in patient_cols:
            cursor.execute("ALTER TABLE patients ADD COLUMN deleted_at TEXT")

        # ─── جدول الإعدادات ───────────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # ─── جدول سجل النشاطات ───────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                username   TEXT,
                action     TEXT    NOT NULL,
                details    TEXT,
                ip_address TEXT,
                created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        ''')

        # ─── جدول خريطة الأسنان ──────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tooth_records (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                tooth_num  TEXT    NOT NULL,
                status     TEXT    NOT NULL DEFAULT 'healthy',
                notes      TEXT,
                updated_at TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                UNIQUE(patient_id, tooth_num)
            )
        ''')

        # ─── جدول الوصفات الطبية ──────────────────────────────────
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id        INTEGER NOT NULL,
                rx_number         INTEGER,
                patient_age       TEXT,
                prescription_date TEXT,
                drugs             TEXT,
                created_at        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        ''')

        # ترحيل: إنشاء الجدول إن لم يكن موجوداً في قاعدة بيانات قديمة
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prescriptions'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE prescriptions (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id        INTEGER NOT NULL,
                    rx_number         INTEGER,
                    patient_age       TEXT,
                    prescription_date TEXT,
                    drugs             TEXT,
                    created_at        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
                )
            ''')

        db.commit()

        # ─── بيانات افتراضية للإعدادات ────────────────────────────
        default_settings = [
            ('clinic_name',         'عيادة د. علي حسين لطب الأسنان'),
            ('doctor_name',         'د. علي حسين'),
            ('clinic_address',      'بغداد، العراق'),
            ('clinic_phone',        '07700000000'),
            ('clinic_email',        ''),
            ('clinic_hours',        'السبت - الخميس: 9 صباحاً - 5 مساءً'),
            ('currency_symbol',     'د.ع'),
            ('phone_format',        '07XXXXXXXXX'),
            ('appointment_duration','30'),
            ('working_days',        'السبت,الأحد,الاثنين,الثلاثاء,الأربعاء,الخميس'),
            ('work_start_time',     '09:00'),
            ('work_end_time',       '17:00'),
            ('payment_methods',     'نقدي,بطاقة,تحويل بنكي'),
            ('default_installments','3'),
            ('overdue_alert_days',  '7'),
            ('notify_appointments', '1'),
            ('notify_installments', '1'),
            ('notify_followup',     '1'),
            ('date_format',         'YYYY-MM-DD'),
            ('language',            'ar'),
            ('font_size',           'medium'),
            ('report_default_period','month'),
            ('common_diagnoses',    'تسوس,التهاب لثة,كسر سن,اعوجاج أسنان,خراج,تآكل مينا,حساسية أسنان'),
            ('common_treatments',   'حشو,تنظيف,خلع,تركيب تاج,قلع عصب,تقويم,زراعة'),
        ]
        for key, value in default_settings:
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        db.commit()

        # ─── إنشاء مستخدم افتراضي إذا لم يوجد ────────────────────
        import hashlib
        admin_check = cursor.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        ).fetchone()

        if not admin_check:
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                ('admin', password_hash, 'مدير النظام', 'admin')
            )
            db.commit()
        else:
            # ضمان أن الحساب الافتراضي admin يبقى بصلاحية مدير النظام
            cursor.execute(
                "UPDATE users SET full_name = ?, role = ? WHERE username = ?",
                ('مدير النظام', 'admin', 'admin')
            )
            db.commit()

        db.close()
