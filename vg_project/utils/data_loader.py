"""
data_loader.py
--------------
Loads games.csv and vgsales.csv, cleans them, validates them,
and writes a normalized SQLite database (db/videogames.db).

Run:  python utils/data_loader.py
"""

import os
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

# ---- Paths (project-root relative) -------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "db" / "videogames.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


# ---- Helpers ----------------------------------------------------------------
def _read_csv_safe(path: Path) -> pd.DataFrame | None:
    """Read CSV with multiple encodings; return None if missing."""
    if not path.exists():
        return None
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", errors="ignore")


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    """snake_case all columns."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.replace(r"[^\w]+", "_", regex=True)
        .str.lower()
    )
    return df


def _make_synthetic():
    """Generate small synthetic data so the app runs without uploads."""
    rng = np.random.default_rng(42)
    platforms = ["PS4", "X360", "PC", "Wii", "PS3", "DS", "PS2", "XOne", "Switch"]
    genres = ["Action", "Sports", "Shooter", "RPG", "Racing", "Platform", "Misc",
              "Simulation", "Puzzle", "Adventure", "Fighting", "Strategy"]
    publishers = ["Nintendo", "EA", "Activision", "Sony", "Ubisoft", "Take-Two",
                  "Sega", "Capcom", "Square Enix", "Bandai Namco"]
    n = 600
    games = pd.DataFrame({
        "name": [f"Game {i}" for i in range(n)],
        "platform": rng.choice(platforms, n),
        "genre": rng.choice(genres, n),
        "publisher": rng.choice(publishers, n),
        "year_of_release": rng.integers(1995, 2020, n),
        "user_score": np.round(rng.uniform(3, 10, n), 1),
        "critic_score": np.round(rng.uniform(30, 100, n), 0),
        "user_count": rng.integers(5, 5000, n),
        "critic_count": rng.integers(3, 100, n),
        "rating": rng.choice(["E", "T", "M", "E10+"], n),
        "developer": rng.choice(publishers, n),
    })
    vg = games[["name", "platform", "year_of_release", "genre", "publisher"]].copy()
    vg["na_sales"] = np.round(rng.exponential(0.3, n), 2)
    vg["eu_sales"] = np.round(rng.exponential(0.25, n), 2)
    vg["jp_sales"] = np.round(rng.exponential(0.15, n), 2)
    vg["other_sales"] = np.round(rng.exponential(0.05, n), 2)
    vg["global_sales"] = (
        vg.na_sales + vg.eu_sales + vg.jp_sales + vg.other_sales
    ).round(2)
    return games, vg


def load_raw():
    """Load games.csv + vgsales.csv if present, else synthetic."""
    games = _read_csv_safe(DATA_DIR / "games.csv")
    vg = _read_csv_safe(DATA_DIR / "vgsales.csv")
    if games is None or vg is None:
        print("⚠️  CSV files not found in /data — generating synthetic sample.")
        games, vg = _make_synthetic()
    return _normalize_cols(games), _normalize_cols(vg)


def clean(games: pd.DataFrame, vg: pd.DataFrame):
    """Standard cleaning: rename, fix dtypes, drop hopeless rows."""
    # Standardize year column name
    for df in (games, vg):
        if "year_of_release" in df.columns:
            df.rename(columns={"year_of_release": "release_year"}, inplace=True)
        if "year" in df.columns and "release_year" not in df.columns:
            df.rename(columns={"year": "release_year"}, inplace=True)

    # Numeric coercion
    for col in ["user_score", "critic_score", "user_count", "critic_count",
                "release_year"]:
        if col in games.columns:
            games[col] = pd.to_numeric(games[col], errors="coerce")
    for col in ["na_sales", "eu_sales", "jp_sales", "other_sales",
                "global_sales", "release_year"]:
        if col in vg.columns:
            vg[col] = pd.to_numeric(vg[col], errors="coerce")

    # User score sometimes 0-100 in some sources → normalize to 0-10
    if "user_score" in games.columns and games["user_score"].max(skipna=True) > 10:
        games["user_score"] = games["user_score"] / 10.0

    # Drop rows missing the essentials
    games = games.dropna(subset=["name"])
    vg = vg.dropna(subset=["name"])

    # Fill text NAs
    for col in ["platform", "genre", "publisher", "rating", "developer"]:
        if col in games.columns:
            games[col] = games[col].fillna("Unknown").astype(str).str.strip()
        if col in vg.columns:
            vg[col] = vg[col].fillna("Unknown").astype(str).str.strip()

    # Numeric NA → 0 for sales
    for col in ["na_sales", "eu_sales", "jp_sales", "other_sales", "global_sales"]:
        if col in vg.columns:
            vg[col] = vg[col].fillna(0)

    # Recompute global_sales if obviously off
    if {"na_sales", "eu_sales", "jp_sales", "other_sales"}.issubset(vg.columns):
        vg["global_sales"] = (
            vg.na_sales + vg.eu_sales + vg.jp_sales + vg.other_sales
        ).round(2)

    return games, vg


def build_database(games: pd.DataFrame, vg: pd.DataFrame, db_path: Path = DB_PATH):
    """Create normalized SQLite DB from cleaned dataframes."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Build dimension tables from union of both datasets
    def _dim(values, table, col):
        uniq = pd.Series(sorted({str(v) for v in values if pd.notna(v)}))
        uniq = uniq[uniq.str.len() > 0]
        df = pd.DataFrame({col: uniq})
        df.to_sql(table, conn, if_exists="append", index=False)
        return pd.read_sql(f"SELECT * FROM {table}", conn)

    plat_vals = pd.concat([games.get("platform", pd.Series(dtype=str)),
                           vg.get("platform", pd.Series(dtype=str))])
    genre_vals = pd.concat([games.get("genre", pd.Series(dtype=str)),
                            vg.get("genre", pd.Series(dtype=str))])
    pub_vals = pd.concat([games.get("publisher", pd.Series(dtype=str)),
                          vg.get("publisher", pd.Series(dtype=str))])

    plat = _dim(plat_vals, "platforms", "platform_name")
    gen = _dim(genre_vals, "genres", "genre_name")
    pub = _dim(pub_vals, "publishers", "publisher_name")

    # Map names → ids
    plat_map = dict(zip(plat.platform_name, plat.platform_id))
    gen_map = dict(zip(gen.genre_name, gen.genre_id))
    pub_map = dict(zip(pub.publisher_name, pub.publisher_id))

    # Insert games
    g = games.copy()
    g["platform_id"] = g.get("platform", "").map(plat_map)
    g["genre_id"] = g.get("genre", "").map(gen_map)
    g["publisher_id"] = g.get("publisher", "").map(pub_map)
    g_cols = ["name", "platform_id", "genre_id", "publisher_id", "release_year",
              "user_score", "critic_score", "user_count", "critic_count",
              "rating", "developer"]
    for c in g_cols:
        if c not in g.columns:
            g[c] = None
    g[g_cols].to_sql("games", conn, if_exists="append", index=False)

    # Build name→game_id lookup so sales can FK back to games
    games_db = pd.read_sql("SELECT game_id, name, platform_id FROM games", conn)
    key = (games_db["name"].str.lower() + "|" +
           games_db["platform_id"].astype("Int64").astype(str))
    name_plat_to_id = dict(zip(key, games_db["game_id"]))

    s = vg.copy()
    s["platform_id"] = s.get("platform", "").map(plat_map)
    s["genre_id"] = s.get("genre", "").map(gen_map)
    s["publisher_id"] = s.get("publisher", "").map(pub_map)
    skey = (s["name"].astype(str).str.lower() + "|" +
            s["platform_id"].astype("Int64").astype(str))
    s["game_id"] = skey.map(name_plat_to_id)

    s_cols = ["game_id", "name", "platform_id", "genre_id", "publisher_id",
              "release_year", "na_sales", "eu_sales", "jp_sales",
              "other_sales", "global_sales"]
    for c in s_cols:
        if c not in s.columns:
            s[c] = None
    s[s_cols].to_sql("sales", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()
    return db_path


def merged_view() -> pd.DataFrame:
    """Convenience: a flat join used across the dashboard."""
    conn = sqlite3.connect(DB_PATH)
    q = """
    SELECT s.sale_id, s.name, p.platform_name AS platform,
           ge.genre_name AS genre, pu.publisher_name AS publisher,
           s.release_year, s.na_sales, s.eu_sales, s.jp_sales,
           s.other_sales, s.global_sales,
           g.user_score, g.critic_score, g.user_count, g.critic_count,
           g.rating, g.developer
    FROM sales s
    LEFT JOIN platforms  p  ON s.platform_id  = p.platform_id
    LEFT JOIN genres     ge ON s.genre_id     = ge.genre_id
    LEFT JOIN publishers pu ON s.publisher_id = pu.publisher_id
    LEFT JOIN games      g  ON s.game_id      = g.game_id
    """
    df = pd.read_sql(q, conn)
    conn.close()
    return df


if __name__ == "__main__":
    games, vg = load_raw()
    games, vg = clean(games, vg)
    path = build_database(games, vg)
    print(f"✅ Database built at {path}")
    print(f"   games rows: {len(games):,} | sales rows: {len(vg):,}")
