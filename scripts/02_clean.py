"""Step 2: clean data/survey.csv -> data/clean.csv (raw file is never modified).

Anonymization: campuses are labelled "Campus A" / "Campus B"; the timestamp is dropped
(only a duplicate-timestamp flag is kept); emails and phone numbers are redacted from text.
"""
import re
import pandas as pd

RAW, OUT = "data/survey.csv", "data/clean.csv"
CAMPUS_BY_DATE = {"2026-09-16": "Campus A", "2026-09-23": "Campus B"}

raw = pd.read_csv(RAW)
print(f"Raw rows: {len(raw)}")

# --- short column names (positional, so the long question text is not needed downstream)
df = raw.copy()
df.columns = ["timestamp", "role", "barrier", "items_text", "current_action_text", "teams_group",
              "assistance_text", "impact", "known_programs", "wanted_programs", "learn_more"]

# --- clean text: strip whitespace and invisible direction marks
text_cols = [c for c in df.columns if c != "timestamp"]
for c in text_cols:
    df[c] = df[c].astype("string").str.replace("‏", "", regex=False).str.strip()
    df[c] = df[c].replace("", pd.NA)

# --- anonymize program names: original => generic, read from a private git-ignored file
try:
    RENAMES = [tuple(p.strip() for p in line.split("=>")) for line in open("scripts/private_renames.txt") if "=>" in line]
except FileNotFoundError:
    RENAMES = []
    print("NOTE: scripts/private_renames.txt not found - program names will NOT be anonymized")
for c in text_cols:
    for original, generic in RENAMES:
        df[c] = df[c].str.replace(original, generic, regex=False)

# --- 1. remove the test response, identified by content
is_test = df[["items_text", "current_action_text", "assistance_text"]].eq("Test").fillna(False).astype(bool).all(axis=1)
assert is_test.sum() == 1, f"expected exactly 1 test row, found {is_test.sum()}"
print(f"Removed test row(s): {is_test.sum()} (row {df.index[is_test][0] + 2} in the spreadsheet)")
df = df[~is_test].reset_index(drop=True)

# --- 2. campus from date; flag anything unexpected
ts = pd.to_datetime(df["timestamp"], errors="coerce")
df["campus"] = ts.dt.strftime("%Y-%m-%d").map(CAMPUS_BY_DATE).fillna("UNKNOWN DATE")
print("Rows with a date other than 9/16 or 9/23:", (df["campus"] == "UNKNOWN DATE").sum())
df["dup_timestamp"] = df["timestamp"].duplicated(keep=False).astype(int)

# --- 3. which form each person got (blanks on the other form are structural, not missing)
df["form"] = df["role"].map({"Faculty/Staff": "staff_form", "Student": "student_form"})

# --- 4. yes/no and awareness levels
df["learn_more_other_text"] = df["learn_more"].where(~df["learn_more"].isin(["Yes", "No"]))
df["learn_more"] = df["learn_more"].map({"Yes": 1, "No": 0}).astype("Int64")
df["teams_group"] = df["teams_group"].map({"No": "Not aware", "Yes, but I haven't used it": "Aware, not used",
                                           "Yes, I've used it": "Used it"})

# --- 5. barrier: keep the 3 standard answers, move write-ins to "Other"
std_barriers = ["Lack of awareness about reuse/sharing options",
                "Difficulty finding available items or knowing who has them",
                "The cost of transporting items around campus"]
df["barrier_other_text"] = df["barrier"].where(~df["barrier"].isin(std_barriers))
df["barrier"] = df["barrier"].where(df["barrier"].isin(std_barriers) | df["barrier"].isna(), "Other")

# --- 6. multi-select questions -> one 0/1 column per option; write-ins -> *_other_text
SPLIT = r",\s*(?![^()]*\))"  # split on commas that are not inside parentheses
OPTIONS = {
    "impact": ("impact", ["Recycling", "Using Reusables (coffee cups, water bottles, etc.)",
                          "Composting", "Reducing Printing Paper"]),
    "known_programs": ("known", ["Reuse Program", "Bottle Filling Stations", "Donation Program",
                                 "Clothing Swaps", "Residential Composting", "Move-in Cardboard Recycling",
                                 "Appliance Rental Program", "Zero Waste Sports Events"]),
    "wanted_programs": ("want", ["Reusable Containers (coffee cups, clamshells, etc.)", "Fix-it Clinics",
                                 "Clothing Swaps", "Sharing Shelf", "Bottle Filling Stations",
                                 "Digital Sharing Platform"]),
}
def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.split(" (")[0].lower()).strip("_")

for col, (prefix, options) in OPTIONS.items():
    lists = df[col].dropna().str.split(SPLIT)
    other = pd.Series(pd.NA, index=df.index, dtype="string")
    for opt in options:
        df[f"{prefix}_{slug(opt)}"] = pd.NA
        df.loc[lists.index, f"{prefix}_{slug(opt)}"] = lists.apply(lambda l: int(opt in l))
        df[f"{prefix}_{slug(opt)}"] = df[f"{prefix}_{slug(opt)}"].astype("Int64")
    extras = lists.apply(lambda l: "; ".join(x for x in l if x not in options))
    other.loc[extras.index] = extras.replace("", pd.NA)
    df[f"{prefix}_other_text"] = other
    df[f"{prefix}_n_selected"] = lists.apply(lambda l: sum(x in options for x in l)).reindex(df.index).astype("Int64")
    df = df.drop(columns=col)

# --- 7. privacy: redact emails/phones in every text column
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"\(?\b\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")
# School-identifying words live in a private, git-ignored file so they never appear in published code
try:
    PRIVATE = [t.strip() for t in open("scripts/private_terms.txt") if t.strip()]
except FileNotFoundError:
    PRIVATE = []
    print("NOTE: scripts/private_terms.txt not found - school names will NOT be redacted")
# match even when glued to digits/symbols (e.g. "1BU"), but not inside longer letter-words
SCHOOL = re.compile(r"(?<![A-Za-z])\d?(?:" + "|".join(map(re.escape, PRIVATE)) + r")(?![A-Za-z])") if PRIVATE else re.compile(r"(?!x)x")
n_redacted = 0
for c in [c for c in df.columns if c.endswith("_text")]:
    s = df[c].dropna()
    hits = s.str.contains(EMAIL) | s.str.contains(PHONE) | s.str.contains(SCHOOL)
    n_redacted += int(hits.sum())
    df.loc[s.index, c] = (s.str.replace(EMAIL, "[email removed]", regex=True)
                           .str.replace(PHONE, "[phone removed]", regex=True)
                           .str.replace(SCHOOL, "the university", regex=True))
print(f"Text answers with an email, phone, or school name redacted: {n_redacted}")

# --- 8. save (timestamp dropped for anonymity)
df.insert(0, "id", range(1, len(df) + 1))
df = df.drop(columns="timestamp")
df.to_csv(OUT, index=False)

print(f"\nClean rows: {len(df)}  columns: {df.shape[1]}  -> saved to {OUT}\n")
print("Rows per campus:");            print(df["campus"].value_counts().sort_index().to_string(), "\n")
print("Role x campus:");              print(pd.crosstab(df["campus"], df["role"], margins=True).to_string(), "\n")
print("Duplicate-timestamp rows flagged:", int(df["dup_timestamp"].sum()))
for c in ["barrier_other_text", "learn_more_other_text", "impact_other_text", "want_other_text"]:
    if c in df:
        print(f"Write-ins in {c}: {df[c].notna().sum()}")

# --- 9. identifying-term scan on all text (for you to review before publishing)
WATCH = SCHOOL.pattern + r"|@"
print("\nText answers containing possibly identifying words:")
found = 0
for c in [c for c in df.columns if c.endswith("_text")]:
    for i, v in df[c].dropna().items():
        if re.search(WATCH, v, flags=re.I):
            found += 1
            print(f"  id {df.at[i, 'id']:>3} [{c}]: {v[:110]}")
print("  (none)" if not found else f"  {found} found - review before publishing")
