"""
Runs every .sql file in sql/ against the loaded warehouse, prints the
results, saves them to reports/, and renders the key charts a BI dashboard
would show (funnel, win rate by rep, monthly revenue trend, open pipeline
by stage).
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SQL_DIR = BASE / "sql"
DB_PATH = BASE / "data" / "pipeline.db"
REPORTS_DIR = BASE / "reports"
FIG_DIR = REPORTS_DIR / "figures"


def run_sql_file(conn, path: Path) -> pd.DataFrame:
    sql = path.read_text()
    return pd.read_sql_query(sql, conn)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    results = {}
    report_lines = ["# Sales Pipeline Funnel Analytics - Report\n"]
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        df = run_sql_file(conn, sql_file)
        results[sql_file.stem] = df
        report_lines.append(f"## {sql_file.stem}\n")
        report_lines.append(df.to_markdown(index=False))
        report_lines.append("\n")
        print(f"\n=== {sql_file.stem} ===")
        print(df.to_string(index=False))

    (REPORTS_DIR / "analysis_report.md").write_text("\n".join(report_lines))

    # --- Chart 1: funnel ---
    funnel = results["01_funnel_conversion"].iloc[0]
    stages = ["reached_lead", "reached_qualified", "reached_proposal", "reached_negotiation", "closed_won"]
    labels = ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won"]
    values = [funnel[s] for s in stages]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(labels[::-1], values[::-1], color="#2980b9")
    for i, v in enumerate(values[::-1]):
        ax.text(v, i, f"  {v:,}", va="center")
    ax.set_title("Sales funnel: deals reaching each stage")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "funnel.png", dpi=120)
    plt.close(fig)

    # --- Chart 2: win rate by rep ---
    by_rep = results["02_win_rate_by_rep"].sort_values("win_rate_pct")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(by_rep["sales_rep"], by_rep["win_rate_pct"], color="#27ae60")
    ax.set_xlabel("Win rate (%)")
    ax.set_title("Win rate by sales rep")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "win_rate_by_rep.png", dpi=120)
    plt.close(fig)

    # --- Chart 3: monthly booked revenue ---
    monthly = results["06_monthly_booked_revenue"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(monthly["close_month"], monthly["booked_revenue_usd"], marker="o", color="#c0392b")
    ax.set_title("Monthly booked (closed-won) revenue")
    ax.set_ylabel("USD")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "monthly_revenue.png", dpi=120)
    plt.close(fig)

    # --- Chart 4: open pipeline value by stage ---
    pipeline = results["05_open_pipeline_value"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(pipeline["current_stage"], pipeline["open_pipeline_value_usd"], color="#8e44ad", label="Raw pipeline value")
    ax.bar(pipeline["current_stage"], pipeline["weighted_forecast_usd"], color="#f1c40f", label="Stage-weighted forecast")
    ax.set_ylabel("USD")
    ax.set_title("Open pipeline: raw value vs. stage-weighted forecast")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "open_pipeline.png", dpi=120)
    plt.close(fig)

    conn.close()
    print(f"\nSaved report -> {REPORTS_DIR / 'analysis_report.md'}")
    print(f"Saved 4 figures -> {FIG_DIR}")


if __name__ == "__main__":
    main()
