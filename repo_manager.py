# repo_manager.py
import os
import shutil
from datetime import datetime
from database import BotDatabase

class RepoManager:
    def __init__(self, repos_folder='repositories'):
        self.repos_folder = repos_folder
        os.makedirs(repos_folder, exist_ok=True)
        self.db = BotDatabase()

    def create_repo_folder(self, repo_id, repo_name):
        """إنشاء مجلد للمستودع على القرص"""
        folder_name = f"repo_{repo_id}_{repo_name.replace(' ', '_')}"
        repo_path = os.path.join(self.repos_folder, folder_name)
        os.makedirs(repo_path, exist_ok=True)
        return repo_path

    def save_files_to_disk(self, repo_id, files_data):
        """حفظ الملفات على القرص"""
        repo = self.db.get_repository(repo_id)
        if not repo:
            return False, "المستودع غير موجود"

        folder_name = f"repo_{repo_id}_{repo[1].replace(' ', '_')}"
        repo_path = os.path.join(self.repos_folder, folder_name)
        os.makedirs(repo_path, exist_ok=True)

        for file_data in files_data:
            filename = file_data.get('filename')
            content = file_data.get('content', '')
            file_path = os.path.join(repo_path, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return True, "تم حفظ الملفات بنجاح"

    def get_repo_files_from_disk(self, repo_id):
        """قراءة الملفات من القرص"""
        repo = self.db.get_repository(repo_id)
        if not repo:
            return []

        folder_name = f"repo_{repo_id}_{repo[1].replace(' ', '_')}"
        repo_path = os.path.join(self.repos_folder, folder_name)

        if not os.path.exists(repo_path):
            return []

        files = []
        for filename in os.listdir(repo_path):
            file_path = os.path.join(repo_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                files.append({
                    'filename': filename,
                    'content': content,
                    'size': os.path.getsize(file_path)
                })

        return files

    def update_file_on_disk(self, repo_id, filename, content):
        """تعديل ملف على القرص"""
        repo = self.db.get_repository(repo_id)
        if not repo:
            return False, "المستودع غير موجود"

        folder_name = f"repo_{repo_id}_{repo[1].replace(' ', '_')}"
        repo_path = os.path.join(self.repos_folder, folder_name)
        file_path = os.path.join(repo_path, filename)

        if not os.path.exists(file_path):
            return False, "الملف غير موجود"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, "تم تعديل الملف بنجاح"

    def delete_file_from_disk(self, repo_id, filename):
        """حذف ملف من القرص"""
        repo = self.db.get_repository(repo_id)
        if not repo:
            return False, "المستودع غير موجود"

        folder_name = f"repo_{repo_id}_{repo[1].replace(' ', '_')}"
        repo_path = os.path.join(self.repos_folder, folder_name)
        file_path = os.path.join(repo_path, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return True, "تم حذف الملف"
        return False, "الملف غير موجود"

    def delete_repo_from_disk(self, repo_id):
        """حذف مجلد المستودع بالكامل"""
        repo = self.db.get_repository(repo_id)
        if not repo:
            return False, "المستودع غير موجود"

        folder_name = f"repo_{repo_id}_{repo[1].replace(' ', '_')}"
        repo_path = os.path.join(self.repos_folder, folder_name)

        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            return True, "تم حذف المستودع"
        return False, "المستودع غير موجود على القرص"