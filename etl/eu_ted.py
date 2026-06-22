import os
import io
import zipfile
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# --- ENV & DB ---------------------------------------------------------------
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

REQUIRED = [
    "contract_id","supplier","buyer","award_date","start_date",
    "end_date","contract_value","payment_terms_d", "buyer_country","supplier_country","cpv_main","dispatch_date",

]
USE_DEFAULT_DURATION = os.getenv("USE_DEFAULT_DURATION", "0") == "1"

# --- МАППИНГ ИМЁН КОЛОНОК (TED CAN встречаются разные схемы) ---------------
NAME_MAPS = [
    {
        "ID_NOTICE_CAN": "contract_id",
        "CAE_NAME": "buyer",
        "WIN_NAME": "supplier",
        "DT_AWARD": "award_date",
        "DT_DISPATCH": "dispatch_date",  # ← только сюда

        "AWARD_VALUE_EURO": "contract_value",
        "AWARD_VALUE_EURO_FIN_1": "contract_value",
        "AWARD_EST_VALUE_EURO": "contract_value",

        "ISO_COUNTRY_CODE": "buyer_country",
        "WIN_COUNTRY_CODE": "supplier_country",
        "MAIN_CPV_CODE_GPA": "cpv_main",
        "CPV": "cpv_main",
    },
    {
        "CONTRACT_ID": "contract_id",
        "SUPPLIER_NAME": "supplier",
        "BUYER_NAME": "buyer",
        "AWARD_DATE": "award_date",
        "START_DATE": "start_date",
        "END_DATE": "end_date",
        "AMOUNT_EUR": "contract_value",
        "PAYMENT_TERMS": "payment_terms_d",
        "BUYER_COUNTRY": "buyer_country",
        "SUPPLIER_COUNTRY": "supplier_country",
    }
]





def smart_rename(df: pd.DataFrame) -> pd.DataFrame:
    """Переименуем известные имена колонок в наши целевые."""
    cols = {c.strip(): c for c in df.columns}
    for mp in NAME_MAPS:
        if any(k in cols for k in mp.keys()):
            rename = {cols[k]: v for k, v in mp.items() if k in cols}
            return df.rename(columns=rename)
    return df

def _coalesce_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Если после переименования получились дубликаты колонок с одинаковым именем —
    сведём их в одну колонку, беря первое ненулевое/ненаполненное значение по строкам."""
    cols = df.columns
    dup_names = [c for c in set(cols) if list(cols).count(c) > 1]
    for name in dup_names:
        # соберём все одноимённые колоноки в один фрейм
        block = df.loc[:, [c for c in df.columns if c == name]]
        # возьмём первое не-NaN слева направо
        merged = block.bfill(axis=1).iloc[:, 0]
        df = df.drop(columns=[c for c in df.columns if c == name])
        df[name] = merged
    # гарантия: уникальные имена
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# --- ЧТЕНИЕ CSV / ZIP -------------------------------------------------------
import csv
import re

DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{2}$")  # пример: 28/12/22

def _read_csv_safely(path_or_buf):
    """
    Надёжное чтение TED CSV:
    - авто-детект разделителя, fallback на ',' затем ';'
    - читаем как строки (dtype=str)
    - без low_memory (не дружит с engine='python')
    - пропускаем битые строки
    """
    # вынимаем небольшой сэмпл
    try:
        if isinstance(path_or_buf, (str, bytes, os.PathLike)):
            with open(path_or_buf, 'rb') as fh:
                sample_bytes = fh.read(1_000_000)
        else:
            pos = path_or_buf.tell()
            sample_bytes = path_or_buf.read(1_000_000)
            path_or_buf.seek(pos)
    except Exception:
        sample_bytes = b""

    for enc in ("utf-8", "latin-1"):
        try:
            sample_text = sample_bytes.decode(enc, errors="replace")
        except Exception:
            continue

        # попробуем sniffer
        try:
            dialect = csv.Sniffer().sniff(sample_text, delimiters=";,|\t,")
            sep = dialect.delimiter
        except Exception:
            # TED subset канонически с запятой
            sep = ","

        for header in [0, None]:  # 0 = первая строка как шапка, None = без шапки
            try:
                return pd.read_csv(
                    path_or_buf,
                    sep=sep,
                    engine="python",
                    dtype=str,
                    on_bad_lines="skip",
                    header=header,
                    quoting=csv.QUOTE_MINIMAL
                )
            except Exception:
                continue

    # финальный fallback
    return pd.read_csv(path_or_buf, sep=",", engine="python", dtype=str, on_bad_lines="skip", header=None)

def _coalesce_amount_scalar(x):
    x = "" if x is None else str(x)
    x = x.replace("\xa0", " ").replace(" ", "").replace(",", ".")
    try:
        return float(x)
    except Exception:
        return 0.0
  


import numpy as np
import re as _re

_YMD_DASH   = _re.compile(r"^\d{4}-\d{2}-\d{2}$")   # 2024-12-31
_YMD_SLASH  = _re.compile(r"^\d{4}/\d{2}/\d{2}$")   # 2024/12/31
_DMY_SLASH  = _re.compile(r"^\d{2}/\d{2}/\d{4}$")   # 31/12/2024
_DMY_DOTS   = _re.compile(r"^\d{2}\.\d{2}\.\d{4}$") # 31.12.2024
_DMY_2Y     = _re.compile(r"^\d{2}/\d{2}/\d{2}$")   # 31/12/24

def _parse_date_series(s: pd.Series) -> pd.Series:
    s_raw = s.astype(str).str.strip()
    s_raw = s_raw.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    s_norm = s_raw.str.replace(".", "/", regex=False)

    out = pd.Series(pd.NaT, index=s_raw.index, dtype="datetime64[ns]")

    def apply_mask(mask, series, fmt):
        mask = mask.fillna(False).astype(bool)   # ← ключевая строка
        if mask.any():
            out.loc[mask] = pd.to_datetime(series.loc[mask], format=fmt, errors="coerce")

    apply_mask(s_raw.str.match(_YMD_DASH),  s_raw, "%Y-%m-%d")
    apply_mask(s_norm.str.match(_YMD_SLASH), s_norm, "%Y/%m/%d")
    apply_mask(s_norm.str.match(_DMY_SLASH), s_norm, "%d/%m/%Y")
    apply_mask(s_raw.str.match(_DMY_DOTS),   s_raw, "%d.%m.%Y")
    apply_mask(s_norm.str.match(_DMY_2Y),    s_norm, "%d/%m/%y")

    return out.dt.date




# --- НОРМАЛИЗАЦИЯ -----------------------------------------------------------
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = smart_rename(df.copy())
    df = _coalesce_duplicate_columns(df)

    def col(df_, name):
        if name not in df_.columns:
            return None
        obj = df_[name]
        if isinstance(obj, pd.DataFrame):  # дубликаты имён → берём первый
            obj = obj.iloc[:, 0]
        return obj

# --- ДАТЫ ---
    for c in ["award_date", "start_date", "end_date", "dispatch_date"]:
        s = col(df, c)
        if s is not None:
            df[c] = _parse_date_series(s)

    # если award_date нет, но есть dispatch_date — берём dispatch_date
    if "award_date" not in df.columns and "dispatch_date" in df.columns:
        df["award_date"] = df["dispatch_date"]
    elif "award_date" in df.columns and "dispatch_date" in df.columns:
    # если award_date частично пустая — дополним из dispatch_date
        mask = pd.isna(df["award_date"]) & pd.notna(df["dispatch_date"])
    if mask.any():
        df.loc[mask, "award_date"] = df.loc[mask, "dispatch_date"]

# вернём к date
    if "award_date" in df.columns:
        df["award_date"] = pd.to_datetime(df["award_date"]).dt.date

# если start_date нет → award_date
    if col(df, "start_date") is None and col(df, "award_date") is not None:
        df["start_date"] = col(df, "award_date")

# end_date не трогаем (никаких дефолтов)
    if col(df, "end_date") is None:
        df["end_date"] = pd.NaT



    # --- СУММА (AWARD_*VALUE*EURO и ко) ---

    if "contract_value" not in df.columns:
        cand = [c for c in df.columns if _re.search(r"AWARD_.*VALUE.*EURO", str(c), flags=_re.I)]
        if not cand:
            cand = [c for c in df.columns if _re.match(r"^(VAL(_TOTAL)?(_EURO)?|VALUE(_CONTRACT)?)(|_EUR)$", str(c), flags=_re.I)]
        if cand:
            s = col(df, cand[0])
            df["contract_value"] = s
        else:
            df["contract_value"] = 0

  # коалесим скаляры суммы единым способом
    df["contract_value"] = df["contract_value"].apply(_coalesce_amount_scalar)

    # --- PAYMENT TERMS ---
    s = col(df, "payment_terms_d")
    if s is not None:
        # сохраняем как число, но БЕЗ дефолта 45, пусть остаётся NaN если неизвестно
        df["payment_terms_d"] = pd.to_numeric(s, errors="coerce")
    else:
        df["payment_terms_d"] = pd.NA

    # --- МИНИ-ВАЛИДАЦИЯ ---
    must = ["contract_id", "supplier", "buyer", "start_date"]
    df = df.dropna(subset=must)

    for c in REQUIRED:
        if c not in df.columns:
            if c == "contract_value":
                df[c] = 0.0
            elif c == "payment_terms_d":
                df[c] = pd.NA
            else:
                df[c] = pd.NA
    # гарантируем уникальные имена
    df = df.loc[:, ~df.columns.duplicated()]


    # типы
    df["contract_value"] = pd.to_numeric(df["contract_value"], errors="coerce").fillna(0.0).astype(float)
    df["payment_terms_d"] = pd.to_numeric(df["payment_terms_d"], errors="coerce")

    for c in ["buyer_country", "supplier_country"]:
        if c not in df.columns:
            df[c] = pd.NA

    if "cpv_main" not in df.columns:
       df["cpv_main"] = pd.NA

    return df[REQUIRED]




# --- UPSERT -----------------------------------------------------------------
from sqlalchemy import text

def upsert_contracts(df: pd.DataFrame):
    with engine.begin() as conn:
        df.to_sql("_stg_contracts", conn, if_exists="replace", index=False)

        conn.execute(text("""
            CREATE TEMP TABLE _stg_norm AS
            SELECT DISTINCT ON (contract_id)
                CAST(NULLIF(trim(contract_id::text), '') AS BIGINT) AS contract_id,
                trim(supplier::text)                                  AS supplier,
                trim(buyer::text)                                     AS buyer,
                trim(buyer_country::text)                             AS buyer_country,
                trim(supplier_country::text)                          AS supplier_country,
                trim(cpv_main::text)                                  AS cpv_main,
                CAST(award_date AS DATE)                              AS award_date,
                CAST(start_date AS DATE)                              AS start_date,
                CAST(end_date   AS DATE)                              AS end_date,
                CAST(contract_value AS NUMERIC(18,2))                 AS contract_value,
                CAST(payment_terms_d AS INTEGER)                      AS payment_terms_d,
                CAST(dispatch_date AS DATE)                           AS dispatch_date
            FROM _stg_contracts
            WHERE contract_id IS NOT NULL
            ORDER BY contract_id, award_date DESC NULLS LAST;

            INSERT INTO f_contracts (
                contract_id, supplier, buyer, buyer_country, supplier_country,
                cpv_main, dispatch_date,
                award_date, start_date, end_date, contract_value, payment_terms_d
            )
            SELECT
                contract_id, supplier, buyer, buyer_country, supplier_country,
                cpv_main, dispatch_date,
                award_date, start_date, end_date, contract_value, payment_terms_d
            FROM _stg_norm
            ON CONFLICT (contract_id) DO UPDATE
            SET supplier         = EXCLUDED.supplier,
                buyer            = EXCLUDED.buyer,
                buyer_country    = EXCLUDED.buyer_country,
                supplier_country = EXCLUDED.supplier_country,
                cpv_main         = EXCLUDED.cpv_main,
                dispatch_date    = EXCLUDED.dispatch_date,
                award_date       = EXCLUDED.award_date,
                start_date       = EXCLUDED.start_date,
                end_date         = EXCLUDED.end_date,
                contract_value   = EXCLUDED.contract_value,
                payment_terms_d  = EXCLUDED.payment_terms_d;

            DROP TABLE IF EXISTS _stg_contracts;
            DROP TABLE IF EXISTS _stg_norm;
        """))



# --- ЗАГРУЗКА ИЗ data/eu/ (CSV и ZIP) --------------------------------------
def load_eu_csv(path: str = "data/eu"):
    if not os.path.isdir(path):
        print(f"Folder not found: {path}")
        return

    files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith((".csv", ".zip"))]
    if not files:
        print("No CSV/ZIP files in data/eu/")
        return

    frames = []
    for f in files:
        if f.endswith(".csv"):
            df = _read_csv_safely(f)
            nf = normalize(df)
        elif f.endswith(".zip"):
            with zipfile.ZipFile(f) as z:
                members = [n for n in z.namelist() if n.lower().endswith(".csv")]
                if not members:
                    continue
                for name in members:
                    with z.open(name) as fh:
                        data = fh.read()
                    df = _read_csv_safely(io.BytesIO(data))
                    nf = normalize(df)
        else:
           continue

        # выравниваем набор и порядок колонок + снимаем возможные дубликаты имён
        missing = [c for c in REQUIRED if c not in nf.columns]
        for c in missing:
            nf[c] = pd.NA
        nf = nf[REQUIRED]
        nf = nf.loc[:, ~nf.columns.duplicated()]
        frames.append(nf)
 
    if not frames:
         print("Nothing parsed from provided files")
         return 
               
    out = pd.concat(frames, ignore_index=True, copy=False)
    upsert_contracts(out)
    print(f"Upserted {len(out)} rows into f_contracts")




# --- MAIN -------------------------------------------------------------------
if __name__ == "__main__":
    load_eu_csv()
