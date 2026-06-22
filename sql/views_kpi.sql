-- KPI by supplier × month
CREATE OR REPLACE VIEW v_supplier_kpi AS
WITH base AS (
  SELECT
    date_trunc('month', COALESCE(award_date, start_date))::date AS month,
    COALESCE(NULLIF(supplier, ''), 'UNKNOWN') AS supplier,
    CASE
      WHEN start_date IS NOT NULL AND end_date IS NOT NULL
      THEN GREATEST(0, end_date - start_date)::numeric
      ELSE NULL
    END AS lt_days
  FROM f_contracts
  WHERE COALESCE(award_date, start_date) IS NOT NULL
)
SELECT
  month,
  supplier,
  0::numeric AS otd_pct,
  0::numeric AS otif_pct,
  0::numeric AS podr_pct,
  AVG(lt_days)::numeric AS lt_avg,
  CASE
    WHEN AVG(lt_days) IS NULL OR AVG(lt_days) = 0 THEN NULL
    ELSE (STDDEV_POP(lt_days) / NULLIF(AVG(lt_days), 0))::numeric
  END AS lt_cov,
  COUNT(*) AS lines
FROM base
GROUP BY month, supplier;


-- KPI by month across all suppliers
CREATE OR REPLACE VIEW v_kpi_monthly AS
SELECT
  month,
  AVG(otd_pct)::numeric  AS otd_pct,
  AVG(otif_pct)::numeric AS otif_pct,
  AVG(podr_pct)::numeric AS podr_pct,
  AVG(lt_avg)::numeric   AS lt_avg,
  AVG(lt_cov)::numeric   AS lt_cov
FROM v_supplier_kpi
GROUP BY month
ORDER BY month;


-- Cash-to-Cash by quarter and supplier
CREATE OR REPLACE VIEW v_c2c AS
SELECT
  date_trunc('quarter', COALESCE(award_date, start_date))::date AS quarter,
  COALESCE(NULLIF(supplier, ''), 'UNKNOWN') AS supplier,
  CASE
    WHEN start_date IS NOT NULL AND end_date IS NOT NULL
    THEN ROUND((GREATEST(0, end_date - start_date)::numeric / 3.0), 2)
    ELSE NULL
  END AS dio_days,
  payment_terms_d::numeric AS dso_days,
  30::numeric AS dpo_days
FROM f_contracts
WHERE COALESCE(award_date, start_date) IS NOT NULL;
