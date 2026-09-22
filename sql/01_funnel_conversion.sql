-- Funnel conversion: how many deals reached each stage, and the
-- stage-over-stage conversion rate. This is the single most-asked question
-- of any sales pipeline: "where are we losing deals?"

WITH funnel AS (
    SELECT
        COUNT(*)                                            AS total_deals,
        COUNT(*)                                             AS reached_lead,
        SUM(CASE WHEN reached_qualified = 1 THEN 1 ELSE 0 END)  AS reached_qualified,
        SUM(CASE WHEN reached_proposal = 1 THEN 1 ELSE 0 END)    AS reached_proposal,
        SUM(CASE WHEN reached_negotiation = 1 THEN 1 ELSE 0 END) AS reached_negotiation,
        SUM(CASE WHEN current_stage = 'Closed Won' THEN 1 ELSE 0 END) AS closed_won
    FROM deals
)
SELECT
    reached_lead,
    reached_qualified,
    ROUND(100.0 * reached_qualified / reached_lead, 1)         AS lead_to_qualified_pct,
    reached_proposal,
    ROUND(100.0 * reached_proposal / reached_qualified, 1)     AS qualified_to_proposal_pct,
    reached_negotiation,
    ROUND(100.0 * reached_negotiation / reached_proposal, 1)   AS proposal_to_negotiation_pct,
    closed_won,
    ROUND(100.0 * closed_won / reached_negotiation, 1)         AS negotiation_to_won_pct,
    ROUND(100.0 * closed_won / reached_lead, 1)                AS overall_lead_to_won_pct
FROM funnel;
