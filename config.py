# config.py
import os
from datetime import timedelta

class Config:
    # ========== إعدادات Flask ==========
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'py-mainta-secret-key-2024'
    
    # ========== إعدادات الجلسة ==========
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)  # 30 يوم
    
    # ========== Google OAuth ==========
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or 'your-google-client-id.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or 'your-google-client-secret'
    
    # ========== المدير ==========
    ADMIN_EMAIL = 'vgty65v@gmail.com'
    
    # ========== مجلدات التخزين ==========
    BOTS_FOLDER = 'bots'
    REPOSITORIES_FOLDER = 'repositories'
    
    # ========== قاعدة البيانات ==========
    DATABASE = 'bots.db'
    
    # ========== إعدادات الملفات ==========
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 ميجابايت
    ALLOWED_EXTENSIONS = {'py', 'txt', 'json', 'env', 'yml', 'yaml', 'md'}
    
    # ========== إعدادات Render ==========
    RENDER_API_KEY = os.environ.get('RENDER_API_KEY') or ''
    RENDER_SERVICE_ID = os.environ.get('RENDER_SERVICE_ID') or ''
    
    # ========== إعدادات WebSocket ==========
    WEBSOCKET_PORT = 5001