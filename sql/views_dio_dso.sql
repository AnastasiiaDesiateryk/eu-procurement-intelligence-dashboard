-- v_country_dio_dso: только DIO (без DSO, без C2C)
-- Групуємо по країні покупця; при потребі можна замінити buyer_country → supplier_country.
CREATE OR REPLACE VIEW v_country_dio_dso AS
WITH base AS (
  SELECT
    COALESCE(NULLIF(buyer_country,''), 'UNK')          AS country,
    EXTRACT(YEAR FROM COALESCE(award_date,start_date))::int AS year,
    (end_date - start_date)::numeric                   AS lt_days,   -- lead time в днях
    contract_value::numeric                            AS spend_eur
  FROM f_contracts
  WHERE start_date IS NOT NULL
    AND end_date   IS NOT NULL
)
SELECT
  country,
  year,
  ROUND(AVG(lt_days)/3.0, 2)  AS dio_days,   -- прокси: DIO ≈ LT/3
  COUNT(*)                    AS lines,
  SUM(spend_eur)              AS spend_eur
FROM base
WHERE lt_days IS NOT NULL
GROUP BY 1,2;

-- удобный срез по годам (например 2020 и 2023)
CREATE OR REPLACE VIEW v_country_dio_dso_2020_2023 AS
SELECT *
FROM v_country_dio_dso
WHERE year IN (2020, 2023)
ORDER BY country, year;
