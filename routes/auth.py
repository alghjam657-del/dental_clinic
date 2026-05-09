"""
مسارات المصادقة - Authentication Routes
تسجيل الدخول والخروج
"""

import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db.database import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _role_home(role):
    """تحديد الصفحة الرئيسية حسب دور المستخدم"""
    if role == 'accountant':
        return 'finance.index'
    if role == 'doctor':
        return 'medical.prescription_form'
    if role == 'reception':
        return 'patients.index'
    return 'dashboard.index'


def login_required(f):
    """Decorator للتحقق من تسجيل الدخول"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if 'user_id' in session:
        return redirect(url_for(_role_home(session.get('role'))))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'error')
            return render_template('login.html')

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password_hash)
        ).fetchone()

        if user:
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['full_name'] = user['full_name']
            session['role']      = user['role']
            return redirect(url_for(_role_home(user['role'])))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')

    return render_template('login.html')


@auth_bp.route('/welcome', methods=['GET'])
def welcome():
    """واجهة الترحيب (تعرض صفحة الدخول دائماً)"""
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('auth.login'))
