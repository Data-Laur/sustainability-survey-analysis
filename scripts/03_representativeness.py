"""Step 3: compare the sample's role mix to the school's actual split (read-only on data/clean.csv)."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.proportion import proportion_confint
import chart_style as cs
cs.apply()

POP = {"Student": 0.768, "Faculty/Staff": 0.232}
df = pd.read_csv("data/clean.csv")


def compare(d, label):
    n = len(d)
    obs = d["role"].value_counts().reindex(POP.keys()).fillna(0)
    exp = pd.Series(POP) * n
    chi2, p = stats.chisquare(obs, exp)
    rows = []
    for role in POP:
        lo, hi = proportion_confint(obs[role], n, method="wilson")
        rows.append({"group": label, "role": role, "n": int(obs[role]), "sample_%": 100 * obs[role] / n,
                     "ci_low_%": 100 * lo, "ci_high_%": 100 * hi, "school_%": 100 * POP[role],
                     "expected_n": exp[role], "weight": POP[role] / (obs[role] / n) if obs[role] else np.nan})
    print(f"\n=== {label} (n={n}) ===")
    print(pd.DataFrame(rows).drop(columns="group").round(1).to_string(index=False))
    print(f"Chi-square goodness-of-fit: chi2={chi2:.2f}, p={p:.3f}")
    return pd.DataFrame(rows), p


all_rows, p_all = compare(df, "All respondents")
a_rows, p_a = compare(df[df.campus == "Campus A"], "Campus A")
b_rows, p_b = compare(df[df.campus == "Campus B"], "Campus B")

# --- chart: sample share (with 95% CI) vs school share, overall and by campus
res = pd.concat([all_rows, a_rows, b_rows])
fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), sharey=True)
for ax, (label, g) in zip(axes, res.groupby("group", sort=False)):
    x = np.arange(len(g))
    ax.bar(x - 0.2, g["sample_%"], 0.4, label="Survey sample", color=cs.NAVY,
           yerr=[g["sample_%"] - g["ci_low_%"], g["ci_high_%"] - g["sample_%"]], capsize=4)
    ax.bar(x + 0.2, g["school_%"], 0.4, label="School population", color=cs.LIGHT)
    ax.set_xticks(x, g["role"])
    ax.set_title(f"{label} (n={g['n'].sum()})")
    ax.set_xlabel("Role")
    for xi, v in zip(x - 0.2, g["sample_%"]):
        ax.text(xi, v + 5.5, f"{v:.0f}%", ha="center", fontsize=9)
axes[0].set_ylabel("Share of group (%)")
axes[0].set_ylim(0, 100)
axes[0].legend(loc="upper right")
fig.suptitle("Survey sample vs. school population by role (error bars: 95% confidence interval)")
fig.tight_layout()
fig.savefig("outputs/03_representativeness.png", dpi=150)
print("\nSaved outputs/03_representativeness.png")
