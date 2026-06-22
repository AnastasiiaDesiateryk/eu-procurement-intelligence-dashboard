-- База данных уже есть. Создаём целевую таблицу.
CREATE TABLE IF NOT EXISTS f_contracts (
  contract_id       BIGINT PRIMARY KEY,
  supplier          TEXT    NOT NULL,
  buyer             TEXT    NOT NULL,
  award_date        DATE,
  start_date        DATE    NOT NULL,
  end_date          DATE    NOT NULL,
  contract_value    NUMERIC(18,2) NOT NULL DEFAULT 0,
  payment_terms_d   INTEGER NOT NULL DEFAULT 45,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Индексы под типовые срезы/графики
-- CREATE INDEX IF NOT EXISTS ix_f_contracts_award_month
--   ON f_contracts (date_trunc('month', award_date));

CREATE INDEX IF NOT EXISTS ix_f_contracts_buyer
  ON f_contracts (buyer);

CREATE INDEX IF NOT EXISTS ix_f_contracts_supplier
  ON f_contracts (supplier);

-- Триггер на updated_at (опционально, но полезно)
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_updated_at ON f_contracts;
CREATE TRIGGER trg_set_updated_at
BEFORE UPDATE ON f_contracts
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
