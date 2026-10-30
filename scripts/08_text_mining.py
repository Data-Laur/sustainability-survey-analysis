"""Step 8 (lean): text mining of the open-ended questions + export of all open text (read-only on data/clean.csv).

Only three questions are truly open-ended and all are staff-only (Q3 items, Q4 current actions, Q6 help requests).
"Distinctive words by campus/role" is intentionally skipped: with ~40 mostly one-word answers it would only show noise.
Bars show raw counts; with so little text, many words tie at 1-2 mentions - read them as themes, not rankings.
"""
import re
from collections import Counter
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import chart_style as cs
cs.apply()

df = pd.read_csv("data/clean.csv")

QUESTIONS = {"items_text": "Q3: items that could be reduced/reused",
             "current_action_text": "Q4: what the department is doing now",
             "assistance_text": "Q6: help requests"}
WRITE_INS = {"impact_other_text": "Student write-in: biggest-impact activity",
             "want_other_text": "Student write-in: program wanted",
             "learn_more_other_text": "Student write-in: learning more",
             "barrier_other_text": "Staff write-in: barrier"}

STOP = set("""a about above after again all also am an and any are as at be because been before being below between both but by
can could did do does doing down during each few for from further had has have having he her here hers him his how i if in into
is it its itself just me more most my myself no nor not now of off on once only or other our ours out over own same she should
so some such than that the their them then there these they this those through to too under until up us very was we were what
yes please i'd i'm sure know need like can
when where which while who whom why will with would you your yours get got really still probably much many lot lots etc
con el la los las de del un una y en que por para vs""".split())
SURVEY_WORDS = {"reuse", "reusing", "reused", "reduce", "reducing", "reduction", "department", "dept", "sustainability",
                "sustainable", "waste", "zero", "item", "items", "campus", "university", "teams", "group", "order", "use", "using"}
SYNONYMS = {"stationaries": "stationery", "stationary": "stationery", "coffe": "coffee", "kcups": "kcup", "vasos": "cups",
            "pipettes": "pipette", "pipet": "pipette", "gloves": "glove"}
NON_ANSWER = re.compile(r"(no|na|n/?a|none|nope|yes|idk|i dk|i don'?t know|unsure|uncertain|not sure|i'?m not sure|i'?m not sire|"
                        r"not that i know|i am good|i'?m ok|no thank you|no thanks|not at this moment|actually,? i'?m not sure we are)")


def norm(t):
    return re.sub(r"\s+", " ", t.replace("’", "'").lower()).strip()


def is_non_answer(t):
    s = norm(t).replace("[email removed]", "").strip(" .!?,-")
    return s == "" or bool(NON_ANSWER.fullmatch(s))


def stem(w):
    w = SYNONYMS.get(w, w)
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def tokens(t, drop_survey):
    t = norm(t).replace("[email removed]", " ").replace("re use", "reuse").replace("re-use", "reuse")
    out = [stem(w) for w in re.findall(r"[a-z']+", t) if w not in STOP and len(w) > 1]
    if drop_survey:
        out = [w for w in out if w not in SURVEY_WORDS and stem(w) not in SURVEY_WORDS]
    return out


def count_terms(texts, drop_survey):
    words, phrases = Counter(), Counter()
    for t in texts:
        tk = tokens(t, drop_survey)
        words.update(tk)
        phrases.update(" ".join(p) for p in zip(tk, tk[1:]))
    return words, phrases


def barpanel(ax, counter, n, title, color):
    top = counter.most_common(n)[::-1]
    if not top:
        ax.text(0.5, 0.5, "No repeated terms", ha="center", transform=ax.transAxes)
    else:
        ax.barh([w for w, _ in top], [c for _, c in top], color=color)
        for y, (_, c) in enumerate(top):
            ax.text(c + 0.05, y, str(c), va="center", fontsize=8)
    ax.set_title(title, fontsize=10)


quotes = []
for col, qlabel in QUESTIONS.items():
    d = df[df[col].notna()]
    texts = d[col].tolist()
    informative = [t for t in texts if not is_non_answer(t)]
    print(f"\n==================== {qlabel} ====================")
    print(f"Answers: {len(texts)}; non-answers (no/na/unsure/yes only): {len(texts)-len(informative)}; mined: {len(informative)}")
    short = col.split("_")[0]
    res = {}
    for label, drop in [("with survey words", False), ("without survey words", True)]:
        res[label] = count_terms(informative, drop)
        w, p = res[label]
        print(f"\n  Top words ({label}): " + ", ".join(f"{k} {v}" for k, v in w.most_common(25)))
        p15 = [(k, v) for k, v in p.most_common(15) if v >= 1]
        print(f"  Top two-word phrases ({label}): " + (", ".join(f"{k} {v}" for k, v in p15) or "none"))
        rep = sum(1 for _, v in p.items() if v >= 2)
        print(f"  (phrases mentioned 2+ times: {rep})")
    for kind, idx, n, fname in [("words", 0, 25, f"08_{short}_top_words.png"), ("phrases", 1, 15, f"08_{short}_top_phrases.png")]:
        fig, axes = plt.subplots(1, 2, figsize=(11, 0.28 * n + 2))
        barpanel(axes[0], res["with survey words"][idx], n, "With survey words", cs.NAVY)
        barpanel(axes[1], res["without survey words"][idx], n, "Without survey words", cs.LEAF)
        for ax in axes:
            ax.set_xlabel("Number of mentions"); ax.set_ylabel("Word" if kind == "words" else "Two-word phrase")
        fig.suptitle(f"{qlabel}: top {kind} (n={len(informative)} informative answers)", fontweight="bold")
        fig.tight_layout(); fig.savefig(f"outputs/{fname}", dpi=150); plt.close(fig)
        print(f"  Saved outputs/{fname}")

    # example quotes: top terms (phrases first, else words), short answers only
    w, p = res["without survey words"]
    terms = [k for k, v in p.most_common(5) if v >= 2] or [k for k, _ in w.most_common(5)]
    print(f"\n  Example answers (<=20 words) for top terms:")
    for term in terms:
        hits = [t for t in informative if len(t.split()) <= 20 and all(stem(x) in tokens(t, False) or x in tokens(t, False) for x in term.split())]
        for t in hits[:5]:
            quotes.append({"question": qlabel, "term": term, "quote": t})
        print(f"   '{term}': " + (" | ".join(f'"{t}"' for t in hits[:5]) or "(none)"))

pd.DataFrame(quotes).to_csv("outputs/08_marketing_quotes.csv", index=False)

# ---- export all open text (for theming), with campus and role
rows = []
for col, label in {**QUESTIONS, **WRITE_INS}.items():
    d = df[df[col].notna()]
    for _, r in d.iterrows():
        rows.append({"id": r["id"], "campus": r["campus"], "role": r["role"], "question": label,
                     "text": r[col], "non_answer": is_non_answer(r[col])})
out = pd.DataFrame(rows).sort_values(["question", "id"])
out.to_csv("outputs/open_text.csv", index=False)
print(f"\nSaved outputs/open_text.csv: {len(out)} text answers "
      f"({int((~out.non_answer).sum())} informative) from {out.id.nunique()} respondents")
print(out.groupby(["question", "role"]).size().to_string())
print("Saved outputs/08_marketing_quotes.csv")
