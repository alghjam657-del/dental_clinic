"""
مسارات القسم الطبي - Medical Routes
الوصفة الطبية
"""

import json
from flask import Blueprint, render_template, request, jsonify
from routes.auth import login_required
from db.database import get_db

medical_bp = Blueprint('medical', __name__, url_prefix='/medical')


@medical_bp.route('/prescription')
@login_required
def prescription_form():
    """واجهة إنشاء وصفة طبية جاهزة للطباعة/PDF"""
    db = get_db()
    patients = db.execute(
        'SELECT id, full_name FROM patients WHERE is_deleted = 0 ORDER BY full_name'
    ).fetchall()

    selected_patient_id = request.args.get('patient_id', type=int)
    selected_patient_name = ''
    if selected_patient_id:
        p = db.execute(
            'SELECT full_name FROM patients WHERE id = ? AND is_deleted = 0',
            (selected_patient_id,)
        ).fetchone()
        if p:
            selected_patient_name = p['full_name']

    return render_template(
        'prescription.html',
        patients=patients,
        selected_patient_id=selected_patient_id,
        selected_patient_name=selected_patient_name,
    )


@medical_bp.route('/prescription/save', methods=['POST'])
@login_required
def save_prescription():
    """حفظ وصفة طبية في ملف المريض"""
    db = get_db()
    data = request.get_json(silent=True) or {}

    patient_id        = data.get('patient_id', type=int) if False else int(data.get('patient_id', 0))
    rx_number         = data.get('rx_number')
    patient_age       = data.get('patient_age', '').strip()
    prescription_date = data.get('prescription_date', '').strip()
    drugs             = data.get('drugs', [])

    if not patient_id:
        return jsonify({'ok': False, 'msg': 'الرجاء اختيار مريض من القائمة أولاً'}), 400

    patient = db.execute(
        'SELECT id FROM patients WHERE id = ? AND is_deleted = 0', (patient_id,)
    ).fetchone()
    if not patient:
        return jsonify({'ok': False, 'msg': 'المريض غير موجود'}), 404

    db.execute(
        '''INSERT INTO prescriptions
           (patient_id, rx_number, patient_age, prescription_date, drugs)
           VALUES (?, ?, ?, ?, ?)''',
        (patient_id, rx_number, patient_age, prescription_date, json.dumps(drugs, ensure_ascii=False))
    )
    db.commit()
    return jsonify({'ok': True, 'msg': 'تم حفظ الوصفة في ملف المريض'})
