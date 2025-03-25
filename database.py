import sqlite3, json, pytz
from croniter import croniter
from datetime import datetime, timedelta

class DB:
    def __init__(self):
        self.timezone = pytz.timezone('Asia/Colombo')
        self.conn = sqlite3.connect('database.db')
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_link TEXT NOT NULL,
            group_list TEXT NOT NULL,
            share_text TEXT,
            cron_active BOOLEAN DEFAULT 0,
            cron_expression TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cron (
            id INTEGER,
            execution_time INTEGER
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            data TEXT
        )''')
        cursor.close()
        self.conn.commit()
    def set_timezone(self, timezone):
        self.timezone = pytz.timezone(timezone)
    def add_job(self, job):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO jobs (post_link, group_list, share_text) VALUES (?, ?, ?)", (job['post_link'], job['group_list'], job['share_text']))
        job_id = cursor.lastrowid
        cursor.close()
        self.conn.commit()
        return job_id
    def get_active_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM jobs WHERE cron_active = 1")
        job = cursor.fetchone()
        while job:
            yield {'id': job[0]}
            job = cursor.fetchone()
        cursor.close()
    def get_job(self, job_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE cron_active = 1 AND id = ?", (job_id,))
        job = cursor.fetchone()
        cursor.close()
        if not job:
            return None
        return {
            'id': job[0],
            'post_link': job[1],
            'group_list': json.loads(job[2]),
            'share_text': job[3],
            'cron_expression': job[5]
        }
    def edit_job(self, job_id, field, value):
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE jobs SET {field} = ? WHERE id = ?", (value, job_id))
        updated = cursor.rowcount > 0
        cursor.close()
        return updated
    def delete_cron(self, job_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM cron WHERE id = ?", (job_id,))
        deleted = cursor.rowcount > 0
        if deleted:
            cursor.execute("UPDATE jobs SET cron_active = 0, cron_expression = NULL WHERE id = ?", (job_id,))
        cursor.close()
        self.conn.commit()
        return deleted
    def delete_job(self, job_id):
        self.delete_cron(job_id)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        deleted = cursor.rowcount > 0
        cursor.close()
        self.conn.commit()
        return deleted
    def get_all_mins(self, crontab_expression):
        date = datetime.now(self.timezone).date()
        start_time = self.timezone.localize(datetime.combine(date, datetime.min.time()))
        end_time = start_time + timedelta(days=1)
        cron = croniter(crontab_expression, start_time)
        matching_times = []
        if croniter.match(crontab_expression, start_time):
            matching_times.append(start_time.hour * 60 + start_time.minute)
        while True:
            next_time = cron.get_next(datetime)
            if next_time >= end_time:
                break
            matching_times.append(next_time.hour * 60 + next_time.minute)
        return matching_times
    def add_cron(self, job_id, crontab_expression):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM jobs WHERE id = ?", (job_id,))
        if not cursor.fetchone():
            return False
        self.delete_cron(job_id)
        cursor.execute("UPDATE jobs SET cron_active = 1, cron_expression = ? WHERE id = ?", (crontab_expression, job_id))
        for execution_time in self.get_all_mins(crontab_expression):
            cursor.execute("INSERT INTO cron (id, execution_time) VALUES (?, ?)", (job_id, execution_time))
        cursor.close()
        self.conn.commit()
        return True
    def get_jobs_for_current_minute(self):
        now = datetime.now(self.timezone)
        minutes_passed = now.minute + now.hour * 60
        cursor = self.conn.cursor()
        cursor.execute("SELECT jobs.post_link,jobs.group_list,jobs.share_text FROM cron JOIN jobs ON cron.id = jobs.id WHERE execution_time = ?", (minutes_passed,))
        job = cursor.fetchone()
        while job:
            yield {
                'post_link': job[0],
                'group_list': json.loads(job[1]),
                'share_text': job[2]
            }
            job = cursor.fetchone()
        cursor.close()
    def set_user(self, chat_id, data):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (chat_id, data) VALUES (?, ?)", (chat_id, json.dumps(data)))
        cursor.close()
        self.conn.commit()
    def get_user(self, chat_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM users WHERE chat_id = ?", (chat_id,))
        data = cursor.fetchone()
        cursor.close()
        return None if not data else json.loads(data[0])