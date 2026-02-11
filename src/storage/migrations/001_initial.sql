-- Initial database schema for MafiaAI

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    phase TEXT NOT NULL DEFAULT 'lobby',
    round_number INTEGER NOT NULL DEFAULT 0,
    winner TEXT,
    role_map_json TEXT NOT NULL DEFAULT '{}',
    state_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS game_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    round_number INTEGER NOT NULL,
    phase TEXT NOT NULL,
    eliminated TEXT,
    eliminated_role TEXT,
    votes_json TEXT NOT NULL DEFAULT '{}',
    night_kill TEXT,
    detective_target TEXT,
    detective_result INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bets (
    bet_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    bettor_id TEXT NOT NULL,
    bet_type TEXT NOT NULL,
    target TEXT NOT NULL,
    amount REAL NOT NULL,
    round_placed INTEGER NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    settled INTEGER NOT NULL DEFAULT 0,
    payout REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS spectators (
    session_id TEXT PRIMARY KEY,
    chips REAL NOT NULL DEFAULT 1000,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
