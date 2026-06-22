ALTER TABLE f_contracts
  ADD CONSTRAINT chk_dates       CHECK (end_date >= start_date);

ALTER TABLE f_contracts
  ADD CONSTRAINT chk_value       CHECK (contract_value >= 0);

ALTER TABLE f_contracts
  ADD CONSTRAINT chk_payment     CHECK (payment_terms_d BETWEEN 0 AND 365);

-- Удобные индексы для case-insensitive поиска
CREATE INDEX IF NOT EXISTS ix_f_contracts_buyer_ci
  ON f_contracts (lower(buyer));
CREATE INDEX IF NOT EXISTS ix_f_contracts_supplier_ci
  ON f_contracts (lower(supplier));
