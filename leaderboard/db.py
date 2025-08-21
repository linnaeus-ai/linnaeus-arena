import os
import sqlite3
from datetime import datetime
from contextlib import closing

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        first_run = not os.path.exists(self.db_path)
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.executescript(
                '''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS models (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  org TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS scores (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  model_id INTEGER NOT NULL,
                  text REAL NOT NULL,
                  translate REAL NOT NULL,
                  vision REAL NOT NULL,
                  overall REAL NOT NULL,
                  updated_at TEXT NOT NULL,
                  FOREIGN KEY(model_id) REFERENCES models(id)
                );
                '''
            )
            conn.commit()
        if first_run:
            self.seed()

    def seed(self):
        now = datetime.utcnow().isoformat()
        models = [
            { 'name': 'GPT-4.1', 'org': 'OpenAI' },
            { 'name': 'GPT-4o', 'org': 'OpenAI' },
            { 'name': 'o3-mini', 'org': 'OpenAI' },
            { 'name': 'Claude 3.5 Sonnet', 'org': 'Anthropic' },
            { 'name': 'Claude 3.5 Haiku', 'org': 'Anthropic' },
            { 'name': 'Llama 3.1 405B', 'org': 'Meta' },
            { 'name': 'Llama 3.1 70B', 'org': 'Meta' },
            { 'name': 'Llama 3.1 8B', 'org': 'Meta' },
            { 'name': 'Qwen2.5-72B', 'org': 'Alibaba' },
            { 'name': 'Qwen2.5-7B', 'org': 'Alibaba' },
            { 'name': 'Mistral Large 2', 'org': 'Mistral AI' },
            { 'name': 'Mixtral 8x22B', 'org': 'Mistral AI' },
            { 'name': 'Phi-3.5-mini', 'org': 'Microsoft' },
            { 'name': 'Gemini 1.5 Pro', 'org': 'Google' },
            { 'name': 'Gemini 1.5 Flash', 'org': 'Google' },
        ]
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute('BEGIN')
            try:
                for m in models:
                    cur.execute('INSERT INTO models (name, org) VALUES (?, ?)', (m['name'], m['org']))
                    model_id = cur.lastrowid
                    text = round(80 + (20 * os.urandom(1)[0]/255), 1)
                    translate = round(75 + (25 * os.urandom(1)[0]/255), 1)
                    vision = round(70 + (30 * os.urandom(1)[0]/255), 1)
                    overall = round((text + translate + vision) / 3, 1)
                    cur.execute(
                        'INSERT INTO scores (model_id, text, translate, vision, overall, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                        (model_id, text, translate, vision, overall, now)
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def get_leaderboard(self, topic: str):
        order_map = {
            'overall': 's.overall DESC, s.text DESC, s.translate DESC, s.vision DESC, m.name ASC',
            'text': 's.text DESC, s.overall DESC, s.translate DESC, s.vision DESC, m.name ASC',
            'translate': 's.translate DESC, s.overall DESC, s.text DESC, s.vision DESC, m.name ASC',
            'vision': 's.vision DESC, s.overall DESC, s.text DESC, s.translate DESC, m.name ASC',
        }
        topic_key = topic if topic in order_map else 'overall'
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            sql = (
                'SELECT m.name as model, m.org, s.text, s.translate, s.vision, s.overall, s.updated_at '
                'FROM models m JOIN scores s ON m.id = s.model_id '
                f'ORDER BY {order_map[topic_key]}'
            )
            rows = cur.execute(sql).fetchall()
            result = []
            for idx, r in enumerate(rows, start=1):
                result.append({
                    'rank': idx,
                    'model': r['model'],
                    'org': r['org'],
                    'text': float(r['text']),
                    'translate': float(r['translate']),
                    'vision': float(r['vision']),
                    'overall': float(r['overall']),
                    'updated_at': r['updated_at'],
                })
            return result
