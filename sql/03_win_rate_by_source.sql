-- Win rate by lead source, plus volume - a source with a great win rate but
-- tiny volume matters less than a mediocre-but-large one. Both numbers are
-- needed together, which is why this isn't just "ORDER BY win_rate DESC".

SELECT
    source,
    COUNT(*)                                                       AS total_deals,
    SUM(CASE WHEN current_stage = 'Closed Won' THEN 1 ELSE 0 END)   AS won,
    SUM(CASE WHEN current_stage = 'Closed Lost' THEN 1 ELSE 0 END)  AS lost,
    ROUND(100.0 * SUM(CASE WHEN current_stage = 'Closed Won' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN current_stage IN ('Closed Won','Closed Lost') THEN 1 ELSE 0 END), 0), 1)
                                                                     AS win_rate_pct_of_closed,
    ROUND(SUM(CASE WHEN current_stage = 'Closed Won' THEN deal_value_usd ELSE 0 END), 0)
                                                                     AS total_booked_revenue_usd
FROM deals
GROUP BY source
ORDER BY total_booked_revenue_usd DESC;
