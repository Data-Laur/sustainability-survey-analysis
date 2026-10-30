"""Step 4: distributions of every closed-ended question, overall and by campus (read-only on data/clean.csv).

Role is not a comparison dimension here: staff and students were asked different questions,
so each question belongs to exactly one role. We therefore split by campus within each role.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/clean.csv")
staff, stud = df[df.form == "staff_form"], df[df.form == "student_form"]
import chart_style as cs
cs.apply()
COLORS = {"Overall": cs.LIGHT, "Campus A": cs.NAVY, "Campus B": cs.LEAF}
rows = []


def label(col, prefix):
    return col[len(prefix):].replace("_", " ").capitalize()


def pct_by_group(data, cols, names):
    """% of respondents (with a valid answer) choosing each option, overall and per campus."""
    out = {}
    for g, d in [("Overall", data), ("Campus A", data[data.campus == "Campus A"]),
                 ("Campus B", data[data.campus == "Campus B"])]:
        out[g] = pd.Series({n: 100 * d[c].mean() for c, n in zip(cols, names)})
        out[g + " n"] = d[cols[0]].notna().sum()
    return out


def chart(res, title, fname, xlabel, role_label):
    items = res["Overall"].sort_values()
    idx = items.index
    fig, ax = plt.subplots(figsize=(9, 0.55 * len(idx) + 2))
    h, y = 0.26, np.arange(len(idx))
    for k, g in enumerate(["Overall", "Campus A", "Campus B"]):
        ax.barh(y + (k - 1) * h, res[g][idx], h, color=COLORS[g], label=f"{g} (n={res[g + ' n']})")
        for yi, v in zip(y + (k - 1) * h, res[g][idx]):
            ax.text(v + 0.8, yi, f"{v:.0f}%", va="center", fontsize=8)
    ax.set_yticks(y, idx)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(role_label)
    ax.set_xlim(0, max(res["Overall"].max(), res["Campus A"].max(), res["Campus B"].max()) + 12)
    ax.set_title(title)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(f"outputs/{fname}", dpi=150)
    plt.close(fig)
    print(f"Saved outputs/{fname}")


def record(question, res):
    for g in ["Overall", "Campus A", "Campus B"]:
        for opt, v in res[g].items():
            rows.append({"question": question, "group": g, "n": res[g + " n"], "option": opt, "percent": round(v, 1)})


# ---------- STAFF: single-choice questions
for col, order, qname, title, fname in [
    ("barrier", None, "Staff: biggest barrier",
     "Staff: biggest barrier to reducing/reusing in their department", "04_staff_barrier.png"),
    ("teams_group", ["Not aware", "Aware, not used", "Used it"], "Staff: Reuse Teams group awareness",
     "Staff: awareness and use of the Reuse Teams group", "04_staff_teams_group.png"),
]:
    d = staff[staff[col].notna()]
    dummies = pd.get_dummies(d[col]).astype(float)
    dummies[col + "_valid"] = 1.0
    names = order or list(d[col].value_counts().index)
    d2 = pd.concat([d[["campus"]], dummies], axis=1)
    res = pct_by_group(d2, names, names)
    for g, sub in [("Overall", d2), ("Campus A", d2[d2.campus == "Campus A"]), ("Campus B", d2[d2.campus == "Campus B"])]:
        res[g + " n"] = len(sub)
    res = {k: (v if not isinstance(v, pd.Series) else v.rename(lambda s: s.replace("Lack of awareness about reuse/sharing options", "Lack of awareness of options")
           .replace("Difficulty finding available items or knowing who has them", "Hard to find items / who has them")
           .replace("The cost of transporting items around campus", "Cost of transporting items"))) for k, v in res.items()}
    record(qname, res)
    print(f"\n{qname}"); print(pd.DataFrame({g: res[g] for g in ["Overall", "Campus A", "Campus B"]}).round(0).to_string())
    print("n:", {g: res[g + " n"] for g in ["Overall", "Campus A", "Campus B"]})
    chart(res, title, fname, "% of staff respondents answering", "Answer")

# ---------- STUDENTS: multi-select questions (each option is a 0/1 column) and learn_more
for prefix, qname, title, fname in [
    ("impact_", "Students: biggest-impact activities", "Students: activities believed to have the biggest Zero Waste impact", "04_student_impact.png"),
    ("known_", "Students: programs recognized", "Students: which items they picked as campus reuse/reduction programs", "04_student_known.png"),
    ("want_", "Students: programs wanted", "Students: reuse/reduction programs they would like to see", "04_student_wanted.png"),
]:
    cols = [c for c in stud.columns if c.startswith(prefix) and not c.endswith(("_text", "_n_selected"))]
    names = [label(c, prefix) for c in cols]
    res = pct_by_group(stud[stud[cols[0]].notna()], cols, names)
    record(qname, res)
    print(f"\n{qname}"); print(pd.DataFrame({g: res[g] for g in ["Overall", "Campus A", "Campus B"]}).round(0).to_string())
    print("n:", {g: res[g + " n"] for g in ["Overall", "Campus A", "Campus B"]})
    chart(res, title, fname, "% of student respondents selecting the option", "Option")
    ns = stud[prefix + "n_selected"].dropna()
    print(f"Options selected per student: median {ns.median():.0f}, mean {ns.mean():.1f}, 0 selected: {(ns == 0).sum()}")

s = stud[stud.learn_more.notna()].copy()
s["tmp"] = s.learn_more
res = {}
for g, d in [("Overall", s), ("Campus A", s[s.campus == "Campus A"]), ("Campus B", s[s.campus == "Campus B"])]:
    res[g] = pd.Series({"Yes": 100 * d.tmp.mean(), "No": 100 * (1 - d.tmp.mean())})
    res[g + " n"] = len(d)
record("Students: interested in learning more", res)
print("\nStudents: interested in learning more"); print(pd.DataFrame({g: res[g] for g in ["Overall", "Campus A", "Campus B"]}).round(0).to_string())
print("n:", {g: res[g + " n"] for g in ["Overall", "Campus A", "Campus B"]})
chart(res, "Students: interested in learning more about reuse and reduction?", "04_student_learn_more.png",
      "% of student respondents answering", "Answer")

pd.DataFrame(rows).to_csv("outputs/04_descriptives.csv", index=False)
print("\nSaved outputs/04_descriptives.csv (all percentages in one table)")
