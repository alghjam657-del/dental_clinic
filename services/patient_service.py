"""
خدمات المرضى - Patient Service
منطق الأعمال الخاص بإدارة المرضى
"""

from db.database import get_db


def get_all_patients():
    """جلب جميع المرضى (بدون المحذوفات)"""
    db = get_db()
    return db.execute(
        'SELECT * FROM patients WHERE is_deleted = 0 ORDER BY id'
    ).fetchall()


def get_patient_by_id(patient_id: int):
    """جلب مريض بمعرفه (بدون المحذوفات)"""
    db = get_db()
    return db.execute(
        'SELECT * FROM patients WHERE id = ? AND is_deleted = 0', (patient_id,)
    ).fetchone()


def search_patients(query: str):
    """البحث في المرضى بالاسم أو رقم الهاتف أو رقم التسلسل (بدون المحذوفات)"""
    db = get_db()
    if query.isdigit():
        return db.execute(
            'SELECT * FROM patients WHERE id = ? AND is_deleted = 0 ORDER BY id',
            (int(query),)
        ).fetchall()

    like = f'%{query}%'
    return db.execute(
        'SELECT * FROM patients WHERE (full_name LIKE ? OR phone LIKE ?) AND is_deleted = 0 ORDER BY id',
        (like, like)
    ).fetchall()


def create_patient(data: dict) -> int:
    """إنشاء مريض جديد وإرجاع معرفه — يملأ الفجوات في التسلسل"""
    db = get_db()
    row = db.execute('''
        SELECT COALESCE(MIN(t1.id + 1), 1) AS next_id
        FROM (SELECT 0 AS id UNION ALL SELECT id FROM patients) t1
        LEFT JOIN patients t2 ON t1.id + 1 = t2.id
        WHERE t2.id IS NULL
    ''').fetchone()
    next_id = row['next_id']
    cursor = db.execute('''
        INSERT INTO patients (id, full_name, phone, email, date_of_birth, gender, address, notes)
        VALUES (:id, :full_name, :phone, :email, :date_of_birth, :gender, :address, :notes)
    ''', {'id': next_id, **data})
    db.commit()
    return cursor.lastrowid


def update_patient(patient_id: int, data: dict):
    """تحديث بيانات مريض"""
    db = get_db()
    db.execute('''
        UPDATE patients
        SET full_name=:full_name, phone=:phone, email=:email,
            date_of_birth=:date_of_birth, gender=:gender,
            address=:address, notes=:notes
        WHERE id=:id
    ''', {**data, 'id': patient_id})
    db.commit()


def delete_patient(patient_id: int):
    """حذف نهائي للمريض (والبيانات المرتبطة به بسبب CASCADE)"""
    db = get_db()

    # قبل حذف المريض: خزّن الاسم والهاتف داخل المواعيد كبيانات زائر
    # حتى لا يختفي الاسم لاحقاً عند تحوّل patient_id إلى NULL.
    patient = db.execute(
        'SELECT full_name, phone FROM patients WHERE id = ?',
        (patient_id,)
    ).fetchone()
    if patient:
        db.execute('''
            UPDATE appointments
            SET
                guest_name = COALESCE(NULLIF(TRIM(guest_name), ''), ?),
                guest_phone = COALESCE(NULLIF(TRIM(guest_phone), ''), ?)
            WHERE patient_id = ?
        ''', (patient['full_name'], patient['phone'], patient_id))

    db.execute('DELETE FROM patients WHERE id = ?', (patient_id,))

    # إذا لم يبق أي مريض، أعد ضبط عداد التسلسل ليبدأ من 1.
    # هذا يجعل أول مريض جديد بعد الإفراغ الكامل يأخذ ID = 1.
    remaining = db.execute('SELECT COUNT(*) AS c FROM patients WHERE is_deleted = 0').fetchone()['c']
    if remaining == 0:
        db.execute("DELETE FROM sqlite_sequence WHERE name = 'patients'")

    db.commit()


def soft_delete_patient(patient_id: int):
    """حذف ناعم (Soft Delete) للمريض - يضع علامة حذف"""
    db = get_db()

    # خزّن الاسم والهاتف في المواعيد قبل الحذف
    patient = db.execute(
        'SELECT full_name, phone FROM patients WHERE id = ?',
        (patient_id,)
    ).fetchone()
    if patient:
        db.execute('''
            UPDATE appointments
            SET
                guest_name = COALESCE(NULLIF(TRIM(guest_name), ''), ?),
                guest_phone = COALESCE(NULLIF(TRIM(guest_phone), ''), ?)
            WHERE patient_id = ?
        ''', (patient['full_name'], patient['phone'], patient_id))

    db.execute(
        "UPDATE patients SET is_deleted = 1, deleted_at = datetime('now','localtime') WHERE id = ?",
        (patient_id,)
    )
    db.commit()


def restore_patient(patient_id: int):
    """استرجاع مريض محذوف"""
    db = get_db()
    db.execute(
        'UPDATE patients SET is_deleted = 0, deleted_at = NULL WHERE id = ?',
        (patient_id,)
    )
    db.commit()


def get_deleted_patients():
    """جلب المرضى المحذوفات (سلة المحذوفات)"""
    db = get_db()
    return db.execute(
        'SELECT * FROM patients WHERE is_deleted = 1 ORDER BY deleted_at DESC'
    ).fetchall()
