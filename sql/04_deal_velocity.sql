-- Deal velocity: average days from creation to close, for won vs. lost
-- deals, broken out by segment - bigger deals should take longer, and this
-- confirms whether that's actually true in the data or whether a segment
-- is taking unexpectedly long relative to its size.

SELECT
    segment,
    current_stage,
    COUNT(*)                                                      AS deal_count,
    ROUND(AVG(JULIANDAY(closed_at) - JULIANDAY(created_at)), 1)    AS avg_days_to_close
FROM deals
WHERE current_stage IN ('Closed Won', 'Closed Lost')
  AND closed_at IS NOT NULL
GROUP BY segment, current_stage
ORDER BY
    CASE segment WHEN 'SMB' THEN 1 WHEN 'Mid-Market' THEN 2 WHEN 'Enterprise' THEN 3 END,
    current_stage;
