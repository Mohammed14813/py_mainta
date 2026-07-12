# database.py
import sqlite3
from datetime import datetime

class BotDatabase:
    def __init__(self, db_name='bots.db'):
        self.db_name = db_name
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # ===== جدول المستودعات =====
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT,
                admin_email TEXT
            )
        ''')

        # ===== جدول الملفات =====
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER,
                filename TEXT,
                content TEXT,
                FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
            )
        ''')

        # ===== جدول البوتات =====
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER,
                name TEXT,
                main_file TEXT,
                requirements_file TEXT,
                status TEXT DEFAULT 'stopped',
                pid INTEGER,
                created_at TEXT,
                FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    # ===================== المستودعات =====================
    def add_repository(self, name, admin_email):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO repositories (name, created_at, admin_email)
            VALUES (?, ?, ?)
        ''', (name, datetime.now().isoformat(), admin_email))
        repo_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return repo_id

    def get_all_repositories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM repositories ORDER BY id DESC')
        repos = cursor.fetchall()
        conn.close()
        return repos

    def get_repository(self, repo_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM repositories WHERE id = ?', (repo_id,))
        repo = cursor.fetchone()
        conn.close()
        return repo

    def delete_repository(self, repo_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM repositories WHERE id = ?', (repo_id,))
        conn.commit()
        conn.close()

    # ===================== الملفات =====================
    def add_file(self, repo_id, filename, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO files (repo_id, filename, content)
            VALUES (?, ?, ?)
        ''', (repo_id, filename, content))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id

    def get_repo_files(self, repo_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM files WHERE repo_id = ?', (repo_id,))
        files = cursor.fetchall()
        conn.close()
        return files

    def get_file(self, repo_id, filename):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM files WHERE repo_id = ? AND filename = ?
        ''', (repo_id, filename))
        file = cursor.fetchone()
        conn.close()
        return file

    def update_file_content(self, repo_id, filename, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE files SET content = ? WHERE repo_id = ? AND filename = ?
        ''', (content, repo_id, filename))
        conn.commit()
        conn.close()

    def delete_file(self, repo_id, filename):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM files WHERE repo_id = ? AND filename = ?
        ''', (repo_id, filename))
        conn.commit()
        conn.close()

    # ===================== البوتات =====================
    def add_bot(self, repo_id, name, main_file, requirements_file):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bots (repo_id, name, main_file, requirements_file, status, created_at)
            VALUES (?, ?, ?, ?, 'stopped', ?)
        ''', (repo_id, name, main_file, requirements_file, datetime.now().isoformat()))
        bot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bot_id

    def get_all_bots(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bots ORDER BY id DESC')
        bots = cursor.fetchall()
        conn.close()
        return bots

    def get_bot(self, bot_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bots WHERE id = ?', (bot_id,))
        bot = cursor.fetchone()
        conn.close()
        return bot

    def update_bot_status(self, bot_id, status, pid=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if pid is not None:
            cursor.execute('''
                UPDATE bots SET status = ?, pid = ? WHERE id = ?
            ''', (status, pid, bot_id))
        else:
            cursor.execute('''
                UPDATE bots SET status = ? WHERE id = ?
            ''', (status, bot_id))
        conn.commit()
        conn.close()

    def delete_bot(self, bot_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bots WHERE id = ?', (bot_id,))
        conn.commit()
        conn.close()