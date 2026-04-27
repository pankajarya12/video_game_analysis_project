-- ============================================================
-- SQLite schema for Video Game Sales & Engagement Analysis
-- Normalized design with PK/FK constraints
-- ============================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS platforms;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS publishers;

CREATE TABLE platforms (
    platform_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT UNIQUE NOT NULL
);

CREATE TABLE genres (
    genre_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name TEXT UNIQUE NOT NULL
);

CREATE TABLE publishers (
    publisher_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    publisher_name TEXT UNIQUE NOT NULL
);

-- games: master catalog (from games.csv)
CREATE TABLE games (
    game_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    platform_id    INTEGER REFERENCES platforms(platform_id),
    genre_id       INTEGER REFERENCES genres(genre_id),
    publisher_id   INTEGER REFERENCES publishers(publisher_id),
    release_year   INTEGER,
    user_score     REAL,
    critic_score   REAL,
    user_count     INTEGER,
    critic_count   INTEGER,
    rating         TEXT,
    developer      TEXT
);

-- sales: regional sales (from vgsales.csv)
CREATE TABLE sales (
    sale_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id      INTEGER REFERENCES games(game_id),
    name         TEXT NOT NULL,
    platform_id  INTEGER REFERENCES platforms(platform_id),
    genre_id     INTEGER REFERENCES genres(genre_id),
    publisher_id INTEGER REFERENCES publishers(publisher_id),
    release_year INTEGER,
    na_sales     REAL DEFAULT 0,
    eu_sales     REAL DEFAULT 0,
    jp_sales     REAL DEFAULT 0,
    other_sales  REAL DEFAULT 0,
    global_sales REAL DEFAULT 0
);

CREATE INDEX idx_games_name      ON games(name);
CREATE INDEX idx_sales_name      ON sales(name);
CREATE INDEX idx_sales_year      ON sales(release_year);
CREATE INDEX idx_sales_platform  ON sales(platform_id);
CREATE INDEX idx_sales_genre     ON sales(genre_id);
