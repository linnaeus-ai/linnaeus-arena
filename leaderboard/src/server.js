import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { Database } from './sqlite.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const db = new Database(path.join(__dirname, '..', 'data', 'leaderboard.db'));

app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'public')));

// API routes
app.get('/api/leaderboard', async (req, res) => {
  try {
    const topic = (req.query.topic || 'overall').toString();
    const allowed = ['overall', 'text', 'translate', 'vision'];
    if (!allowed.includes(topic)) {
      return res.status(400).json({ error: 'Invalid topic' });
    }
    const rows = await db.getLeaderboard(topic);
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Fallback to index.html (single page)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

const port = process.env.PORT || 3000;
app.listen(port, async () => {
  await db.init();
  console.log(`Leaderboard running on http://localhost:${port}`);
});
