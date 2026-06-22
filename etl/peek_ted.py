import zipfile, pandas as pd

for p in ["data/eu/ted_can_2020.zip", "data/eu/ted_can_2023.zip"]:
    with zipfile.ZipFile(p) as z:
        members = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not members:
            print("No CSV inside", p)
            continue
        name = members[0]
        df = pd.read_csv(
            z.open(name),
            nrows=5,
            sep=";",
            engine="python",
            dtype=str,
            on_bad_lines="skip"
        )
        print("=== File:", p, "→ inside:", name)
        print("Columns:", list(df.columns))
        print()
