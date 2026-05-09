"""
خدمات التقارير - Report Service
توليد التقارير والإحصائيات
"""

from db.database import get_db


def get_monthly_income(year: int, month: int):
    """إجمالي الدخل الشهري"""
    db = get_db()
    result = db.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM payments
        WHERE strftime('%Y', payment_date) = ?
          AND strftime('%m', payment_date) = ?
    ''', (str(year), f'{month:02d}')).fetchone()
    return result['total']


def get_patients_count_monthly(year: int, month: int):
    """عدد المرضى الجدد في شهر معين"""
    db = get_db()
    result = db.execute('''
        SELECT COUNT(*) as count
        FROM patients
        WHERE strftime('%Y', created_at) = ?
          AND strftime('%m', created_at) = ?
    ''', (str(year), f'{month:02d}')).fetchone()
    return result['count']


def get_full_report():
    """تقرير شامل للنظام"""
    db = get_db()
    return {
        'total_patients':  db.execute('SELECT COUNT(*) as c FROM patients').fetchone()['c'],
        'total_income':    db.execute('SELECT COALESCE(SUM(amount),0) as t FROM payments').fetchone()['t'],
        'active_plans':    db.execute('SELECT COUNT(*) as c FROM treatment_plans WHERE status="active"').fetchone()['c'],
        'total_appointments': db.execute('SELECT COUNT(*) as c FROM appointments').fetchone()['c'],
        'completed_today': db.execute(
            "SELECT COUNT(*) as c FROM appointments WHERE appointment_date=date('now','localtime') AND status='completed'"
        ).fetchone()['c'],
    }
