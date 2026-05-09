"""
مسارات لوحة التحكم - Dashboard Routes
عرض الإحصائيات والملخصات
"""

from flask import Blueprint, render_template
from routes.auth import login_required
from db.database import get_db
from routes.finance import _calc_overdue

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """لوحة التحكم الرئيسية"""
    db = get_db()

    # ─── إحصائيات عامة ────────────────────────────────────────────
    total_patients = db.execute('SELECT COUNT(*) as count FROM patients').fetchone()['count']

    total_income = db.execute(
        'SELECT COALESCE(SUM(amount), 0) as total FROM payments'
    ).fetchone()['total']

    total_remaining = db.execute(
        'SELECT COALESCE(SUM(total_cost - amount_paid), 0) as total FROM treatment_plans WHERE status = "active"'
    ).fetchone()['total']

    # ─── آخر المرضى المضافين ──────────────────────────────────────
    recent_patients = db.execute(
        'SELECT * FROM patients ORDER BY created_at DESC LIMIT 5'
    ).fetchall()

    # ─── آخر المدفوعات ────────────────────────────────────────────
    recent_payments = db.execute('''
        SELECT pay.*, p.full_name as patient_name
        FROM payments pay
        JOIN patients p ON pay.patient_id = p.id
        ORDER BY pay.created_at DESC
        LIMIT 5
    ''').fetchall()

    # ─── بيانات الرسم البياني الشهري (آخر 6 أشهر) ────────────────
    monthly_income = db.execute('''
        SELECT strftime('%Y-%m', payment_date) as month,
               SUM(amount) as total
        FROM payments
        WHERE payment_date >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    ''').fetchall()
    monthly_income = [dict(r) for r in monthly_income]

    # ─── مواعيد اليوم ─────────────────────────────────────────────
    today_income = db.execute(
        "SELECT COALESCE(SUM(amount), 0) as t FROM payments WHERE payment_date = date('now','localtime')"
    ).fetchone()['t']

    # ─── مرضى جدد هذا الشهر ───────────────────────────────────────
    new_patients_month = db.execute(
        "SELECT COUNT(*) as c FROM patients WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now','localtime') AND is_deleted = 0"
    ).fetchone()['c']

    # ─── المتأخرون عن الأقساط ─────────────────────────────────────
    overdue_plans = db.execute('''
        SELECT tp.*, p.full_name as patient_name, p.phone as patient_phone
        FROM treatment_plans tp
        JOIN patients p ON tp.patient_id = p.id
        WHERE tp.status = 'active' AND tp.installments_count > 0
          AND (tp.total_cost - tp.amount_paid) > 0
    ''').fetchall()
    overdue_count = len(_calc_overdue(overdue_plans))

    return render_template('dashboard.html',
        overdue_count=overdue_count,
        total_patients=total_patients,
        total_income=total_income,
        total_remaining=total_remaining,
        today_income=today_income,
        new_patients_month=new_patients_month,
        recent_patients=recent_patients,
        recent_payments=recent_payments,
        monthly_income=monthly_income,
    )


