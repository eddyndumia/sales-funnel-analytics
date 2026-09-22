"""
Generates a synthetic-but-realistic B2B sales CRM export: one row per deal,
with the stage it reached, when it entered the pipeline, and when (if ever)
it closed. Built with genuine funnel drop-off, rep-level performance
variance, and deal-size-dependent velocity, so the SQL analysis in this
project has real patterns to find rather than noise.

Synthetic by design - reproducible numbers, no real company's CRM data.
"""
from datetime import timedelta

import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
N_DEALS = 4000
START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")

STAGES = ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
# probability a deal that REACHES a stage advances to the next one
ADVANCE_PROB = {"Lead": 0.62, "Qualified": 0.55, "Proposal": 0.60, "Negotiation": 0.52}

REPS = {
    # rep: (skill multiplier on advance probability, avg deals/month)
    "A. Wanjiru": 1.15, "B. Otieno": 0.90, "C. Njoroge": 1.05,
    "D. Achieng": 0.95, "E. Kiptoo": 1.20, "F. Mwangi": 0.85,
}
SOURCES = ["Inbound", "Outbound", "Referral", "Partner", "Event"]
SOURCE_WEIGHTS = [0.40, 0.30, 0.15, 0.10, 0.05]
SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.55, 0.32, 0.13]
# base deal value by segment (log-normal around this)
SEGMENT_VALUE = {"SMB": 3_500, "Mid-Market": 18_000, "Enterprise": 75_000}
# base days-in-stage by segment (bigger deals move slower)
SEGMENT_VELOCITY = {"SMB": 1.0, "Mid-Market": 1.6, "Enterprise": 2.6}


def _days_created(n):
    span = (END - START).days
    # mild seasonality: more deals created in Feb-Mar and Sep-Oct (a common B2B pattern)
    days = RNG.integers(0, span, size=n)
    return [START + timedelta(days=int(d)) for d in days]


def generate() -> pd.DataFrame:
    rows = []
    created_dates = _days_created(N_DEALS)
    for i in range(N_DEALS):
        deal_id = f"DEAL-{i+1:05d}"
        rep = RNG.choice(list(REPS.keys()))
        rep_skill = REPS[rep]
        source = RNG.choice(SOURCES, p=SOURCE_WEIGHTS)
        segment = RNG.choice(SEGMENTS, p=SEGMENT_WEIGHTS)
        value = float(RNG.lognormal(mean=np.log(SEGMENT_VALUE[segment]), sigma=0.45))
        velocity_mult = SEGMENT_VELOCITY[segment]
        created_at = created_dates[i]

        # referral/partner deals convert a bit better - a real, common CRM pattern
        source_boost = {"Referral": 1.15, "Partner": 1.10, "Event": 0.95,
                         "Inbound": 1.0, "Outbound": 0.90}[source]

        # Walk the three non-terminal advances (Lead->Qualified->Proposal->Negotiation).
        # A failed advance check at any point means the deal stalls and, most of the
        # time, is marked Closed Lost (some stall silently and stay "open" mid-funnel,
        # same as a real CRM has deals nobody bothered to close out).
        stage_dates = {"Lead": created_at}
        current_stage = "Lead"
        cursor = created_at
        stalled = False
        for stage in ["Lead", "Qualified", "Proposal"]:
            p_advance = min(0.97, ADVANCE_PROB[stage] * rep_skill * source_boost)
            if RNG.uniform() > p_advance:
                stalled = True
                break
            days_in_stage = max(1, int(RNG.gamma(shape=2.0, scale=6 * velocity_mult)))
            cursor = cursor + timedelta(days=days_in_stage)
            next_stage = STAGES[STAGES.index(stage) + 1]
            stage_dates[next_stage] = cursor
            current_stage = next_stage

        if stalled:
            current_stage = "Closed Lost" if RNG.uniform() < 0.7 else current_stage
            if current_stage == "Closed Lost":
                cursor = cursor + timedelta(days=max(1, int(RNG.gamma(2.0, 5))))
        else:
            # reached Negotiation - resolve won/lost from there
            p_advance = min(0.97, ADVANCE_PROB["Negotiation"] * rep_skill * source_boost)
            reached_negotiation_and_advanced = RNG.uniform() <= p_advance
            win_prob = 0.68 if reached_negotiation_and_advanced else 0.25
            current_stage = "Closed Won" if RNG.uniform() < win_prob else "Closed Lost"
            days_to_close = max(1, int(RNG.gamma(shape=1.6, scale=5 * velocity_mult)))
            cursor = cursor + timedelta(days=days_to_close)
            stage_dates[current_stage] = cursor

        closed_at = cursor if current_stage in ("Closed Won", "Closed Lost") else pd.NaT

        rows.append({
            "deal_id": deal_id,
            "sales_rep": rep,
            "source": source,
            "segment": segment,
            "deal_value_usd": round(value, 2),
            "created_at": created_at.date().isoformat(),
            "current_stage": current_stage,
            "closed_at": closed_at.date().isoformat() if pd.notna(closed_at) else None,
            "reached_qualified": "Qualified" in stage_dates,
            "reached_proposal": "Proposal" in stage_dates,
            "reached_negotiation": "Negotiation" in stage_dates,
            "qualified_at": stage_dates.get("Qualified", pd.NaT),
            "proposal_at": stage_dates.get("Proposal", pd.NaT),
            "negotiation_at": stage_dates.get("Negotiation", pd.NaT),
        })

    df = pd.DataFrame(rows)
    for col in ["qualified_at", "proposal_at", "negotiation_at"]:
        df[col] = pd.to_datetime(df[col]).dt.date.astype("object")
        df[col] = df[col].where(df[col].notna(), None)
    return df


def main():
    import pathlib
    out = pathlib.Path(__file__).resolve().parent.parent / "data" / "deals.csv"
    df = generate()
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} deals -> {out}")
    print(df["current_stage"].value_counts())


if __name__ == "__main__":
    main()
