# terminal_manager.py
import subprocess
import threading
import os
from flask_socketio import emit
from database import BotDatabase
from bot_manager import BotManager

class TerminalManager:
    def __init__(self):
        self.db = BotDatabase()
        self.bot_manager = BotManager()
        self.active_sessions = {}

    def start_bot_session(self, bot_id, socket_id):
        bot = self.db.get_bot(bot_id)
        if not bot:
            emit('terminal_output', {
                'message': '❌ البوت غير موجود',
                'type': 'error'
            })
            return

        repo_id = bot[1]
        main_file = bot[3]
        requirements_file = bot[4]

        repo = self.db.get_repository(repo_id)
        if not repo:
            emit('terminal_output', {
                'message': '❌ المستودع غير موجود',
                'type': 'error'
            })
            return

        bot_folder, error = self.bot_manager.prepare_bot_folder(repo_id, bot_id)
        if error:
            emit('terminal_output', {
                'message': f'❌ {error}',
                'type': 'error'
            })
            return

        bot_path = os.path.join('bots', bot_folder)
        main_path = os.path.join(bot_path, main_file)

        if not os.path.exists(main_path):
            emit('terminal_output', {
                'message': f'❌ الملف الرئيسي {main_file} غير موجود',
                'type': 'error'
            })
            return

        def run_process():
            try:
                if requirements_file:
                    req_path = os.path.join(bot_path, requirements_file)
                    if os.path.exists(req_path):
                        emit('terminal_output', {
                            'message': f'📦 جاري تحميل المكتبات من {requirements_file}...',
                            'type': 'info'
                        })

                        process = subprocess.Popen(
                            ['pip', 'install', '-r', requirements_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            cwd=bot_path
                        )

                        for line in iter(process.stdout.readline, ''):
                            if line.strip():
                                emit('terminal_output', {
                                    'message': line.strip(),
                                    'type': 'output'
                                })

                        process.wait()

                        if process.returncode != 0:
                            emit('terminal_output', {
                                'message': '❌ فشل تحميل المكتبات',
                                'type': 'error'
                            })
                            return

                os.chmod(main_path, 0o755)

                emit('terminal_output', {
                    'message': f'🚀 جاري تشغيل {main_file}...',
                    'type': 'success'
                })

                process = subprocess.Popen(
                    ['python', main_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=bot_path
                )

                self.bot_manager.save_pid(bot_id, process.pid)
                self.db.update_bot_status(bot_id, 'running', process.pid)

                for line in iter(process.stdout.readline, ''):
                    if line.strip():
                        emit('terminal_output', {
                            'message': line.strip(),
                            'type': 'output'
                        })

                process.wait()

                if process.returncode == 0:
                    emit('terminal_output', {
                        'message': '✅ تم إيقاف البوت بنجاح',
                        'type': 'success'
                    })
                    self.db.update_bot_status(bot_id, 'stopped')
                else:
                    emit('terminal_output', {
                        'message': f'❌ توقف البوت برمز خطأ: {process.returncode}',
                        'type': 'error'
                    })
                    self.db.update_bot_status(bot_id, 'error')

            except Exception as e:
                emit('terminal_output', {
                    'message': f'❌ خطأ: {str(e)}',
                    'type': 'error'
                })

        thread = threading.Thread(target=run_process)
        thread.daemon = True
        thread.start()
        self.active_sessions[socket_id] = thread

    def stop_bot_session(self, bot_id):
        return self.bot_manager.stop_bot(bot_id)