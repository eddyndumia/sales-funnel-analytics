-- Win rate and average deal size by sales rep, restricted to deals that have
-- actually closed (won or lost) so open pipeline doesn't distort the rate.

SELECT
    sales_rep,
    COUNT(*)                                                         AS closed_deals,
    SUM(CASE WHEN current_stage = 'Closed Won' THEN 1 ELSE 0 END)     AS won,
    ROUND(100.0 * SUM(CASE WHEN current_stage = 'Closed Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate_pct,
    ROUND(AVG(CASE WHEN current_stage = 'Closed Won' THEN deal_value_usd END), 0) AS avg_won_deal_value_usd,
    ROUND(SUM(CASE WHEN current_stage = 'Closed Won' THEN deal_value_usd ELSE 0 END), 0) AS total_booked_revenue_usd
FROM deals
WHERE current_stage IN ('Closed Won', 'Closed Lost')
GROUP BY sales_rep
ORDER BY win_rate_pct DESC;
