# bot_manager.py
import os
import subprocess
import signal
import shutil
import json
from datetime import datetime
from database import BotDatabase

class BotManager:
    def __init__(self, bots_folder='bots'):
        self.bots_folder = bots_folder
        os.makedirs(bots_folder, exist_ok=True)
        self.db = BotDatabase()
        self.pids_file = os.path.join(bots_folder, 'bot_pids.json')

        if not os.path.exists(self.pids_file):
            with open(self.pids_file, 'w') as f:
                json.dump({}, f)

    def get_pid(self, bot_id):
        """الحصول على PID من الملف"""
        with open(self.pids_file, 'r') as f:
            pids = json.load(f)
        return pids.get(str(bot_id))

    def save_pid(self, bot_id, pid):
        """حفظ PID في الملف"""
        with open(self.pids_file, 'r') as f:
            pids = json.load(f)

        pids[str(bot_id)] = pid

        with open(self.pids_file, 'w') as f:
            json.dump(pids, f)

    def remove_pid(self, bot_id):
        """حذف PID من الملف"""
        with open(self.pids_file, 'r') as f:
            pids = json.load(f)

        if str(bot_id) in pids:
            del pids[str(bot_id)]

        with open(self.pids_file, 'w') as f:
            json.dump(pids, f)

    def prepare_bot_folder(self, repo_id, bot_id):
        """تجهيز مجلد البوت من المستودع"""
        # الحصول على المستودع
        repo = self.db.get_repository(repo_id)
        if not repo:
            return None, "المستودع غير موجود"

        # الحصول على ملفات المستودع
        repo_files = self.db.get_repo_files(repo_id)
        if not repo_files:
            return None, "لا توجد ملفات في المستودع"

        # إنشاء مجلد للبوت
        bot_folder = f"bot_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        bot_path = os.path.join(self.bots_folder, bot_folder)
        os.makedirs(bot_path, exist_ok=True)

        # نسخ الملفات
        for file in repo_files:
            file_path = os.path.join(bot_path, file[2])  # filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file[3])  # content

        return bot_folder, None

    def start_bot(self, bot_id, repo_id, main_file, requirements_file=None):
        """تشغيل البوت"""
        bot = self.db.get_bot(bot_id)
        if not bot:
            return False, "البوت غير موجود"

        # تجهيز مجلد البوت
        bot_folder, error = self.prepare_bot_folder(repo_id, bot_id)
        if error:
            return False, error

        bot_path = os.path.join(self.bots_folder, bot_folder)
        main_path = os.path.join(bot_path, main_file)

        if not os.path.exists(main_path):
            return False, f"الملف الرئيسي {main_file} غير موجود"

        try:
            # تثبيت المتطلبات إذا وجدت
            if requirements_file:
                req_path = os.path.join(bot_path, requirements_file)
                if os.path.exists(req_path):
                    subprocess.run(
                        ['pip', 'install', '-r', requirements_file],
                        cwd=bot_path,
                        capture_output=True,
                        text=True
                    )

            # تشغيل البوت
            process = subprocess.Popen(
                ['python', main_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=bot_path
            )

            # حفظ PID
            self.save_pid(bot_id, process.pid)

            # تحديث حالة البوت في قاعدة البيانات
            self.db.update_bot_status(bot_id, 'running', process.pid)

            return True, f"تم تشغيل البوت بنجاح (PID: {process.pid})"

        except Exception as e:
            return False, f"خطأ: {str(e)}"

    def stop_bot(self, bot_id):
        """إيقاف البوت"""
        pid = self.get_pid(bot_id)

        if not pid:
            return False, "البوت ليس قيد التشغيل"

        try:
            os.kill(pid, signal.SIGTERM)
            self.remove_pid(bot_id)
            self.db.update_bot_status(bot_id, 'stopped')
            return True, "تم إيقاف البوت"
        except ProcessLookupError:
            self.remove_pid(bot_id)
            self.db.update_bot_status(bot_id, 'stopped')
            return True, "البوت كان متوقفاً بالفعل"
        except Exception as e:
            return False, f"خطأ: {str(e)}"

    def restart_bot(self, bot_id):
        """إعادة تشغيل البوت"""
        bot = self.db.get_bot(bot_id)
        if not bot:
            return False, "البوت غير موجود"

        # إيقاف أولاً
        self.stop_bot(bot_id)

        # ثم تشغيل
        return self.start_bot(bot_id, bot[1], bot[3], bot[4])

    def delete_bot(self, bot_id):
        """حذف البوت بالكامل"""
        bot = self.db.get_bot(bot_id)
        if not bot:
            return False, "البوت غير موجود"

        # إيقاف البوت
        self.stop_bot(bot_id)

        # حذف من قاعدة البيانات
        self.db.delete_bot(bot_id)

        return True, "تم حذف البوت"