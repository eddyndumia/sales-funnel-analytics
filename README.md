# Sales Funnel Analytics

Six SQL queries on a B2B sales pipeline. Where deals drop off, which reps and lead sources actually close, how long deals take, and what the open pipeline is really worth.

The data is synthetic (`src/generate_data.py`), 4,000 deals from Jan 2024 to Apr 2026 with real drop-off, rep skill differences and source quality built in.

| Lead | Qualified | Proposal | Negotiation | Won |
|---|---|---|---|---|
| 4,000 | 2,527 | 1,405 | 909 | 454 |

- 11.3% of leads end up won. The biggest leak is Qualified to Proposal.
- Best rep closes 25.8%, worst 6.6%, on the same lead pool.
- Referrals close at 22.1%, outbound at 10.9%.
- Enterprise deals take 119 days to close, SMB 43.

![Funnel](reports/figures/funnel.png)

Each query is its own file in [`sql/`](sql/), readable on its own. The tests run them against a tiny hand-built database with answers I worked out by hand, so they check the SQL and not the random data.

```bash
pip install -r requirements.txt
python src/generate_data.py
python src/load_db.py
python src/run_analysis.py
python -m pytest tests/ -v
```
