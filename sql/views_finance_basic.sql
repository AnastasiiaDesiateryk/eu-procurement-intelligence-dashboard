
CREATE OR REPLACE VIEW v_awards_base AS
WITH base AS (
  SELECT
    NULLIF(buyer_country,'')          AS buyer_country_raw,
    NULLIF(supplier_country,'')       AS supplier_country_raw,
    NULLIF(buyer,'')                  AS buyer_raw,
    NULLIF(supplier,'')               AS supplier_raw,
    NULLIF(cpv_main,'')               AS cpv_main,
    CAST(contract_value AS NUMERIC)   AS amount_eur,
    EXTRACT(YEAR FROM COALESCE(award_date::timestamp, start_date::timestamp))::int AS year
  FROM f_contracts
  WHERE contract_value IS NOT NULL
)
-- explode suppliers; 
SELECT
  COALESCE(NULLIF(split_part(buyer_country_raw,    '---', 1),''),   'UNK') AS country_buyer,
  COALESCE(NULLIF(split_part(supplier_country_raw, '---', 1),''),   'UNK') AS country_supplier,
  split_part(buyer_raw,    '---', 1) AS buyer,
  s_one                               AS supplier,
  cpv_main,
  amount_eur,
  year
FROM base

LEFT JOIN LATERAL (
  SELECT TRIM(x) AS s_one
  FROM regexp_split_to_table(COALESCE(base.supplier_raw,''), '---+') AS x
  WHERE TRIM(x) <> ''
) suppliers ON TRUE;



CREATE OR REPLACE VIEW v_country_year_buyer AS
SELECT
  country_buyer AS country,
  year,
  COUNT(*)                              AS awards,
  SUM(amount_eur)                       AS spend_eur,
  AVG(NULLIF(amount_eur,0))            AS avg_award_eur,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY NULLIF(amount_eur,0)) AS median_award_eur
FROM v_awards_base
GROUP BY 1,2
ORDER BY 1,2;


CREATE OR REPLACE VIEW v_country_year_supplier AS
SELECT
  country_supplier AS country,
  year,
  COUNT(*)                              AS awards,
  SUM(amount_eur)                       AS spend_eur,
  AVG(NULLIF(amount_eur,0))            AS avg_award_eur,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY NULLIF(amount_eur,0)) AS median_award_eur
FROM v_awards_base
GROUP BY 1,2
ORDER BY 1,2;

-- Тоp-CPV 
CREATE OR REPLACE VIEW v_country_year_buyer_top_cpv AS
SELECT country_buyer AS country, year, cpv_main,
       COUNT(*) AS awards, SUM(amount_eur) AS spend_eur,
       RANK() OVER (PARTITION BY country_buyer, year ORDER BY SUM(amount_eur) DESC) AS rnk
FROM v_awards_base
WHERE cpv_main IS NOT NULL
GROUP BY 1,2,3;

CREATE OR REPLACE VIEW v_country_year_buyer_top_suppliers AS
SELECT country_buyer AS country, year, supplier,
       COUNT(*) AS awards, SUM(amount_eur) AS spend_eur,
       RANK() OVER (PARTITION BY country_buyer, year ORDER BY SUM(amount_eur) DESC) AS rnk
FROM v_awards_base
GROUP BY 1,2,3;

CREATE OR REPLACE VIEW v_country_year_supplier_top_buyers AS
SELECT country_supplier AS country, year, buyer,
       COUNT(*) AS awards, SUM(amount_eur) AS spend_eur,
       RANK() OVER (PARTITION BY country_supplier, year ORDER BY SUM(amount_eur) DESC) AS rnk
FROM v_awards_base
GROUP BY 1,2,3;
