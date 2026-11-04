import json
import sqlite3
from pathlib import Path

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY, body TEXT NOT NULL)')

    def save(self, plan):
        with sqlite3.connect(self.path) as connection:
            connection.execute('INSERT INTO plans VALUES (?, ?)', (plan['id'], json.dumps(plan)))

    def get(self, plan_id):
        with sqlite3.connect(self.path) as connection:
            row = connection.execute('SELECT body FROM plans WHERE id=?', (plan_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self):
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute('SELECT body FROM plans ORDER BY rowid DESC LIMIT 100').fetchall()
        return [json.loads(row[0]) for row in rows]
