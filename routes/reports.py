"""
مسارات التقارير - Reports Routes
إحصائيات وتقارير الإيرادات والمرضى
"""

from flask import Blueprint, render_template
from routes.auth import login_required
from db.database import get_db

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    """صفحة التقارير"""
    db = get_db()

    # ─── الدخل الشهري (آخر 12 شهراً) ────────────────────────────
    monthly_income = db.execute('''
        SELECT strftime('%Y-%m', payment_date) as month,
               SUM(amount) as total
        FROM payments
        WHERE payment_date >= date('now', '-12 months')
        GROUP BY month
        ORDER BY month
    ''').fetchall()
    monthly_income = [dict(r) for r in monthly_income]

    # ─── مرضى جدد شهرياً (آخر 12 شهراً) ─────────────────────────
    monthly_patients = db.execute('''
        SELECT strftime('%Y-%m', created_at) as month,
               COUNT(*) as total
        FROM patients
        WHERE created_at >= date('now', '-12 months')
        GROUP BY month
        ORDER BY month
    ''').fetchall()
    monthly_patients = [dict(r) for r in monthly_patients]

    # ─── أعلى 10 مرضى دفعاً ──────────────────────────────────────
    top_payers = db.execute('''
        SELECT p.id, p.full_name,
               COALESCE(SUM(pay.amount), 0) as total_paid
        FROM patients p
        LEFT JOIN payments pay ON p.id = pay.patient_id
        GROUP BY p.id
        ORDER BY total_paid DESC
        LIMIT 10
    ''').fetchall()

    # ─── الديون المتبقية ──────────────────────────────────────────
    debts = db.execute('''
        SELECT p.id, p.full_name, p.phone,
               SUM(tp.total_cost - tp.amount_paid) as remaining
        FROM treatment_plans tp
        JOIN patients p ON tp.patient_id = p.id
        WHERE tp.status = 'active'
          AND (tp.total_cost - tp.amount_paid) > 0
        GROUP BY p.id
        ORDER BY remaining DESC
        LIMIT 10
    ''').fetchall()

    # ─── حالة المواعيد ────────────────────────────────────────────
    appt_stats = db.execute('''
        SELECT status, COUNT(*) as cnt
        FROM appointments
        WHERE is_deleted = 0
        GROUP BY status
    ''').fetchall()
    appt_stats = [dict(r) for r in appt_stats]

    # ─── أكثر المرضى زيارةً ──────────────────────────────────────
    top_visitors = db.execute('''
        SELECT p.id, p.full_name, p.phone,
               COUNT(a.id) as visit_count,
               MAX(a.appointment_date) as last_visit
        FROM patients p
        JOIN appointments a ON p.id = a.patient_id
        WHERE a.status = 'completed' AND a.is_deleted = 0
        GROUP BY p.id
        ORDER BY visit_count DESC
        LIMIT 10
    ''').fetchall()

    # ─── أيام الأسبوع الأكثر ازدحاماً ───────────────────────────
    busy_days = db.execute('''
        SELECT strftime('%w', appointment_date) as dow,
               COUNT(*) as cnt
        FROM appointments
        WHERE is_deleted = 0
        GROUP BY dow
        ORDER BY dow
    ''').fetchall()
    busy_days = [dict(r) for r in busy_days]

    # ─── ملخص ─────────────────────────────────────────────────────
    total_income    = db.execute('SELECT COALESCE(SUM(amount),0) as t FROM payments').fetchone()['t']
    total_remaining = db.execute(
        "SELECT COALESCE(SUM(total_cost - amount_paid),0) as t FROM treatment_plans WHERE status='active'"
    ).fetchone()['t']
    total_patients  = db.execute('SELECT COUNT(*) as c FROM patients WHERE is_deleted = 0').fetchone()['c']
    total_appts     = db.execute('SELECT COUNT(*) as c FROM appointments WHERE is_deleted = 0').fetchone()['c']

    # ─── دخل هذا الشهر مقارنة بالشهر الماضي ─────────────────────
    income_this_month = db.execute(
        "SELECT COALESCE(SUM(amount),0) as t FROM payments WHERE strftime('%Y-%m', payment_date) = strftime('%Y-%m','now','localtime')"
    ).fetchone()['t']
    income_last_month = db.execute(
        "SELECT COALESCE(SUM(amount),0) as t FROM payments WHERE strftime('%Y-%m', payment_date) = strftime('%Y-%m', date('now','-1 month','localtime'))"
    ).fetchone()['t']

    return render_template('reports.html',
        monthly_income=monthly_income,
        monthly_patients=monthly_patients,
        top_payers=top_payers,
        debts=debts,
        appt_stats=appt_stats,
        top_visitors=top_visitors,
        busy_days=busy_days,
        total_income=total_income,
        total_remaining=total_remaining,
        total_patients=total_patients,
        total_appts=total_appts,
        income_this_month=income_this_month,
        income_last_month=income_last_month,
    )
