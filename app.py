"""
نظام إدارة عيادة الأسنان
Dental Clinic Management System
Main Application Entry Point
"""

from flask import Flask, redirect, url_for, request, session, flash
from flask_session import Session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix
import os

from db.database import init_db
from routes.auth import auth_bp
from routes.patients import patients_bp
from routes.finance import finance_bp
from routes.medical import medical_bp
from routes.dashboard import dashboard_bp
from routes.settings import settings_bp
from routes.reports import reports_bp

from datetime import date as _date


csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    env_name = os.environ.get('FLASK_ENV', '').lower() or os.environ.get('APP_ENV', '').lower()
    is_production = env_name == 'production'

    # ─── إعدادات التطبيق ─────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dental-clinic-secret-2024-xK9mP')
    app.config['DEBUG'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('SESSION_LIFETIME_SECONDS', '43200'))
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get(
        'SESSION_COOKIE_SECURE',
        '1' if is_production else '0'
    ) == '1'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PREFERRED_URL_SCHEME'] = 'https' if is_production else 'http'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    # In reverse-proxy deployments, strict SSL referrer checks can fail if
    # upstream/proxy normalization differs between hostnames.
    app.config['WTF_CSRF_SSL_STRICT'] = os.environ.get('WTF_CSRF_SSL_STRICT', '0') == '1'
    app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'data.db')
    app.config['TEMPLATES_AUTO_RELOAD'] = False

    # ─── تهيئة الـ Session ────────────────────────────────────────
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    Session(app)
    csrf.init_app(app)

    # ─── تهيئة قاعدة البيانات ─────────────────────────────────────
    with app.app_context():
        init_db(app)

    # ─── تسجيل الـ Blueprints ─────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(medical_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(reports_bp)

    @app.before_request
    def enforce_role_permissions():
        """تقييد الصلاحيات حسب الدور"""
        if 'user_id' not in session:
            return None

        endpoint = request.endpoint or ''
        role = session.get('role')

        # المدير لديه صلاحية كاملة
        if role == 'admin':
            return None

        # الموظف العام: مسموح بكل شيء عدا التقارير
        if role == 'staff':
            if endpoint.startswith('reports.'):
                flash('التقارير متاحة للمدير فقط', 'warning')
                return redirect(url_for('dashboard.index'))
            return None

        # السماح بالملفات الثابتة وصفحات المصادقة العامة
        if endpoint.startswith('static') or endpoint in {'auth.logout', 'auth.login', 'auth.welcome'}:
            return None

        role_rules = {
            'accountant': {
                'allowed_prefixes': {'finance.', 'patients.'},
                'allowed_exact_get': set(),
                'allowed_exact_post': set(),
                'redirect_to': 'finance.index',
                'message': 'صلاحية المحاسب: المالية والأقساط + إدارة المرضى',
            },
            'doctor': {
                'allowed_prefixes': {'patients.', 'medical.'},
                'allowed_exact_get': set(),
                'allowed_exact_post': set(),
                'redirect_to': 'medical.prescription_form',
                'message': 'صلاحية الطبيب: الوصفة الطبية + المرضى فقط',
            },
            'reception': {
                'allowed_prefixes': {'patients.'},
                'allowed_exact_get': set(),
                'allowed_exact_post': set(),
                'redirect_to': 'patients.index',
                'message': 'صلاحية الاستقبال: المرضى فقط',
            },
        }

        rule = role_rules.get(role)
        if not rule:
            return None

        if any(endpoint.startswith(prefix) for prefix in rule['allowed_prefixes']):
            return None

        if endpoint in rule['allowed_exact_get'] and request.method == 'GET':
            return None

        if endpoint in rule['allowed_exact_post'] and request.method == 'POST':
            return None

        flash(rule['message'], 'warning')
        return redirect(url_for(rule['redirect_to']))

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_err):
        flash('انتهت صلاحية الجلسة أو فشل التحقق الأمني. أعد المحاولة.', 'error')
        return redirect(url_for('auth.welcome'))

    # ─── Jinja2 Filters ───────────────────────────────────────────
    @app.template_filter('ordinal_ar')
    def ordinal_ar(n):
        """Convert payment number to Arabic ordinal: 1→الأولى, 2→الثانية…"""
        words = {
            1: 'الأولى', 2: 'الثانية', 3: 'الثالثة', 4: 'الرابعة',
            5: 'الخامسة', 6: 'السادسة', 7: 'السابعة', 8: 'الثامنة',
            9: 'التاسعة', 10: 'العاشرة'
        }
        try:
            n = int(n)
            return words.get(n, f'رقم {n}')
        except (TypeError, ValueError):
            return n

    @app.template_filter('fmt_num')
    def fmt_num(value):
        """Format number with commas: 300000 → 300,000"""
        try:
            v = float(value)
            if v == int(v):
                return f"{int(v):,}"
            return f"{v:,.2f}"
        except (TypeError, ValueError):
            return value

    @app.template_filter('status_label')
    def status_label(status):
        labels = {
            'scheduled': 'مجدول',
            'completed': 'مكتمل',
            'cancelled': 'ملغي',
            'no_show':   'لم يحضر',
        }
        return labels.get(status, status)

    @app.template_filter('payment_label')
    def payment_label(method):
        labels = {
            'cash':     'نقدي',
            'card':     'بطاقة',
            'transfer': 'تحويل بنكي',
        }
        return labels.get(method, method)

    @app.template_filter('calc_age')
    def calc_age(value):
        """يحسب العمر من سنة الميلاد أو يعيد الرقم مباشرة إن كان عمراً"""
        try:
            v = int(str(value).strip())
            if v > 1000:  # سنة ميلاد
                age = _date.today().year - v
                return f'{age} سنة'
            else:  # عمر مباشر
                return f'{v} سنة'
        except:
            return '—'

    @app.template_filter('fmt12h')
    def fmt12h(t):
        """تحويل الوقت 24 ساعة إلى 12 ساعة بالعربية (08:30 → 8:30 ص)"""
        try:
            parts = str(t).split(':')
            h, m = int(parts[0]), parts[1]
            suffix = 'ص' if h < 12 else 'م'
            h12 = h % 12 or 12
            return f'{h12}:{m} {suffix}'
        except:
            return t

    # ─── Context Processors ───────────────────────────────────────
    @app.context_processor
    def inject_globals():
        return {'now_date': _date.today().isoformat()}

    @app.context_processor
    def inject_notifications():
        return {'notifications': [], 'notif_count': 0}

    # ─── الصفحة الرئيسية ──────────────────────────────────────────
    @app.route('/')
    def index():
        return redirect(url_for('auth.welcome'))

    return app


# Expose a module-level WSGI app so Gunicorn can run with app:app.
app = create_app()


if __name__ == '__main__':
    from waitress import serve
    print("Starting server on http://127.0.0.1:8080")
    serve(app, host='0.0.0.0', port=8080, threads=8)
