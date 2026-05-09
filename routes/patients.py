"""
مسارات المرضى - Patients Routes
إدارة بيانات المرضى (إضافة، تعديل، حذف، عرض)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from routes.auth import login_required
from services.patient_service import (
    get_all_patients, get_patient_by_id, create_patient,
    update_patient, delete_patient, search_patients,
    soft_delete_patient, restore_patient, get_deleted_patients
)

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')


@patients_bp.route('/')
@login_required
def index():
    """عرض قائمة المرضى"""
    search = request.args.get('q', '').strip()
    if search:
        patients = search_patients(search)
    else:
        patients = get_all_patients()
    return render_template('patients.html', patients=patients, search=search)


@patients_bp.route('/add', methods=['POST'])
@login_required
def add():
    """إضافة مريض جديد"""
    data = {
        'full_name':     request.form.get('full_name', '').strip(),
        'phone':         request.form.get('phone', '').strip(),
        'email':         request.form.get('email', '').strip(),
        'date_of_birth': request.form.get('date_of_birth', '').strip(),
        'gender':        request.form.get('gender', 'male'),
        'address':       request.form.get('address', '').strip(),
        'notes':         request.form.get('notes', '').strip(),
    }

    if not data['full_name'] or not data['phone']:
        return jsonify({'success': False, 'message': 'الاسم ورقم الهاتف مطلوبان'}), 400

    patient_id = create_patient(data)
    return jsonify({'success': True, 'message': 'تم إضافة المريض بنجاح', 'id': patient_id})


@patients_bp.route('/<int:patient_id>', methods=['GET'])
@login_required
def get_patient(patient_id):
    """جلب بيانات مريض واحد (JSON)"""
    patient = get_patient_by_id(patient_id)
    if not patient:
        return jsonify({'success': False, 'message': 'المريض غير موجود'}), 404
    return jsonify({'success': True, 'patient': dict(patient)})


@patients_bp.route('/<int:patient_id>/update', methods=['POST'])
@login_required
def update(patient_id):
    """تعديل بيانات مريض"""
    data = {
        'full_name':     request.form.get('full_name', '').strip(),
        'phone':         request.form.get('phone', '').strip(),
        'email':         request.form.get('email', '').strip(),
        'date_of_birth': request.form.get('date_of_birth', '').strip(),
        'gender':        request.form.get('gender', 'male'),
        'address':       request.form.get('address', '').strip(),
        'notes':         request.form.get('notes', '').strip(),
    }

    if not data['full_name'] or not data['phone']:
        return jsonify({'success': False, 'message': 'الاسم ورقم الهاتف مطلوبان'}), 400

    update_patient(patient_id, data)
    return jsonify({'success': True, 'message': 'تم تحديث بيانات المريض'})


@patients_bp.route('/<int:patient_id>/delete', methods=['POST'])
@login_required
def delete(patient_id):
    """حذف ناعم (Soft Delete) للمريض - ينقله إلى سلة المحذوفات"""
    soft_delete_patient(patient_id)
    return jsonify({'success': True, 'message': 'تم نقل المريض إلى سلة المحذوفات'})


@patients_bp.route('/<int:patient_id>/profile')
@login_required
def profile(patient_id):
    """صفحة ملف المريض الكامل"""
    from db.database import get_db
    db = get_db()

    patient = get_patient_by_id(patient_id)
    if not patient:
        flash('المريض غير موجود', 'error')
        return redirect(url_for('patients.index'))

    treatment_plans = db.execute(
        'SELECT * FROM treatment_plans WHERE patient_id = ? ORDER BY created_at DESC',
        (patient_id,)
    ).fetchall()

    payments = db.execute(
        '''SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY patient_id
                   ORDER BY payment_date, id
               ) as payment_num
           FROM payments
           WHERE patient_id = ?
           ORDER BY payment_date, id''',
        (patient_id,)
    ).fetchall()

    tooth_rows = db.execute(
        'SELECT tooth_num, status, notes FROM tooth_records WHERE patient_id = ?',
        (patient_id,)
    ).fetchall()
    tooth_map = {r['tooth_num']: {'status': r['status'], 'notes': r['notes'] or ''} for r in tooth_rows}

    # ─── ملخص مالي ────────────────────────────────────────────────
    fin = db.execute('''
        SELECT
            COALESCE(SUM(tp.total_cost), 0)    as total_cost,
            COALESCE(SUM(tp.amount_paid), 0)   as total_paid,
            COALESCE(SUM(tp.total_cost - tp.amount_paid), 0) as total_remaining
        FROM treatment_plans tp
        WHERE tp.patient_id = ?
    ''', (patient_id,)).fetchone()

    # ─── آخر زيارة ────────────────────────────────────────────────
    last_visit = db.execute('''
        SELECT appointment_date FROM appointments
        WHERE patient_id = ? AND status = 'completed' AND is_deleted = 0
        ORDER BY appointment_date DESC LIMIT 1
    ''', (patient_id,)).fetchone()

    # ─── الوصفات الطبية ───────────────────────────────────────────
    import json as _json
    rx_rows = db.execute(
        'SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY created_at DESC',
        (patient_id,)
    ).fetchall()
    prescriptions = []
    for r in rx_rows:
        try:
            drugs = _json.loads(r['drugs'] or '[]')
        except Exception:
            drugs = []
        prescriptions.append({
            'id':                r['id'],
            'rx_number':         r['rx_number'],
            'patient_age':       r['patient_age'],
            'prescription_date': r['prescription_date'],
            'drugs':             drugs,
            'created_at':        r['created_at'],
        })

    return render_template('patient_profile.html',
        patient=patient,
        treatment_plans=treatment_plans,
        payments=payments,
        tooth_map=tooth_map,
        fin=fin,
        prescriptions=prescriptions,
    )


@patients_bp.route('/<int:patient_id>/tooth/save', methods=['POST'])
@login_required
def save_tooth(patient_id):
    """حفظ حالة سن"""
    tooth_num = request.form.get('tooth_num', '').strip()
    status    = request.form.get('status', 'healthy')
    notes     = request.form.get('notes', '').strip()

    allowed_statuses = ['healthy', 'filling', 'crown', 'extracted', 'root_canal', 'implant', 'needs_treatment']
    if not tooth_num or status not in allowed_statuses:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'}), 400

    db = get_db()
    db.execute('''
        INSERT INTO tooth_records (patient_id, tooth_num, status, notes, updated_at)
        VALUES (?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(patient_id, tooth_num)
        DO UPDATE SET status=excluded.status, notes=excluded.notes, updated_at=excluded.updated_at
    ''', (patient_id, tooth_num, status, notes))
    db.commit()
    return jsonify({'success': True, 'message': 'تم حفظ حالة السن'})


@patients_bp.route('/trash')
@login_required
def trash():
    """صفحة سلة المحذوفات"""
    deleted = get_deleted_patients()
    return render_template('trash/patients_trash.html', deleted_patients=deleted, now=date.today())


@patients_bp.route('/<int:patient_id>/restore', methods=['POST'])
@login_required
def restore(patient_id):
    """استرجاع مريض محذوف"""
    restore_patient(patient_id)
    return jsonify({'success': True, 'message': 'تم استرجاع المريض بنجاح'})


@patients_bp.route('/<int:patient_id>/permanent-delete', methods=['POST'])
@login_required
def permanent_delete(patient_id):
    """حذف نهائي للمريض"""
    delete_patient(patient_id)
    return jsonify({'success': True, 'message': 'تم حذف المريض نهائياً'})
