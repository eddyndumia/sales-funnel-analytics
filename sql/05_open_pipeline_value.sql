-- Open pipeline value by stage: what's currently "in flight" and how much
-- of it is realistically expected to close, using a simple stage-weighted
-- forecast (a standard, if simplified, CRM forecasting convention).

WITH stage_weights AS (
    SELECT 'Lead' AS current_stage, 0.05 AS win_weight
    UNION ALL SELECT 'Qualified', 0.20
    UNION ALL SELECT 'Proposal', 0.45
    UNION ALL SELECT 'Negotiation', 0.70
)
SELECT
    d.current_stage,
    COUNT(*)                                            AS open_deal_count,
    ROUND(SUM(d.deal_value_usd), 0)                       AS open_pipeline_value_usd,
    sw.win_weight,
    ROUND(SUM(d.deal_value_usd) * sw.win_weight, 0)         AS weighted_forecast_usd
FROM deals d
JOIN stage_weights sw ON sw.current_stage = d.current_stage
WHERE d.current_stage NOT IN ('Closed Won', 'Closed Lost')
GROUP BY d.current_stage, sw.win_weight
ORDER BY sw.win_weight DESC;
