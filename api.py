
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:pg@localhost:5432/scm_mvp",
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# -------------------- C2C (supplier-quarter baseline) --------------------
@app.get("/api/c2c/latest")
def c2c_latest(supplier: str | None = Query(default=None)):
    sql = """
        SELECT quarter, supplier, dio_days, dso_days, dpo_days,
               (dio_days + dso_days - dpo_days) AS c2c_days
        FROM v_c2c
        {where}
        ORDER BY quarter DESC
        LIMIT 1
    """
    where = "WHERE supplier = :supplier" if supplier else ""
    with engine.connect() as c:
        row = c.execute(
            text(sql.format(where=where)),
            {"supplier": supplier} if supplier else {},
        ).mappings().first()
    return row or {}

@app.get("/api/c2c/top")
def c2c_top(limit: int = 20):
    sql = text("""
        SELECT quarter, supplier, dio_days, dso_days, dpo_days,
               (dio_days + dso_days - dpo_days) AS c2c_days
        FROM v_c2c
        WHERE quarter = (SELECT MAX(quarter) FROM v_c2c)
        ORDER BY c2c_days DESC NULLS LAST
        LIMIT :limit
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"limit": limit}).mappings()]
    return {"items": rows}

# -------------------- Suppliers KPI --------------------
@app.get("/api/suppliers")
def suppliers():
    sql = text("""
        SELECT supplier,
               AVG(otd_pct)  AS otd_pct,
               AVG(otif_pct) AS otif_pct,
               AVG(podr_pct) AS podr_pct,
               AVG(lt_avg)   AS lt_avg,
               AVG(lt_cov)   AS lt_cov,
               SUM(lines)    AS lines
        FROM v_supplier_kpi
        GROUP BY supplier
        ORDER BY podr_pct DESC NULLS LAST
        LIMIT 200
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql).mappings()]
    return {"items": rows}

@app.get("/api/kpi")
def kpi_timeseries():
    sql = text("""
        SELECT to_char(month, 'YYYY-MM') AS month,
               AVG(otd_pct)  AS otd_pct,
               AVG(otif_pct) AS otif_pct,
               AVG(podr_pct) AS podr_pct,
               AVG(lt_avg)   AS lt_avg,
               AVG(lt_cov)   AS lt_cov
        FROM v_supplier_kpi
        GROUP BY month
        ORDER BY month
        LIMIT 120
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql).mappings()]
    return {"items": rows}

# -------------------- Country-level C2C --------------------
@app.get("/api/c2c/country")
def c2c_country(years: str = "2020,2023"):
    ys = [int(y.strip()) for y in years.split(",") if y.strip().isdigit()] or [2020, 2023]
    sql = text("""
        SELECT country, year, dio_days, dso_days, dpo_days,
               (dio_days + dso_days - dpo_days) AS c2c_days,
               lines, spend_eur
        FROM v_c2c_country_year
        WHERE year = ANY(:years)
        ORDER BY country, year
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"years": ys}).mappings()]
    return {"items": rows}

@app.get("/api/c2c/country/delta")
def c2c_country_delta(year_a: int = 2020, year_b: int = 2023):
    sql = text("""
        WITH src AS (
          SELECT country, year,
                 (dio_days + dso_days - dpo_days) AS c2c_days,
                 lines, spend_eur
          FROM v_c2c_country_year
          WHERE year = ANY(:years)
        ),
        pvt AS (
          SELECT
            country,
            MAX(CASE WHEN year = :ya THEN c2c_days END) AS c2c_ya,
            MAX(CASE WHEN year = :yb THEN c2c_days END) AS c2c_yb,
            MAX(CASE WHEN year = :ya THEN spend_eur END) AS spend_a,
            MAX(CASE WHEN year = :yb THEN spend_eur END) AS spend_b,
            MAX(CASE WHEN year = :ya THEN lines END)     AS lines_a,
            MAX(CASE WHEN year = :yb THEN lines END)     AS lines_b
          FROM src
          GROUP BY country
        )
        SELECT country, c2c_ya, c2c_yb,
               CASE WHEN c2c_ya IS NOT NULL AND c2c_yb IS NOT NULL
                    THEN (c2c_yb - c2c_ya) ELSE NULL END AS c2c_delta,
               spend_a, spend_b, lines_a, lines_b
        FROM pvt
        ORDER BY country
    """)
    params = {"years": [year_a, year_b], "ya": year_a, "yb": year_b}
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, params).mappings()]
    return {"items": rows}

# -------------------- Country DIO/DSO (без C2C) --------------------
@app.get("/api/country/dio_dso")
def country_dio_dso(years: str = "2020,2023"):
    ys = [int(y) for y in years.split(",") if y.strip().isdigit()] or [2020, 2023]
    sql = text("""
        SELECT country, year, dio_days, dso_days, lines, spend_eur
        FROM v_country_dio_dso
        WHERE year = ANY(:years)
        ORDER BY country, year
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"years": ys}).mappings()]
    return {"items": rows}

# ==================== FINANCE ====================

# ---- Aggregates by country ----
@app.get("/api/finance/buyer")
def finance_buyer(years: str = "2020,2023"):
    ys = [int(y) for y in years.split(",") if y.strip().isdigit()] or [2020, 2023]
    sql = text("""
        SELECT country, year, awards, spend_eur, avg_award_eur, median_award_eur
        FROM v_country_year_buyer
        WHERE year = ANY(:years)
        ORDER BY country, year
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"years": ys}).mappings()]
    return {"items": rows}

@app.get("/api/finance/supplier")
def finance_supplier(years: str = "2020,2023"):
    ys = [int(y) for y in years.split(",") if y.strip().isdigit()] or [2020, 2023]
    sql = text("""
        SELECT country, year, awards, spend_eur, avg_award_eur, median_award_eur
        FROM v_country_year_supplier
        WHERE year = ANY(:years)
        ORDER BY country, year
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"years": ys}).mappings()]
    return {"items": rows}

# ---- Top-10 blocks ----
@app.get("/api/finance/buyer/top_cpv")
def finance_buyer_top_cpv(country: str, year: int, limit: int = 10):
    """
    Топ-CPV по стране покупателя и году.
    Источник: v_buyer_top_cpv (cpv_code, cpv_name, awards, spend_eur, rnk)
    """
    sql = text("""
        SELECT cpv_code, cpv_name, awards, spend_eur, rnk
        FROM v_buyer_top_cpv
        WHERE country = :country AND year = :year
        ORDER BY rnk
        LIMIT :limit
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(
            sql, {"country": country, "year": year, "limit": limit}
        ).mappings()]
    return {"items": rows}

@app.get("/api/finance/buyer/top_suppliers")
def finance_buyer_top_suppliers(country: str, year: int, limit: int = 10):
    sql = text("""
        SELECT supplier, awards, spend_eur, rnk
        FROM v_country_year_buyer_top_suppliers
        WHERE country = :country AND year = :year
        ORDER BY rnk
        LIMIT :limit
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"country": country, "year": year, "limit": limit}).mappings()]
    return {"items": rows}

@app.get("/api/finance/supplier/top_buyers")
def finance_supplier_top_buyers(country: str, year: int, limit: int = 10):
    sql = text("""
        SELECT buyer, awards, spend_eur, rnk
        FROM v_country_year_supplier_top_buyers
        WHERE country = :country AND year = :year
        ORDER BY rnk
        LIMIT :limit
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"country": country, "year": year, "limit": limit}).mappings()]
    return {"items": rows}

# ---- TLT cards ----
@app.get("/api/tlt/top")
def tlt_top(year: int, limit: int = 3):
    sql = text("""
        SELECT country, avg_tlt_days, lines
        FROM v_country_tlt
        WHERE year = :year
        ORDER BY avg_tlt_days ASC
        LIMIT :limit
    """)
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(sql, {"year": year, "limit": limit}).mappings()]
    return {"items": rows}
