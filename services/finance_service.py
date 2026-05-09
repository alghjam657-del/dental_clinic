"""
خدمات المالية - Finance Service
منطق الأعمال الخاص بالمدفوعات وخطط العلاج
"""

from db.database import get_db


def get_all_treatment_plans():
    """جلب جميع خطط العلاج مع أسماء المرضى"""
    db = get_db()
    return db.execute('''
        SELECT tp.*, p.full_name as patient_name
        FROM treatment_plans tp
        JOIN patients p ON tp.patient_id = p.id
        ORDER BY tp.created_at DESC
    ''').fetchall()


def get_treatment_plan_by_id(plan_id: int):
    """جلب خطة علاج بمعرفها"""
    db = get_db()
    return db.execute(
        'SELECT * FROM treatment_plans WHERE id = ?', (plan_id,)
    ).fetchone()


def create_treatment_plan(data: dict) -> int:
    """إنشاء خطة علاج جديدة"""
    db = get_db()

    initial_payment    = float(data.get('initial_payment', 0))
    total_cost         = float(data.get('total_cost', 0))
    installments_count = int(data.get('installments_count', 1))

    cursor = db.execute('''
        INSERT INTO treatment_plans
            (patient_id, description, total_cost, initial_payment, installments_count, amount_paid)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['patient_id'],
        data['description'],
        total_cost,
        initial_payment,
        installments_count,
        initial_payment   # الدفعة الأولى تُحسب ضمن المدفوع
    ))

    plan_id = cursor.lastrowid

    # تسجيل الدفعة الأولى تلقائياً
    if initial_payment > 0:
        db.execute('''
            INSERT INTO payments (patient_id, treatment_plan_id, amount, payment_method, notes)
            VALUES (?, ?, ?, 'cash', 'دفعة أولى')
        ''', (data['patient_id'], plan_id, initial_payment))

    db.commit()
    return plan_id


def add_payment(data: dict) -> int:
    """تسجيل دفعة جديدة وتحديث الرصيد في خطة العلاج"""
    db = get_db()
    amount = float(data['amount'])

    cursor = db.execute('''
        INSERT INTO payments (patient_id, treatment_plan_id, amount, payment_date, payment_method, notes)
        VALUES (:patient_id, :treatment_plan_id, :amount, :payment_date, :payment_method, :notes)
    ''', data)

    # تحديث إجمالي المدفوع في خطة العلاج
    if data.get('treatment_plan_id'):
        db.execute('''
            UPDATE treatment_plans
            SET amount_paid = amount_paid + ?
            WHERE id = ?
        ''', (amount, data['treatment_plan_id']))

        # تحديث حالة الخطة إذا اكتمل السداد
        plan = db.execute(
            'SELECT total_cost, amount_paid FROM treatment_plans WHERE id = ?',
            (data['treatment_plan_id'],)
        ).fetchone()
        if plan and plan['amount_paid'] >= plan['total_cost']:
            db.execute(
                'UPDATE treatment_plans SET status = "completed" WHERE id = ?',
                (data['treatment_plan_id'],)
            )

    db.commit()
    return cursor.lastrowid


def get_payments_for_patient(patient_id: int):
    """جلب جميع مدفوعات مريض"""
    db = get_db()
    return db.execute(
        'SELECT * FROM payments WHERE patient_id = ? ORDER BY payment_date DESC',
        (patient_id,)
    ).fetchall()


def get_all_payments():
    """جلب جميع المدفوعات"""
    db = get_db()
    return db.execute('''
        SELECT pay.*, p.full_name as patient_name
        FROM payments pay
        JOIN patients p ON pay.patient_id = p.id
        ORDER BY pay.payment_date DESC
    ''').fetchall()


def get_financial_summary():
    """ملخص مالي شامل"""
    db = get_db()
    total_income = db.execute(
        'SELECT COALESCE(SUM(amount), 0) as t FROM payments'
    ).fetchone()['t']

    total_plans = db.execute(
        'SELECT COALESCE(SUM(total_cost), 0) as t FROM treatment_plans'
    ).fetchone()['t']

    total_remaining = db.execute(
        'SELECT COALESCE(SUM(total_cost - amount_paid), 0) as t FROM treatment_plans WHERE status="active"'
    ).fetchone()['t']

    return {
        'total_income':    total_income,
        'total_plans':     total_plans,
        'total_remaining': total_remaining,
    }
