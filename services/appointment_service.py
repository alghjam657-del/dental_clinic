"""
خدمات المواعيد - Appointment Service
منطق الأعمال الخاص بالمواعيد
"""

from db.database import get_db


def get_appointments_by_date(date_str: str):
    """جلب مواعيد يوم معين مع اسم المريض (بدون المحذوفات)"""
    db = get_db()
    return db.execute('''
        SELECT a.*,
               COALESCE(NULLIF(TRIM(p.full_name), ''), NULLIF(TRIM(a.guest_name), ''), '—') as patient_name,
               COALESCE(NULLIF(TRIM(p.phone), ''), NULLIF(TRIM(a.guest_phone), ''), '') as patient_phone
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        WHERE a.appointment_date = ? AND a.is_deleted = 0 AND (p.is_deleted = 0 OR p.is_deleted IS NULL)
        ORDER BY a.appointment_time
    ''', (date_str,)).fetchall()


def get_all_appointments():
    """جلب جميع المواعيد (بدون المحذوفات)"""
    db = get_db()
    return db.execute('''
        SELECT a.*, COALESCE(NULLIF(TRIM(p.full_name), ''), NULLIF(TRIM(a.guest_name), ''), '—') as patient_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        WHERE a.is_deleted = 0 AND (p.is_deleted = 0 OR p.is_deleted IS NULL)
        ORDER BY a.appointment_date DESC, a.appointment_time
    ''').fetchall()


def create_appointment(data: dict) -> int:
    """إنشاء موعد جديد"""
    db = get_db()
    cursor = db.execute('''
        INSERT INTO appointments (
            patient_id, appointment_date, appointment_time,
            duration_minutes, notes, guest_name, guest_phone
        )
        VALUES (
            :patient_id, :appointment_date, :appointment_time,
            :duration_minutes, :notes, :guest_name, :guest_phone
        )
    ''', data)
    db.commit()
    return cursor.lastrowid


def update_appointment(appt_id: int, data: dict):
    """تعديل بيانات موعد"""
    db = get_db()
    db.execute('''
        UPDATE appointments
        SET patient_id = :patient_id,
            appointment_date = :appointment_date,
            appointment_time = :appointment_time,
            duration_minutes = :duration_minutes,
            notes = :notes,
            guest_name = :guest_name,
            guest_phone = :guest_phone
        WHERE id = :id
    ''', {**data, 'id': appt_id})
    db.commit()


def update_appointment_status(appt_id: int, status: str):
    """تحديث حالة موعد"""
    db = get_db()
    db.execute(
        'UPDATE appointments SET status = ? WHERE id = ?',
        (status, appt_id)
    )
    db.commit()


def delete_appointment(appt_id: int):
    """حذف نهائي لموعد"""
    db = get_db()
    db.execute('DELETE FROM appointments WHERE id = ?', (appt_id,))
    db.commit()


def soft_delete_appointment(appt_id: int):
    """حذف ناعم (Soft Delete) للموعد - يضع علامة حذف"""
    db = get_db()
    db.execute(
        "UPDATE appointments SET is_deleted = 1, deleted_at = datetime('now','localtime') WHERE id = ?",
        (appt_id,)
    )
    db.commit()


def restore_appointment(appt_id: int):
    """استرجاع موعد محذوف"""
    db = get_db()
    db.execute(
        'UPDATE appointments SET is_deleted = 0, deleted_at = NULL WHERE id = ?',
        (appt_id,)
    )
    db.commit()


def get_deleted_appointments():
    """جلب المواعيد المحذوفة (سلة المحذوفات)"""
    db = get_db()
    return db.execute('''
        SELECT a.*,
               COALESCE(NULLIF(TRIM(p.full_name), ''), NULLIF(TRIM(a.guest_name), ''), '—') as patient_name,
               COALESCE(NULLIF(TRIM(p.phone), ''), NULLIF(TRIM(a.guest_phone), ''), '') as patient_phone
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        WHERE a.is_deleted = 1
        ORDER BY a.deleted_at DESC
    ''').fetchall()
