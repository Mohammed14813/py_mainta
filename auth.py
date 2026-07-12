# auth.py
from flask import session, redirect, url_for, flash, request
from functools import wraps
from authlib.integrations.flask_client import OAuth
from config import Config

oauth = OAuth()

def init_oauth(app):
    """تهيئة OAuth مع Google"""
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

def login_required(f):
    """تأكد من أن المستخدم مسجل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('الرجاء تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """تأكد من أن المستخدم هو المدير"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_email') != Config.ADMIN_EMAIL:
            flash('غير مصرح لك بالدخول', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function