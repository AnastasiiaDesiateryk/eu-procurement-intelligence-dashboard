import zipfile, pandas as pd, re

FILES = ["data/eu/ted_can_2020.zip", "data/eu/ted_can_2023.zip"]

PATTERNS = {
    "buyer":   re.compile(r"^CAE_", re.I),
    "winner":  re.compile(r"^WIN_", re.I),
    "value":   re.compile(r"^(VAL(_TOTAL)?(_EURO)?|VALUE(_CONTRACT)?)(|_EUR)$", re.I),
    "award":   re.compile(r"^(DT_.*AWARD|DATE_.*AWARD|DT_DISPATCH)$", re.I),
}

def peek(path):
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        df = pd.read_csv(z.open(name), nrows=5, sep=",", engine="python", dtype=str, on_bad_lines="skip")
        cols = list(df.columns)
        print(f"\n=== {path} → {name}")
        for key, rx in PATTERNS.items():
            hit = [c for c in cols if rx.match(str(c))]
            print(f"{key.upper():>7}: {hit[:8]}{' ...' if len(hit)>8 else ''}")
        # покажем пару значений для очевидных полей
        for c in ["CAE_NAME","WIN_NAME","VAL_TOTAL_EURO","VAL_TOTAL","DT_AWARD","DT_DISPATCH"]:
            if c in df.columns:
                print(f"\nSample {c}:")
                print(df[c].head(3).tolist())

for p in FILES:
    peek(p)

