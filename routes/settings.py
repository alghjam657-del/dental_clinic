"""
إعدادات النظام
System Settings Blueprint
"""

import json
import os
import shutil
from datetime import datetime

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for, jsonify, current_app)

from db.database import get_db
from routes.auth import login_required
from security_utils import hash_password, verify_password

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


def get_all_settings():
    """تحميل كل الإعدادات من قاعدة البيانات كـ dict"""
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    return {row['key']: row['value'] for row in rows}


def set_setting(key, value):
    """حفظ إعداد واحد"""
    get_db().execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    get_db().commit()


def log_activity(action, details=None):
    """تسجيل نشاط في سجل النشاطات"""
    try:
        get_db().execute(
            """INSERT INTO activity_log (user_id, username, action, details, ip_address)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session.get('user_id'),
                session.get('username', ''),
                action,
                details,
                request.remote_addr
            )
        )
        get_db().commit()
    except Exception:
        pass


# ─── الصفحة الرئيسية للإعدادات ────────────────────────────────────────────
@settings_bp.route('/')
@login_required
def index():
    cfg = get_all_settings()
    db = get_db()
    users = db.execute(
        "SELECT id, username, full_name, role, created_at FROM users ORDER BY id"
    ).fetchall()
    logs = db.execute(
        "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    active_tab = request.args.get('tab', 'clinic')
    return render_template('settings.html',
                           cfg=cfg,
                           users=users,
                           logs=logs,
                           active_tab=active_tab)


# ─── حفظ بيانات العيادة ───────────────────────────────────────────────────
@settings_bp.route('/clinic', methods=['POST'])
@login_required
def save_clinic():
    db = get_db()
    fields = ['clinic_name', 'doctor_name', 'clinic_address',
              'clinic_phone', 'clinic_email', 'clinic_hours']
    for field in fields:
        val = request.form.get(field, '').strip()
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل بيانات العيادة')
    flash('تم حفظ بيانات العيادة بنجاح', 'success')
    return redirect(url_for('settings.index', tab='clinic'))


# ─── حفظ إعدادات المرضى ───────────────────────────────────────────────────
@settings_bp.route('/patients', methods=['POST'])
@login_required
def save_patients():
    db = get_db()
    for field in ['phone_format', 'currency_symbol']:
        val = request.form.get(field, '').strip()
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل إعدادات المرضى')
    flash('تم حفظ إعدادات المرضى بنجاح', 'success')
    return redirect(url_for('settings.index', tab='patients'))


# ─── حفظ إعدادات المواعيد ─────────────────────────────────────────────────
@settings_bp.route('/appointments', methods=['POST'])
@login_required
def save_appointments():
    db = get_db()
    for field in ['appointment_duration', 'working_days',
                  'work_start_time', 'work_end_time']:
        val = request.form.get(field, '').strip()
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل إعدادات المواعيد')
    flash('تم حفظ إعدادات المواعيد بنجاح', 'success')
    return redirect(url_for('settings.index', tab='appointments'))


# ─── حفظ إعدادات المالية ──────────────────────────────────────────────────
@settings_bp.route('/finance', methods=['POST'])
@login_required
def save_finance():
    db = get_db()
    for field in ['currency_symbol', 'payment_methods',
                  'default_installments', 'overdue_alert_days']:
        val = request.form.get(field, '').strip()
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل إعدادات المالية')
    flash('تم حفظ إعدادات المالية بنجاح', 'success')
    return redirect(url_for('settings.index', tab='finance'))


# ─── حفظ إعدادات السجلات الطبية ──────────────────────────────────────────
@settings_bp.route('/medical', methods=['POST'])
@login_required
def save_medical():
    db = get_db()
    for field in ['common_diagnoses', 'common_treatments']:
        val = request.form.get(field, '').strip()
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل إعدادات السجلات الطبية')
    flash('تم حفظ إعدادات السجلات الطبية بنجاح', 'success')
    return redirect(url_for('settings.index', tab='medical'))


# ─── حفظ إعدادات الإشعارات ────────────────────────────────────────────────
@settings_bp.route('/notifications', methods=['POST'])
@login_required
def save_notifications():
    db = get_db()
    for field in ['notify_appointments', 'notify_installments', 'notify_followup']:
        val = '1' if request.form.get(field) else '0'
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل إعدادات الإشعارات')
    flash('تم حفظ إعدادات الإشعارات بنجاح', 'success')
    return redirect(url_for('settings.index', tab='notifications'))


# ─── حفظ إعدادات الواجهة ─────────────────────────────────────────────────
@settings_bp.route('/interface', methods=['POST'])
@login_required
def save_interface():
    db = get_db()
    for field in ['date_format', 'language', 'font_size']:
        val = request.form.get(field, '').strip()
        db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (field, val))
    db.commit()
    log_activity('تعديل إعدادات الواجهة')
    flash('تم حفظ إعدادات الواجهة بنجاح', 'success')
    return redirect(url_for('settings.index', tab='interface'))


# ─── إدارة المستخدمين ─────────────────────────────────────────────────────
@settings_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لإضافة مستخدمين', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    username  = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password  = request.form.get('password', '').strip()
    role      = request.form.get('role', 'staff').strip()

    if not username or not full_name or not password:
        flash('يرجى تعبئة جميع الحقول المطلوبة', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        flash('اسم المستخدم موجود مسبقاً', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    pw_hash = hash_password(password)
    db.execute(
        "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
        (username, pw_hash, full_name, role)
    )
    db.commit()
    log_activity('إضافة مستخدم', f'اسم المستخدم: {username}')
    flash(f'تم إضافة المستخدم "{full_name}" بنجاح', 'success')
    return redirect(url_for('settings.index', tab='users'))


@settings_bp.route('/users/<int:uid>/edit', methods=['POST'])
@login_required
def edit_user(uid):
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لتعديل المستخدمين', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    full_name = request.form.get('full_name', '').strip()
    role      = request.form.get('role', 'staff').strip()
    password  = request.form.get('password', '').strip()

    db = get_db()
    if password:
        pw_hash = hash_password(password)
        db.execute(
            "UPDATE users SET full_name=?, role=?, password=? WHERE id=?",
            (full_name, role, pw_hash, uid)
        )
    else:
        db.execute(
            "UPDATE users SET full_name=?, role=? WHERE id=?",
            (full_name, role, uid)
        )
    db.commit()
    log_activity('تعديل مستخدم', f'ID: {uid}')
    flash('تم تعديل بيانات المستخدم بنجاح', 'success')
    return redirect(url_for('settings.index', tab='users'))


@settings_bp.route('/users/<int:uid>/delete', methods=['POST'])
@login_required
def delete_user(uid):
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لحذف المستخدمين', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    if uid == session.get('user_id'):
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    db = get_db()
    user = db.execute("SELECT username FROM users WHERE id=?", (uid,)).fetchone()
    if user and user['username'] == 'admin':
        flash('لا يمكن حذف حساب المدير الافتراضي', 'danger')
        return redirect(url_for('settings.index', tab='users'))

    db.execute("DELETE FROM users WHERE id=?", (uid,))
    db.commit()
    log_activity('حذف مستخدم', f'ID: {uid}')
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('settings.index', tab='users'))


# ─── تغيير كلمة المرور ────────────────────────────────────────────────────
@settings_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_pw  = request.form.get('old_password', '')
    new_pw  = request.form.get('new_password', '')
    conf_pw = request.form.get('confirm_password', '')

    if new_pw != conf_pw:
        flash('كلمة المرور الجديدة وتأكيدها غير متطابقتين', 'danger')
        return redirect(url_for('settings.index', tab='security'))

    if len(new_pw) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'danger')
        return redirect(url_for('settings.index', tab='security'))

    db = get_db()
    user = db.execute(
        "SELECT password FROM users WHERE id=?", (session['user_id'],)
    ).fetchone()

    is_valid, _ = verify_password(user['password'], old_pw)
    if not is_valid:
        flash('كلمة المرور الحالية غير صحيحة', 'danger')
        return redirect(url_for('settings.index', tab='security'))

    new_hash = hash_password(new_pw)
    db.execute("UPDATE users SET password=? WHERE id=?", (new_hash, session['user_id']))
    db.commit()
    log_activity('تغيير كلمة المرور')
    flash('تم تغيير كلمة المرور بنجاح', 'success')
    return redirect(url_for('settings.index', tab='security'))


# ─── النسخ الاحتياطي ──────────────────────────────────────────────────────
@settings_bp.route('/backup', methods=['POST'])
@login_required
def backup():
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لعمل نسخ احتياطية', 'danger')
        return redirect(url_for('settings.index', tab='security'))

    db_path     = current_app.config['DATABASE']
    backup_dir  = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'data_backup_{timestamp}.db')
    shutil.copy2(db_path, backup_file)

    log_activity('نسخ احتياطي', f'الملف: data_backup_{timestamp}.db')
    flash(f'تم إنشاء النسخة الاحتياطية: data_backup_{timestamp}.db', 'success')
    return redirect(url_for('settings.index', tab='security'))


# ─── API: بيانات المستخدم للتعديل ────────────────────────────────────────
@settings_bp.route('/users/<int:uid>/data')
@login_required
def user_data(uid):
    db   = get_db()
    user = db.execute(
        "SELECT id, username, full_name, role FROM users WHERE id=?", (uid,)
    ).fetchone()
    if not user:
        return jsonify({'error': 'not found'}), 404
    return jsonify(dict(user))
