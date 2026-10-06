"""Create (if needed) and inspect the SQLite database. Run: python view_db.py"""
from src import config as C, tracker

with tracker.db() as con:  # opening it creates progress.db and the tables
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    print(f"Database file: {C.DB_FILE}\n")
    for t in tables:
        cols = [r["name"] for r in con.execute(f"PRAGMA table_info({t})")]
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}  ({n} rows)\n  columns: {', '.join(cols)}\n")