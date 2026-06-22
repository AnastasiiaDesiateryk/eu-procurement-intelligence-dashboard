import os, zipfile, pandas as pd

IN_ZIP = "data/eu/cpv_2008_xls.zip"   # твой архив
OUT_CSV = "data/eu/cpv_dict.csv"

# 1) достаём первый .xls/.xlsx
with zipfile.ZipFile(IN_ZIP, "r") as z:
    # ищем любой .xls или .xlsx
    xls_name = next(n for n in z.namelist() if n.lower().endswith((".xls", ".xlsx")))
    # распаковываем
    z.extract(xls_name, "data/cpv")
    # оставляем только имя файла без подпапок
    xls_path = os.path.join("data/cpv", os.path.basename(xls_name))

# 2) читаем (CODE, EN) и нормализуем
df = pd.read_excel(xls_path, dtype=str)
df = df.rename(columns={"CODE": "code", "EN": "name_en"})
df = df[["code", "name_en"]].dropna()
df["code"] = df["code"].str.strip()
df["name_en"] = df["name_en"].str.strip()

# 3) сохраняем в CSV
df.to_csv(OUT_CSV, index=False, encoding="utf-8")
print(f"Saved {len(df)} rows → {OUT_CSV}")
