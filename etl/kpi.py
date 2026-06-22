from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

SQL = """
-- пересобираем агрегаты как материализованные таблицы
DROP TABLE IF EXISTS kpi_supplier CASCADE;
CREATE TABLE kpi_supplier AS
SELECT * FROM v_supplier_kpi;

DROP TABLE IF EXISTS kpi_c2c CASCADE;
CREATE TABLE kpi_c2c AS
SELECT * FROM v_c2c;

-- индексы для быстрого дашборда
CREATE INDEX IF NOT EXISTS idx_kpi_supplier_month ON kpi_supplier (month);
CREATE INDEX IF NOT EXISTS idx_kpi_supplier_supplier ON kpi_supplier (supplier);
CREATE INDEX IF NOT EXISTS idx_kpi_c2c_quarter ON kpi_c2c (quarter);
"""

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("KPI materialized: kpi_supplier, kpi_c2c")
