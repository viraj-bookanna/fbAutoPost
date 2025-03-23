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
            post_link TEXT,
            group_list TEXT,
            share_text TEXT
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
    def delete_cron(self, job_id):
        deleted = False
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM cron WHERE id = ?", (job_id,))
        if cursor.rowcount > 0:
            deleted = True
        cursor.close()
        self.conn.commit()
        return deleted
    def delete_job(self, job_id):
        deleted = False
        self.delete_cron(job_id)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        if cursor.rowcount > 0:
            deleted = True
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
        for execution_time in self.get_all_mins(crontab_expression):
            cursor.execute("INSERT INTO cron (id, execution_time) VALUES (?, ?)", (job_id, execution_time))
        cursor.close()
        self.conn.commit()
        return True
    def get_jobs_for_current_minute(self):
        now = datetime.now(self.timezone)
        minutes_passed = now.minute + now.hour * 60
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cron JOIN jobs ON cron.id = jobs.id WHERE execution_time = ?", (minutes_passed,))
        job = cursor.fetchone()
        while job:
            yield {
                'post_link': job[3],
                'group_list': json.loads(job[4]),
                'share_text': job[5]
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