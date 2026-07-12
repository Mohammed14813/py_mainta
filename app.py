# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from flask_socketio import SocketIO, emit
from datetime import datetime
import json

from config import Config
from database import BotDatabase
from auth import init_oauth, login_required, admin_required, oauth
from repo_manager import RepoManager
from bot_manager import BotManager
from terminal_manager import TerminalManager

# ===================== تهيئة التطبيق =====================
app = Flask(__name__)
app.config.from_object(Config)

# تهيئة الجلسة
Session(app)

# تهيئة SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# تهيئة OAuth
init_oauth(app)

# ===================== تهيئة المديرين =====================
db = BotDatabase()
repo_manager = RepoManager()
bot_manager = BotManager()
terminal_manager = TerminalManager()

# ===================== الصفحة الرئيسية =====================
@app.route('/')
def home():
    if 'user_email' not in session:
        return redirect('/login')
    return render_template('home.html', admin_email=Config.ADMIN_EMAIL)

# ===================== تسجيل الدخول =====================
@app.route('/login')
def login():
    if 'user_email' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/google_login')
def google_login():
    return oauth.google.authorize_redirect(url_for('google_callback'))

@app.route('/google_callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)

    email = user_info.get('email')
    name = user_info.get('name')

    if email == Config.ADMIN_EMAIL:
        session['user_email'] = email
        session['user_name'] = name
        session.permanent = True
        flash('✅ تم تسجيل الدخول بنجاح!', 'success')
        return redirect('/')
    else:
        flash('❌ غير مصرح لك بالدخول', 'error')
        return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect('/')

# ===================== إضافة مستودع =====================
@app.route('/add_repo', methods=['GET', 'POST'])
@login_required
@admin_required
def add_repo():
    if request.method == 'POST':
        repo_name = request.form.get('repo_name')

        if not repo_name:
            flash('❌ الرجاء إدخال اسم المستودع', 'error')
            return redirect('/add_repo')

        # حفظ المستودع في قاعدة البيانات
        repo_id = db.add_repository(repo_name, session['user_email'])

        # إنشاء مجلد المستودع
        repo_manager.create_repo_folder(repo_id, repo_name)

        # الطريقة 1: رفع ملفات
        uploaded_files = request.files.getlist('files')

        if uploaded_files and uploaded_files[0].filename != '':
            files_data = []
            for file in uploaded_files:
                if file.filename:
                    content = file.read().decode('utf-8')
                    db.add_file(repo_id, file.filename, content)
                    files_data.append({
                        'filename': file.filename,
                        'content': content
                    })

            # حفظ على القرص
            repo_manager.save_files_to_disk(repo_id, files_data)

        # الطريقة 2: كتابة يدوية
        manual_files = request.form.getlist('manual_files[]')
        manual_contents = request.form.getlist('manual_contents[]')

        for i in range(len(manual_files)):
            if manual_files[i] and manual_contents[i]:
                db.add_file(repo_id, manual_files[i], manual_contents[i])

        # حفظ الملفات اليدوية على القرص
        repo_manager.save_files_to_disk(repo_id, db.get_repo_files(repo_id))

        flash(f'✅ تم إنشاء المستودع "{repo_name}" بنجاح!', 'success')
        return redirect('/repositories')

    return render_template('add_repo.html')

# ===================== مستودعاتي =====================
@app.route('/repositories')
@login_required
@admin_required
def repositories():
    repos = db.get_all_repositories()
    return render_template('repositories.html', repos=repos)

@app.route('/repo/<int:repo_id>')
@login_required
@admin_required
def repo_files(repo_id):
    repo = db.get_repository(repo_id)
    if not repo:
        flash('❌ المستودع غير موجود', 'error')
        return redirect('/repositories')

    files = db.get_repo_files(repo_id)
    return render_template('repo_files.html', repo=repo, files=files)

# ===================== تعديل الملف =====================
@app.route('/edit_file/<int:repo_id>/<filename>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_file(repo_id, filename):
    if request.method == 'POST':
        content = request.form.get('content')

        if content is not None:
            db.update_file_content(repo_id, filename, content)
            repo_manager.update_file_on_disk(repo_id, filename, content)
            flash(f'✅ تم حفظ {filename} بنجاح', 'success')
            return redirect(f'/repo/{repo_id}')

    file_data = db.get_file(repo_id, filename)
    if not file_data:
        flash('❌ الملف غير موجود', 'error')
        return redirect(f'/repo/{repo_id}')

    return render_template('edit_file.html',
                         repo_id=repo_id,
                         filename=filename,
                         content=file_data[3])

@app.route('/delete_file/<int:repo_id>/<filename>')
@login_required
@admin_required
def delete_file(repo_id, filename):
    db.delete_file(repo_id, filename)
    repo_manager.delete_file_from_disk(repo_id, filename)
    flash(f'✅ تم حذف {filename}', 'success')
    return redirect(f'/repo/{repo_id}')

# ===================== تشغيل بوت =====================
@app.route('/run_bot', methods=['GET', 'POST'])
@login_required
@admin_required
def run_bot():
    if request.method == 'POST':
        repo_id = request.form.get('repo_id')
        main_file = request.form.get('main_file')
        requirements_file = request.form.get('requirements_file')

        if not repo_id or not main_file:
            flash('❌ الرجاء اختيار المستودع وملف التشغيل', 'error')
            return redirect('/run_bot')

        repo = db.get_repository(int(repo_id))
        if not repo:
            flash('❌ المستودع غير موجود', 'error')
            return redirect('/run_bot')

        # إنشاء بوت جديد
        bot_id = db.add_bot(
            int(repo_id),
            repo[1],
            main_file,
            requirements_file
        )

        # تشغيل البوت
        success, message = bot_manager.start_bot(
            bot_id,
            int(repo_id),
            main_file,
            requirements_file
        )

        if success:
            flash(f'✅ {message}', 'success')
            return redirect(f'/terminal/{bot_id}')
        else:
            db.update_bot_status(bot_id, 'error')
            flash(f'❌ {message}', 'error')
            return render_template('error_terminal.html',
                                 bot_id=bot_id,
                                 error=message,
                                 main_file=main_file,
                                 requirements_file=requirements_file)

    repos = db.get_all_repositories()
    return render_template('run_bot.html', repos=repos)

# ===================== بوتاتي =====================
@app.route('/my_bots')
@login_required
@admin_required
def my_bots():
    bots = db.get_all_bots()
    return render_template('my_bots.html', bots=bots)

@app.route('/stop_bot/<int:bot_id>')
@login_required
@admin_required
def stop_bot(bot_id):
    success, message = bot_manager.stop_bot(bot_id)
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'error')
    return redirect('/my_bots')

@app.route('/restart_bot/<int:bot_id>')
@login_required
@admin_required
def restart_bot(bot_id):
    success, message = bot_manager.restart_bot(bot_id)
    if success:
        flash(f'✅ {message}', 'success')
        return redirect(f'/terminal/{bot_id}')
    else:
        flash(f'❌ {message}', 'error')
        return redirect('/my_bots')

@app.route('/delete_bot/<int:bot_id>')
@login_required
@admin_required
def delete_bot(bot_id):
    success, message = bot_manager.delete_bot(bot_id)
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'error')
    return redirect('/my_bots')

# ===================== الشاشة السوداء (Terminal) =====================
@app.route('/terminal/<int:bot_id>')
@login_required
@admin_required
def terminal(bot_id):
    bot = db.get_bot(bot_id)
    if not bot:
        flash('❌ البوت غير موجود', 'error')
        return redirect('/my_bots')

    repo = db.get_repository(bot[1])
    return render_template('terminal.html',
                         bot=bot,
                         repo=repo,
                         bot_id=bot_id)

# ===================== WebSocket للشاشة السوداء =====================
@socketio.on('connect')
def handle_connect():
    """اتصال WebSocket"""
    emit('terminal_output', {
        'message': '🟢 متصل بالمحطة',
        'type': 'success'
    })

@socketio.on('start_bot_terminal')
def handle_start_bot_terminal(data):
    """تشغيل البوت من الشاشة السوداء"""
    bot_id = data.get('bot_id')
    socket_id = request.sid

    terminal_manager.start_bot_session(bot_id, socket_id)

@socketio.on('stop_bot_terminal')
def handle_stop_bot_terminal(data):
    """إيقاف البوت من الشاشة السوداء"""
    bot_id = data.get('bot_id')
    success, message = terminal_manager.stop_bot_session(bot_id)

    emit('terminal_output', {
        'message': f'⏹ {message}',
        'type': 'success' if success else 'error'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """قطع الاتصال"""
    emit('terminal_output', {
        'message': '🔴 تم قطع الاتصال',
        'type': 'error'
    })

# ===================== تشغيل التطبيق =====================
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)