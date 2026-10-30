"""Step 6: gap analysis - intending/wanting vs. doing, and wanting/using vs. knowing (read-only on data/clean.csv).

Staff free-text is coded with simple, visible rules (see NOT_DOING and WANTS_HELP below).
"""
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
import chart_style as cs
cs.apply()

df = pd.read_csv("data/clean.csv")
staff, stud = df[df.form == "staff_form"].copy(), df[df.form == "student_form"].copy()
pd.set_option("display.width", 200)

# ============ STAFF ============
NOT_DOING = re.compile(r"^(no|na|n/a|nope|none)\b|not sure|unsure|uncertain|idk|don'?t know|not that i know|i'?m not sire", re.I)
def code_action(t):
    if pd.isna(t): return np.nan
    t = t.replace("’", "'").strip()
    return "No / unsure" if NOT_DOING.search(t) else "Doing something"

def code_help(t):
    if pd.isna(t): return np.nan
    t = t.replace("’", "'").lower()
    if "[email removed]" in t or "learn more" in t or t.startswith("yes"): return "Wants help"
    if t.strip(" .!") == "awareness": return "Unclear"
    return "No thanks"

staff["action"] = staff["current_action_text"].map(code_action)
staff["help"] = staff["assistance_text"].map(code_help)

print("=== STAFF ===")
n = staff.teams_group.notna().sum()
vc = staff.teams_group.value_counts()
aware = vc.get("Aware, not used", 0) + vc.get("Used it", 0)
print(f"\nA. Awareness funnel (n={n}): aware {aware} ({100*aware/n:.0f}%) -> used {vc.get('Used it',0)} ({100*vc.get('Used it',0)/n:.0f}%)")
print(f"   Of the {aware} who know the group, {vc.get('Aware, not used',0)} ({100*vc.get('Aware, not used',0)/aware:.0f}%) never used it.")

print("\nB. Staff who asked for help, by awareness of the Teams group (the people asking for help from a group they don't know):")
hb = pd.crosstab(staff.teams_group, staff.help).reindex(["Not aware", "Aware, not used", "Used it"])
print(hb.to_string()); print(f"   Coded answers: {staff.help.notna().sum()}  (coding rule printed in script)")
wants = staff[staff.help == "Wants help"]
print(f"   Staff wanting help: {len(wants)}; of them NOT aware of the group: {(wants.teams_group=='Not aware').sum()}")

print("\nC. Reports doing something (Q4) by awareness of the Teams group:")
ab = pd.crosstab(staff.teams_group, staff.action).reindex(["Not aware", "Aware, not used", "Used it"])
print(ab.to_string())
used = staff[staff.teams_group == "Used it"]
print(f"   Even among the {used.action.notna().sum()} who used the group and answered, {(used.action=='No / unsure').sum()} say they are not (or unsure they are) reducing/reusing.")

print("\nD. Barrier by awareness (counts):")
print(pd.crosstab(staff.barrier, staff.teams_group).to_string())

# chart: staff funnel
fig, ax = plt.subplots(figsize=(8, 4.2))
steps = ["Staff answering", "Aware of Teams group", "Have used it", "Asked for help\n(of those who answered)"]
vals = [n, aware, vc.get("Used it", 0), len(wants)]
bars = ax.bar(steps, vals, color=[cs.LIGHT, cs.NAVY, cs.FOREST, cs.LEAF])
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v}", ha="center")
ax.set_ylabel("Number of staff respondents")
ax.set_xlabel("Step")
ax.set_title("Staff: from hearing about the Reuse Teams group to using it")
fig.tight_layout(); fig.savefig("outputs/06_staff_funnel.png", dpi=150); plt.close(fig)

# ============ STUDENTS ============
print("\n=== STUDENTS ===")
s = stud.dropna(subset=["known_reuse_program", "want_fix_it_clinics"]).copy()
rows, plot = [], {}
for name, kc, wc in [("Bottle filling stations", "known_bottle_filling_stations", "want_bottle_filling_stations"),
                     ("Clothing swaps", "known_clothing_swaps", "want_clothing_swaps")]:
    t = pd.crosstab(s[wc], s[kc]).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    wr, wnr, nwr, nn = t.loc[1, 1], t.loc[1, 0], t.loc[0, 1], t.loc[0, 0]
    wanters = wr + wnr
    p = mcnemar(t.values, exact=True).pvalue
    print(f"\nE. {name} (n={len(s)}): want {wanters} ({100*wanters/len(s):.0f}%), recognize it as existing {wr+nwr} ({100*(wr+nwr)/len(s):.0f}%)")
    print(f"   Of those who WANT it: {wr} ({100*wr/wanters:.0f}%) already recognize it as a campus program; {wnr} ({100*wnr/wanters:.0f}%) do not.")
    print(f"   Want vs. recognize differ within the same people? McNemar p={p:.3f}")
    plot[name] = [100 * wr / len(s), 100 * wnr / len(s), 100 * nwr / len(s), 100 * nn / len(s)]

# possible overlap, flagged as an assumption
w = s[s.want_reusable_containers == 1]
print(f"\nF. [ASSUMPTION - the reuse program may already offer reusable containers] Of {len(w)} who want reusable containers, "
      f"{int(w.known_reuse_program.sum())} ({100*w.known_reuse_program.mean():.0f}%) recognize the reuse program.")

fig, ax = plt.subplots(figsize=(9, 3.6))
cats = ["Wants it + recognizes it", "Wants it, does NOT recognize it", "Recognizes it, doesn't want it", "Neither"]
cols = [cs.FOREST, cs.RED, cs.SKY, cs.LIGHT]
left = np.zeros(len(plot))
for i, (cat, col) in enumerate(zip(cats, cols)):
    v = np.array([plot[k][i] for k in plot])
    ax.barh(list(plot), v, left=left, color=col, label=cat)
    for y, (l, x) in enumerate(zip(left, v)):
        if x > 4: ax.text(l + x / 2, y, f"{x:.0f}%", ha="center", va="center", color="white" if i < 3 else "black", fontsize=9)
    left += v
ax.set_xlabel(f"% of student respondents (n={len(s)})"); ax.set_ylabel("Program")
ax.set_title("Students: asking for programs vs. recognizing them as existing")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2, fontsize=8)
fig.tight_layout(); fig.savefig("outputs/06_student_want_vs_recognized.png", dpi=150); plt.close(fig)

# interest vs. recognition
t = stud.dropna(subset=["learn_more", "known_n_selected"])
yes, no = t[t.learn_more == 1].known_n_selected, t[t.learn_more == 0].known_n_selected
u = stats.mannwhitneyu(yes, no)
print(f"\nG. Programs recognized (of 8): interested in learning more = {yes.mean():.1f} (n={len(yes)}), not interested = {no.mean():.1f} (n={len(no)}); Mann-Whitney p={u.pvalue:.3f}")
low = (t.known_n_selected <= 3)
seg = ((t.learn_more == 1) & low).sum()
print(f"   'Interested but know few programs' (wants to learn, recognizes 3 or fewer of 8): {seg} students = {100*seg/len(t):.0f}% of students; {100*seg/(t.learn_more==1).sum():.0f}% of the interested.")

fig, ax = plt.subplots(figsize=(8, 4.2))
dist = pd.crosstab(t.learn_more.map({1: "Interested in learning more", 0: "Not interested"}), t.known_n_selected, normalize="index") * 100
dist = dist.reindex(columns=range(0, 9), fill_value=0)
for lab, col in [("Interested in learning more", cs.FOREST), ("Not interested", cs.MID)]:
    ax.plot(dist.columns, dist.loc[lab], marker="o", color=col, label=f"{lab} (n={(t.learn_more == (1 if lab[0]=='I' else 0)).sum()})")
ax.set_xlabel("Number of programs recognized (out of 8)"); ax.set_ylabel("% of students in the group")
ax.set_title("Students: do those who want to learn more already know the programs?")
ax.legend(); fig.tight_layout(); fig.savefig("outputs/06_student_interest_vs_recognition.png", dpi=150); plt.close(fig)

# belief gap
imp = stud.dropna(subset=["impact_recycling"])
print(f"\nH. Belief: {100*imp.impact_recycling.mean():.0f}% picked recycling as high-impact vs {100*imp.impact_reducing_printing_paper.mean():.0f}% reducing paper. "
      f"{int((imp.impact_n_selected==4).sum())} students ({100*(imp.impact_n_selected==4).mean():.0f}%) picked all four.")
print("\nSaved outputs/06_staff_funnel.png, 06_student_want_vs_recognized.png, 06_student_interest_vs_recognition.png")
