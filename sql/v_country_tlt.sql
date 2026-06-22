-- v_country_tlt: Tender Lead Time (award - dispatch) by buyer country × year
CREATE OR REPLACE VIEW v_country_tlt AS
WITH base AS (
  SELECT
    COALESCE(NULLIF(buyer_country,''), 'UNK') AS country,
    EXTRACT(YEAR FROM award_date)::int        AS year,
    (GREATEST(award_date, dispatch_date) - LEAST(award_date, dispatch_date))::int AS tlt_days
  FROM f_contracts
  WHERE award_date IS NOT NULL
    AND dispatch_date IS NOT NULL
)
SELECT
  country,
  year,
  ROUND(AVG(tlt_days), 1) AS avg_tlt_days,
  COUNT(*)                AS lines
FROM base
WHERE tlt_days IS NOT NULL
GROUP BY country, year
ORDER BY year, avg_tlt_days;
