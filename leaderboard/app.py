from flask import Flask, jsonify, send_from_directory, request
import os
from db import Database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'leaderboard.db')

app = Flask(__name__, static_folder='public', static_url_path='')
db = Database(DB_PATH)

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.get('/api/leaderboard')
def api_leaderboard():
    topic = (request.args.get('topic') or 'overall').lower()
    allowed = {'overall', 'text', 'translate', 'vision'}
    if topic not in allowed:
        return jsonify({'error': 'Invalid topic'}), 400
    rows = db.get_leaderboard(topic)
    return jsonify(rows)

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    # Warm up DB on startup for CLI runs
    db.init()
    port = int(os.environ.get('PORT', '3000'))
    app.run(host='127.0.0.1', port=port)
