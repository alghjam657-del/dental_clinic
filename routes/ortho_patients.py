"""
مسارات مرضى التقويم - Ortho Patients Routes
إدارة بيانات مرضى التقويم (إضافة، تعديل، حذف، عرض)
"""


from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from routes.auth import login_required
from services.ortho_service import get_all_ortho_patients

ortho_bp = Blueprint('ortho_patients', __name__, url_prefix='/ortho')

@ortho_bp.route('/')
@login_required
def index():
    """عرض قائمة مرضى التقويم"""
    patients = get_all_ortho_patients()
    return render_template('ortho_patients.html', patients=patients)

@ortho_bp.route('/add', methods=['POST'])
@login_required
def add():
    """إضافة مريض تقويم جديد"""
    # سنكمل لاحقًا: إضافة مريض تقويم
    return jsonify({'success': True, 'message': 'تم إضافة مريض التقويم (تجريبي)'})

# يمكن إضافة المزيد من المسارات لاحقًا (تعديل، حذف، ملف المريض)
