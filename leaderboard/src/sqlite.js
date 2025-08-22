import fs from 'fs';
import path from 'path';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

// Whitelisted ORDER BY clauses. Never construct identifiers from user input.
// Keep this immutable to avoid accidental mutation.
const ORDER_BY_MAP = Object.freeze({
  overall: 's.overall DESC, s.text DESC, s.translate DESC, s.vision DESC, m.name ASC',
  text: 's.text DESC, s.overall DESC, s.translate DESC, s.vision DESC, m.name ASC',
  translate: 's.translate DESC, s.overall DESC, s.text DESC, s.vision DESC, m.name ASC',
  vision: 's.vision DESC, s.overall DESC, s.text DESC, s.translate DESC, m.name ASC'
});

const ALLOWED_TOPICS = new Set(Object.keys(ORDER_BY_MAP));

export class Database {
  constructor(dbPath) {
    this.dbPath = dbPath;
    this.dir = path.dirname(dbPath);
  }

  async init() {
    if (!fs.existsSync(this.dir)) {
      fs.mkdirSync(this.dir, { recursive: true });
    }
    const firstRun = !fs.existsSync(this.dbPath);
    this.conn = await open({ filename: this.dbPath, driver: sqlite3.Database });
    await this.conn.exec(`
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
        FOREIGN KEY (model_id) REFERENCES models(id)
      );
    `);

    if (firstRun) {
      await this.seed();
    }
  }

  async seed() {
    const now = new Date().toISOString();
    const models = [
      { name: 'GPT-4.1', org: 'OpenAI' },
      { name: 'GPT-4o', org: 'OpenAI' },
      { name: 'o3-mini', org: 'OpenAI' },
      { name: 'Claude 3.5 Sonnet', org: 'Anthropic' },
      { name: 'Claude 3.5 Haiku', org: 'Anthropic' },
      { name: 'Llama 3.1 405B', org: 'Meta' },
      { name: 'Llama 3.1 70B', org: 'Meta' },
      { name: 'Llama 3.1 8B', org: 'Meta' },
      { name: 'Qwen2.5-72B', org: 'Alibaba' },
      { name: 'Qwen2.5-7B', org: 'Alibaba' },
      { name: 'Mistral Large 2', org: 'Mistral AI' },
      { name: 'Mixtral 8x22B', org: 'Mistral AI' },
      { name: 'Phi-3.5-mini', org: 'Microsoft' },
      { name: 'Gemini 1.5 Pro', org: 'Google' },
      { name: 'Gemini 1.5 Flash', org: 'Google' }
    ];

    await this.conn.exec('BEGIN');
    try {
      for (const m of models) {
        const { lastID } = await this.conn.run(
          'INSERT INTO models (name, org) VALUES (?, ?)',
          [m.name, m.org]
        );
        const text = +(80 + Math.random() * 20).toFixed(1);
        const translate = +(75 + Math.random() * 25).toFixed(1);
        const vision = +(70 + Math.random() * 30).toFixed(1);
        const overall = +(((text + translate + vision) / 3).toFixed(1));
        await this.conn.run(
          'INSERT INTO scores (model_id, text, translate, vision, overall, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
          [lastID, text, translate, vision, overall, now]
        );
      }
      await this.conn.exec('COMMIT');
    } catch (e) {
      await this.conn.exec('ROLLBACK');
      throw e;
    }
  }

  async getLeaderboard(topic) {
    // Validate topic against whitelist and choose a static ORDER BY clause.
    const key = ALLOWED_TOPICS.has(topic) ? topic : 'overall';
    const orderByClause = ORDER_BY_MAP[key];

    // Compose SQL by concatenating the chosen constant ORDER BY clause (no identifier/user input interpolation).
    const sql = [
      'SELECT m.name as model, m.org, s.text, s.translate, s.vision, s.overall, s.updated_at',
      'FROM models m JOIN scores s ON m.id = s.model_id',
      'ORDER BY ' + orderByClause
    ].join(' ');

    const rows = await this.conn.all(sql);

    // Add rank after sorting
    return rows.map((r, idx) => ({ rank: idx + 1, ...r }));
  }
}
