"""Loads data/deals.csv into a SQLite database for SQL-based analysis."""
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "pipeline.db"


def main():
    df = pd.read_csv(DATA_DIR / "deals.csv")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS deals")
    df.to_sql("deals", conn, index=False)
    conn.execute("CREATE INDEX idx_deals_rep ON deals(sales_rep)")
    conn.execute("CREATE INDEX idx_deals_stage ON deals(current_stage)")
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
    print(f"Loaded {n} rows into {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
