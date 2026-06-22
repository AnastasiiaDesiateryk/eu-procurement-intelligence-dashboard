-- -- Активные контракты на сегодня
-- CREATE OR REPLACE VIEW v_active_contracts AS
-- SELECT *
-- FROM f_contracts
-- WHERE current_date BETWEEN start_date AND end_date;

-- -- Траты по покупателю по месяцам (award_date)
-- CREATE OR REPLACE VIEW v_spend_by_buyer_month AS
-- SELECT
--   buyer,
--   date_trunc('month', award_date)::date AS month,
--   SUM(contract_value) AS spend_eur
-- FROM f_contracts
-- GROUP BY 1,2;

-- -- Траты по поставщику по месяцам
-- CREATE OR REPLACE VIEW v_spend_by_supplier_month AS
-- SELECT
--   supplier,
--   date_trunc('month', award_date)::date AS month,
--   SUM(contract_value) AS spend_eur
-- FROM f_contracts
-- GROUP BY 1,2;

-- -- Самый простой «топ-10 поставщиков»
-- CREATE OR REPLACE VIEW v_top_suppliers_total AS
-- SELECT supplier, SUM(contract_value) AS total_eur
-- FROM f_contracts
-- GROUP BY supplier
-- ORDER BY total_eur DESC
-- LIMIT 10;

