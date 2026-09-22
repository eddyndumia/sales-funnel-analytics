"""
Tests the SQL queries against a small, hand-built fixture database with
known correct answers - not the generated data, since that has to keep
working even if generate_data.py's parameters change later.
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

FIXTURE_ROWS = [
    # deal_id, sales_rep, source, segment, deal_value_usd, created_at, current_stage, closed_at,
    # reached_qualified, reached_proposal, reached_negotiation
    ("D1", "Rep A", "Inbound", "SMB", 1000, "2024-01-01", "Closed Won", "2024-01-11", 1, 1, 1),
    ("D2", "Rep A", "Inbound", "SMB", 2000, "2024-01-01", "Closed Lost", "2024-01-06", 1, 0, 0),
    ("D3", "Rep B", "Outbound", "SMB", 3000, "2024-01-01", "Closed Won", "2024-01-21", 1, 1, 1),
    ("D4", "Rep B", "Outbound", "SMB", 4000, "2024-01-01", "Lead", None, 0, 0, 0),
    ("D5", "Rep A", "Referral", "Enterprise", 50000, "2024-02-01", "Qualified", None, 1, 0, 0),
]
COLUMNS = ["deal_id", "sales_rep", "source", "segment", "deal_value_usd", "created_at",
           "current_stage", "closed_at", "reached_qualified", "reached_proposal", "reached_negotiation"]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    df = pd.DataFrame(FIXTURE_ROWS, columns=COLUMNS)
    df.to_sql("deals", c, index=False)
    yield c
    c.close()


def _run(conn, filename):
    sql = (SQL_DIR / filename).read_text()
    return pd.read_sql_query(sql, conn)


def test_funnel_conversion_counts(conn):
    df = _run(conn, "01_funnel_conversion.sql")
    row = df.iloc[0]
    assert row["reached_lead"] == 5
    assert row["reached_qualified"] == 4   # D1, D2 (lost after reaching Qualified), D3, D5
    assert row["closed_won"] == 2          # D1, D3


def test_win_rate_by_rep(conn):
    df = _run(conn, "02_win_rate_by_rep.sql").set_index("sales_rep")
    # Rep A: D1 (won), D2 (lost) among closed deals -> D5 is still open, excluded
    assert df.loc["Rep A", "closed_deals"] == 2
    assert df.loc["Rep A", "won"] == 1
    assert df.loc["Rep A", "win_rate_pct"] == 50.0
    # Rep B: D3 (won), D4 is open (Lead), excluded from closed_deals
    assert df.loc["Rep B", "closed_deals"] == 1
    assert df.loc["Rep B", "win_rate_pct"] == 100.0


def test_win_rate_by_source_revenue_totals(conn):
    df = _run(conn, "03_win_rate_by_source.sql").set_index("source")
    assert df.loc["Inbound", "total_booked_revenue_usd"] == 1000  # only D1 won
    assert df.loc["Outbound", "total_booked_revenue_usd"] == 3000  # only D3 won


def test_open_pipeline_value_excludes_closed_deals(conn):
    df = _run(conn, "05_open_pipeline_value.sql").set_index("current_stage")
    assert "Closed Won" not in df.index
    assert "Closed Lost" not in df.index
    assert df.loc["Lead", "open_pipeline_value_usd"] == 4000    # D4
    assert df.loc["Qualified", "open_pipeline_value_usd"] == 50000  # D5


def test_monthly_booked_revenue_only_counts_won(conn):
    df = _run(conn, "06_monthly_booked_revenue.sql").set_index("close_month")
    assert df.loc["2024-01", "deals_won"] == 2       # D1 + D3
    assert df.loc["2024-01", "booked_revenue_usd"] == 4000  # 1000 + 3000
    assert "2024-02" not in df.index  # D5 hasn't closed
