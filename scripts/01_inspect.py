"""Step 1: inspect the raw survey (read-only). Prints columns, types, missing counts, date check."""
import pandas as pd

pd.set_option("display.width", 200, "display.max_colwidth", 70)

df = pd.read_csv("data/survey.csv")
print(f"Rows: {len(df)}   Columns: {df.shape[1]}\n")

summary = pd.DataFrame({
    "type": df.dtypes.astype(str),
    "missing": df.isna().sum(),
    "missing_%": (df.isna().mean() * 100).round(1),
    "unique_values": df.nunique(),
})
summary.index = [f"Q{i}: {c[:60]}" for i, c in enumerate(df.columns)]
print(summary.to_string(), "\n")

# Dates: which festival does each row belong to?
ts = pd.to_datetime(df["Timestamp"], errors="coerce")
print("Unparseable timestamps:", ts.isna().sum())
print("Rows per date:")
print(ts.dt.date.value_counts().sort_index().to_string(), "\n")

# Small-choice questions: show their answers
for c in df.columns[1:]:
    if df[c].nunique() <= 8:
        print(f"--- {c[:80]}")
        print(df[c].value_counts(dropna=False).to_string(), "\n")

# Multi-select questions: show distinct individual choices
for c in df.columns:
    if c.startswith(("What activities", "Which of the following", "What types of Reuse")):
        items = df[c].dropna().str.split(r",\s*(?![^()]*\))").explode().str.strip()
        print(f"--- {c[:80]}  (multi-select choices)")
        print(items.value_counts().to_string(), "\n")

# Open text: how many answered
for c in df.columns[2:7]:
    print(f"Open text answered: {df[c].notna().sum():>3}  |  {c[:70]}")
