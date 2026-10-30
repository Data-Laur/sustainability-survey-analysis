"""Step 9: unmet demand - what respondents asked for or said they want, with counts (read-only on data/clean.csv).

Each student request is labelled:
  - "Already on the programs list": also offered as an answer option in the 'existing programs' question,
    so the ask may be for MORE of it or for better visibility, not for something new.
  - "Not on the programs list": candidate truly-new program (CONFIRM it does not exist before acting).
"""
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
import chart_style as cs
cs.apply()

df = pd.read_csv("data/clean.csv")
stud = df[df.form == "student_form"]
staff = df[df.form == "staff_form"]
rows = []


def add(audience, ask, k, n, status):
    lo, hi = proportion_confint(k, n, method="wilson")
    rows.append({"audience": audience, "ask": ask, "count": int(k), "n": int(n), "percent": round(100 * k / n, 1),
                 "ci_low": round(100 * lo, 1), "ci_high": round(100 * hi, 1), "status": status})


# ---- students: programs wanted
WANT = {"want_reusable_containers": ("Reusable containers (cups, clamshells, etc.)", "Already on the programs list*"),
        "want_fix_it_clinics": ("Fix-it clinics", "Not on the programs list"),
        "want_clothing_swaps": ("Clothing swaps", "Already on the programs list"),
        "want_sharing_shelf": ("Sharing shelf", "Not on the programs list"),
        "want_bottle_filling_stations": ("Bottle filling stations", "Already on the programs list"),
        "want_digital_sharing_platform": ("Digital sharing platform", "Not on the programs list")}
w = stud.dropna(subset=["want_n_selected"])
for c, (label, status) in WANT.items():
    add("Students", label, w[c].sum(), len(w), status)
newtype = w[["want_fix_it_clinics", "want_sharing_shelf", "want_digital_sharing_platform"]].max(axis=1)
add("Students", "At least one of: fix-it clinics / sharing shelf / digital platform", newtype.sum(), len(w), "Not on the programs list")
lm = stud.dropna(subset=["learn_more"])
add("Students", "Wants to learn more about reuse & reduction", lm.learn_more.sum(), len(lm), "Information")

# ---- staff: help requested and barriers (needs)
def code_help(t):
    if pd.isna(t): return np.nan
    t = t.replace("’", "'").lower()
    if "[email removed]" in t or "learn more" in t or t.startswith("yes"): return "Wants help"
    return "Other"
h = staff.assistance_text.map(code_help).dropna()
add("Staff", "Asked for help / more information", (h == "Wants help").sum(), len(h), "Staff request")
b = staff.barrier.dropna()
add("Staff", "Barrier: lack of awareness of reuse/sharing options", (b == "Lack of awareness about reuse/sharing options").sum(), len(b), "Staff need")
add("Staff", "Barrier: hard to find items / who has them", (b == "Difficulty finding available items or knowing who has them").sum(), len(b), "Staff need")
t = staff.teams_group.dropna()
add("Staff", "Not aware the Reuse Teams group exists", (t == "Not aware").sum(), len(t), "Staff need")

out = pd.DataFrame(rows)
out.to_csv("outputs/09_unmet_demand.csv", index=False)
pd.set_option("display.width", 220, "display.max_colwidth", 70)
print(out.drop(columns=["status"]).to_string(index=False))
print("\n* ASSUMPTION: the reuse program on the list is taken to cover reusable containers; confirm with the office.")

# ---- who wants the 'new type' programs? co-occurrence
nt = w[["want_fix_it_clinics", "want_sharing_shelf", "want_digital_sharing_platform"]]
print(f"\nStudents wanting 2+ of the three new-type programs: {(nt.sum(axis=1) >= 2).sum()} ({100*(nt.sum(axis=1) >= 2).mean():.0f}%); all three: {(nt.sum(axis=1) == 3).sum()}")
print("Overlap (share of those wanting row-program who also want column-program):")
print((nt.T.dot(nt) / nt.sum()).round(2).rename(index=lambda s: s[5:], columns=lambda s: s[5:]).to_string())
for camp in ["Campus A", "Campus B"]:
    x = w[w.campus == camp]
    print(f"{camp}: want >=1 new-type program {100*x[nt.columns].max(axis=1).mean():.0f}% (n={len(x)})")

# ---- write-ins, as stated (short, anonymized)
print("\nWrite-in requests (verbatim):")
for col in ["want_other_text", "learn_more_other_text", "impact_other_text"]:
    for v in stud[col].dropna():
        print(f"  [{col.replace('_other_text','')}] {v}")

# ---- chart
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.3, 1]})
s = out[(out.audience == "Students") & out.ask.isin([v[0] for v in WANT.values()])].sort_values("percent")
colmap = {"Already on the programs list": cs.NAVY, "Already on the programs list*": cs.SKY, "Not on the programs list": cs.FOREST}
a1.barh(s.ask, s.percent, color=[colmap[x] for x in s.status],
        xerr=[s.percent - s.ci_low, s.ci_high - s.percent], ecolor=cs.MID, capsize=3)
for y, (p, c) in enumerate(zip(s.percent, s["count"])):
    a1.text(s.ci_high.iloc[y] + 1, y, f"{p:.0f}% ({c})", va="center", fontsize=9)
a1.set_xlim(0, 85)
a1.set_xlabel(f"% of students who want it (n={len(w)}; bars = 95% confidence interval)")
a1.set_ylabel("Program requested")
a1.set_title("Students: programs they want")
from matplotlib.patches import Patch
a1.legend(handles=[Patch(color=cs.FOREST, label="Not on the programs list (candidate new)"),
                   Patch(color=cs.NAVY, label="Already on the programs list"),
                   Patch(color=cs.SKY, label="On the list*, probably covers it")], loc="upper center", bbox_to_anchor=(0.5, -0.14), fontsize=8)

st = out[out.audience == "Staff"].sort_values("percent")
a2.barh([f"{a} (n={n})" for a, n in zip(st.ask.str.replace("Barrier: ", "Barrier: ").str.wrap(32), st.n)], st.percent, color=cs.NAVY,
        xerr=[st.percent - st.ci_low, st.ci_high - st.percent], ecolor=cs.MID, capsize=3)
a2.set_xlim(0, 100)
a2.set_xlabel("% of staff who answered (bars = 95% CI)")
a2.set_ylabel("Need or request")
a2.set_title("Staff: stated needs and requests")
fig.suptitle("Unmet demand: what students and staff ask for", fontweight="bold")
fig.tight_layout(); fig.savefig("outputs/09_unmet_demand.png", dpi=150, bbox_inches="tight")
print("\nSaved outputs/09_unmet_demand.csv and outputs/09_unmet_demand.png")
