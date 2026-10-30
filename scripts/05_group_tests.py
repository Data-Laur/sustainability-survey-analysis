"""Step 5: chi-square tests + Cramer's V, by campus (and role x campus), with small-cell warnings.

Role cannot be compared on survey questions: staff and students answered different questions.
The only role test possible is whether the role mix differs between campuses.
Because ~20 tests are run, p-values are also adjusted (Benjamini-Hochberg) so chance findings are not oversold.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.multitest import multipletests
import chart_style as cs
cs.apply()

df = pd.read_csv("data/clean.csv")
staff, stud = df[df.form == "staff_form"].copy(), df[df.form == "student_form"].copy()
staff["barrier3"] = staff["barrier"].replace({"The cost of transporting items around campus": "Cost / other",
                                              "Other": "Cost / other"})
results = []


def test(name, data, var, group="campus"):
    d = data[[var, group]].dropna()
    tab = pd.crosstab(d[group], d[var])
    chi2, p, dof, exp = stats.chi2_contingency(tab, correction=False)
    n = tab.values.sum()
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))
    min_exp = exp.min()
    pct_small = (exp < 5).mean() * 100
    note = ""
    p_use = p
    if tab.shape == (2, 2) and min_exp < 5:
        p_use = stats.fisher_exact(tab.values)[1]
        note = "small cells -> Fisher exact p"
    elif min_exp < 5 and (pct_small > 20 or min_exp < 1):
        note = "TOO SMALL: >20% of cells expected <5"
    elif min_exp < 5:
        note = "some cells expected <5, caution"
    size = "negligible" if v < 0.1 else "small" if v < 0.3 else "medium" if v < 0.5 else "large"
    results.append({"test": name, "n": n, "chi2": chi2, "p": p_use, "cramers_v": v, "effect": size,
                    "min_expected_cell": min_exp, "flag": note})


# ---- staff by campus
test("Staff: barrier x campus", staff, "barrier3")
staff["teams3"] = staff["teams_group"]
test("Staff: Reuse Teams awareness x campus", staff, "teams3")
staff["aware_any"] = staff["teams_group"].map({"Not aware": "No", "Aware, not used": "Yes", "Used it": "Yes"})
test("Staff: aware of Teams group (yes/no) x campus", staff, "aware_any")

# ---- students by campus: every 0/1 option column and learn_more
for c in stud.columns:
    if c.startswith(("impact_", "known_", "want_")) and not c.endswith(("_text", "_n_selected")):
        grp = {"impact_": "Impact", "known_": "Recognized", "want_": "Wanted"}[c.split("_")[0] + "_"]
        test(f"Students {grp}: {c.split('_', 1)[1].replace('_', ' ')} x campus", stud, c)
test("Students: interested in learning more x campus", stud, "learn_more")

# ---- role x campus (composition)
test("Role mix x campus (all respondents)", df, "role")

res = pd.DataFrame(results)
res["p_adj_BH"] = multipletests(res["p"], method="fdr_bh")[1]
res["significant_after_adjust"] = np.where(res["p_adj_BH"] < 0.05, "YES", "no")
res.to_csv("outputs/05_group_tests.csv", index=False)

pd.set_option("display.width", 250, "display.max_colwidth", 60)
show = res.copy()
for c in ["chi2", "cramers_v", "min_expected_cell"]:
    show[c] = show[c].round(2)
show["p"] = show["p"].round(3)
show["p_adj_BH"] = show["p_adj_BH"].round(3)
print(show[["test", "n", "p", "p_adj_BH", "cramers_v", "effect", "min_expected_cell", "flag", "significant_after_adjust"]]
      .to_string(index=False))
print(f"\n{len(res)} tests run. Raw p<0.05: {(res.p < 0.05).sum()}. Still significant after adjusting for many tests: "
      f"{(res.p_adj_BH < 0.05).sum()}. Expected by pure chance at 5%: ~{0.05 * len(res):.0f}.")

# ---- chart: effect size of every test
r = res.sort_values("cramers_v")
colors = np.where(r["flag"].str.startswith("TOO SMALL"), cs.LIGHT,
                  np.where(r["p_adj_BH"] < 0.05, cs.RED, np.where(r["p"] < 0.05, cs.SKY, cs.MID)))
fig, ax = plt.subplots(figsize=(10, 0.36 * len(r) + 2))
ax.barh(r["test"], r["cramers_v"], color=colors)
ax.axvline(0.1, ls="--", color="gray", lw=0.8)
ax.text(0.101, -0.9, "small effect (0.1)", fontsize=8, color="gray")
ax.set_xlabel("Cramer's V (effect size: 0 = no difference between campuses, 1 = complete)")
ax.set_ylabel("Comparison (Campus A vs. Campus B unless noted)")
ax.set_title("Campus differences: how big are they? (red = holds up after adjustment, blue = p<0.05 only,\n"
             "gray = not significant, light gray = counts too small to trust)")
fig.tight_layout()
fig.savefig("outputs/05_effect_sizes.png", dpi=150)
print("Saved outputs/05_group_tests.csv and outputs/05_effect_sizes.png")
