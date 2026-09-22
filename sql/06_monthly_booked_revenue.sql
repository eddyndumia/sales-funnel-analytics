-- Monthly booked (closed-won) revenue trend - the number a sales leader
-- looks at every Monday morning.

SELECT
    strftime('%Y-%m', closed_at)                          AS close_month,
    COUNT(*)                                                AS deals_won,
    ROUND(SUM(deal_value_usd), 0)                            AS booked_revenue_usd,
    ROUND(AVG(deal_value_usd), 0)                              AS avg_deal_size_usd
FROM deals
WHERE current_stage = 'Closed Won'
GROUP BY close_month
ORDER BY close_month;
