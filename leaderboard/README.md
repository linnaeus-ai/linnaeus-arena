# Linnaeus Leaderboard (local)

Single-page app with a SQLite-backed leaderboard across topics: Overall, Text, Translate, Vision.

Features
- Rijksstijl-inspired header and tabs
- Single page with tabs
- Columns: Rank, Model, Org, Text, Translate, Vision, Overall, Last Updated
- Client-side sorting and search
- SQLite auto-created and seeded with 15 well-known models on first run

Run with Python (recommended)
- Requires Python 3.10+

Setup (Windows PowerShell)
```powershell
cd c:\Apps\Linnaeus
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://localhost:3000

Optional: Run with Node (requires Node.js LTS)
```powershell
cd c:\Apps\Linnaeus
npm install
npm start
```

Notes
- The database is stored at `data/leaderboard.db`. Delete it to reseed on next start.
- API: `GET /api/leaderboard?topic=overall|text|translate|vision`
