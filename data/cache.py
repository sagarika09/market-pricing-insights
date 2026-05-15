import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from config import CACHE_DB_PATH, CACHE_TTL_SECONDS, SCHEMA_COLUMNS

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS price_cache (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    query     TEXT NOT NULL,
    source    TEXT NOT NULL,
    condition TEXT NOT NULL DEFAULT 'All',
    title     TEXT,
    price     REAL,
    url       TEXT,
    image_url TEXT,
    scraped_at TEXT,
    cached_at TEXT NOT NULL
)
"""


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(CACHE_DB_PATH)
    con.execute(_CREATE_TABLE)
    return con


def get_cached(query: str, source: str, condition: str = "All") -> pd.DataFrame | None:
    cutoff = (datetime.utcnow() - timedelta(seconds=CACHE_TTL_SECONDS)).isoformat()
    with _conn() as con:
        df = pd.read_sql_query(
            "SELECT source,title,price,url,image_url,scraped_at FROM price_cache "
            "WHERE query=? AND source=? AND condition=? AND cached_at>=?",
            con,
            params=(query, source, condition, cutoff),
        )
    return df if not df.empty else None


def save_cache(query: str, condition: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    cached_at = datetime.utcnow().isoformat()
    rows = [
        (query, r["source"], condition, r["title"], r["price"], r["url"], r.get("image_url", ""), r["scraped_at"], cached_at)
        for _, r in df.iterrows()
    ]
    with _conn() as con:
        con.executemany(
            "INSERT INTO price_cache (query,source,condition,title,price,url,image_url,scraped_at,cached_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            rows,
        )
