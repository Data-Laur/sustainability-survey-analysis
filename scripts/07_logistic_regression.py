"""Step 7: logistic regression - which students say they want to learn more about reuse and reduction?

Outcome: learn_more (1 = yes, 0 = no), students only.
Predictors (5): campus (B vs A), programs recognized (0-8), programs wanted (0-6),
                thinks reusables are high-impact (0/1), thinks composting is high-impact (0/1).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
import chart_style as cs
cs.apply()

d = pd.read_csv("data/clean.csv")
d = d[d.form == "student_form"].copy()
d["campus_B"] = (d.campus == "Campus B").astype(int)
cols = {"campus_B": "Campus B (vs. Campus A)",
        "known_n_selected": "Each additional program recognized (of 8)",
        "want_n_selected": "Each additional program wanted (of 6)",
        "impact_using_reusables": "Thinks reusables are high-impact",
        "impact_composting": "Thinks composting is high-impact"}
m = d[["learn_more"] + list(cols)].dropna().astype(float)
y, X = m["learn_more"], sm.add_constant(m[list(cols)])

events, nonevents = int(y.sum()), int((1 - y).sum())
print(f"Students in model: {len(m)} of {len(d)} (dropped {len(d)-len(m)} with missing answers)")
print(f"Said yes: {events}, said no: {nonevents}. Events per predictor: {min(events, nonevents)/len(cols):.1f} (rule of thumb: want >= 10)")

fit = sm.Logit(y, X).fit(disp=0)
ci = fit.conf_int()
out = pd.DataFrame({"predictor": [cols[c] for c in cols],
                    "odds_ratio": np.exp(fit.params[list(cols)]).values,
                    "ci_low": np.exp(ci.loc[list(cols), 0]).values,
                    "ci_high": np.exp(ci.loc[list(cols), 1]).values,
                    "p_value": fit.pvalues[list(cols)].values})
print("\n" + out.round(3).to_string(index=False))

# sample-size warnings for binary predictors
print("\nSample-size check for yes/no predictors (smallest group should be >= 10 on both outcomes):")
for c in ["campus_B", "impact_using_reusables", "impact_composting"]:
    t = pd.crosstab(m[c], m["learn_more"])
    print(f"  {cols[c]}: smaller group n={int(t.sum(axis=1).min())}, smallest cell n={int(t.values.min())}"
          + ("   <-- WARNING: thin" if t.values.min() < 10 else ""))

# fit and diagnostics
auc = stats.mannwhitneyu(fit.predict(X)[y == 1], fit.predict(X)[y == 0]).statistic / (events * nonevents)
base = max(events, nonevents) / len(m)
pred = (fit.predict(X) >= 0.5).astype(int)
print(f"\nModel fit: overall test p={fit.llr_pvalue:.3f}; pseudo R-squared={fit.prsquared:.3f}; AUC={auc:.2f} (0.5 = coin flip)")
print(f"Accuracy {100*(pred==y).mean():.0f}% vs. {100*base:.0f}% from always guessing 'yes'")
vif = pd.Series([variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])], index=[cols[c] for c in cols])
print("\nOverlap between predictors (VIF; >5 would be a concern):"); print(vif.round(2).to_string())

out.to_csv("outputs/07_logistic_results.csv", index=False)

# forest plot
o = out.iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.2))
sig = o.p_value < 0.05
ax.errorbar(o.odds_ratio, range(len(o)), xerr=[o.odds_ratio - o.ci_low, o.ci_high - o.odds_ratio], fmt="none",
            ecolor=cs.MID, capsize=4)
ax.scatter(o.odds_ratio, range(len(o)), c=np.where(sig, cs.FOREST, cs.NAVY), s=70, zorder=3)
ax.axvline(1, ls="--", color=cs.RED, lw=1)
ax.set_xscale("log")
ax.set_xticks([0.25, 0.5, 1, 2, 4]); ax.set_xticklabels(["0.25", "0.5", "1", "2", "4"])
ax.set_yticks(range(len(o)), o.predictor)
ax.set_xlabel("Odds ratio for 'yes, I want to learn more' (log scale; 1 = no effect)")
ax.set_ylabel("Predictor")
ax.set_title(f"What predicts students wanting to learn more?\n(n={len(m)}; bars = 95% confidence interval; green = p<0.05)")
fig.tight_layout(); fig.savefig("outputs/07_logistic_odds_ratios.png", dpi=150)
print("\nSaved outputs/07_logistic_results.csv and outputs/07_logistic_odds_ratios.png")
