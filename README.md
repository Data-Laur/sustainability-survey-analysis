# Sustainability Festival Survey Analysis

An analysis of a 336-response survey collected at two university sustainability festivals (anonymized as Campus A and Campus B). The goal was a few defensible, non-obvious findings for a short slide deck, not a tour of every count.

**Result:** the audience is interested; the gap is awareness. Slides: [`outputs/survey_findings_deck.pptx`](outputs/survey_findings_deck.pptx).

## What the data looks like

- 336 usable responses (after removing one test row): 273 students, 63 faculty and staff.
- **Two different surveys under one title.** The form branched by role. Staff answered department questions; students answered questions about campus programs. No question was shared, so staff and students cannot be compared, and most "missing" values are structural, not non-response. Every analysis here is run within a role.

## Key findings

1. **Staff don't know the Reuse Teams group exists.** 60% are unaware (37 of 62), and 6 of the 11 who asked for help had never heard of it.
2. **76% of students want at least one repair-or-share program** (fix-it clinic, sharing shelf, digital platform) that wasn't on the list of existing programs (95% interval 70-80%).
3. **Much of the "demand" is for things students already recognize.** 72% of those wanting bottle filling stations already recognize them as existing (paired test p < 0.001); 67% for clothing swaps (p = 0.007).
4. **Interest in learning more (68%) is broad and unpredictable.** A five-predictor logistic regression does no better than always guessing "yes" (AUC 0.60).
5. **Students rate recycling as high-impact as reusables (77% each), and reducing paper least (36%).** This is the weakest measure, since 28% ticked every option.

Full write-up with evidence, actions and caveats: [`outputs/10_top_findings.md`](outputs/10_top_findings.md). Limitations and survey improvements for next year: [`outputs/11_limitations_and_next_year.md`](outputs/11_limitations_and_next_year.md).

## Method choices worth noting

- **Representativeness first.** The sample's role mix (81% students) was compared with the population (77%) using a goodness-of-fit test; the gap comes almost entirely from Campus B.
- **Effect sizes, not just p-values.** Group comparisons use chi-square with Cramer's V and flag cells with small expected counts.
- **Multiple-testing correction.** 23 campus comparisons were run; four had p < 0.05, but none survived Benjamini-Hochberg adjustment (about one was expected by chance). The conclusion is that the two festivals look alike.
- **Gap analysis with paired tests** (McNemar) to compare "wants it" and "recognizes it" within the same students.
- **Logistic regression with sample-size checks:** events per predictor, smallest-cell counts, and multicollinearity (VIF). The honest result was a null.
- **Text mining kept deliberately lean.** Only three questions were open-ended (all staff, 22-44 mostly one-word answers), so word lists are reported as themes, and campus-specific "distinctive words" were skipped as noise.

## Code and reproducibility

The respondent-level data is **not published**, to protect respondents and the institution. The repository contains the code, the aggregate results and the write-ups; the scripts cannot be re-run without the data.

```
pip install -r requirements.txt
python scripts/01_inspect.py            # reads the raw export (not included)
python scripts/02_clean.py              # raw export -> data/clean.csv (also uses two private lookup files)
python scripts/03_representativeness.py # steps 03-09 read data/clean.csv
python scripts/04_descriptives.py
python scripts/05_group_tests.py
python scripts/06_gap_analysis.py
python scripts/07_logistic_regression.py
python scripts/08_text_mining.py
python scripts/09_unmet_demand.py
python scripts/build_deck.py
```

Run from the repository root. Chart colors are set in `scripts/chart_style.py`. The cleaning script documents every decision (test-row removal, campus from date, structural blanks, multi-select splitting, redaction).

## Data and privacy

- Campuses are labelled Campus A and Campus B; the school is not named.
- The published outputs are charts, summary tables and write-ups only. No individual responses, free-text answers, or contact details are included.

## Repository layout

```
scripts/              one script per analysis step (01-09), plus chart_style.py and build_deck.py
outputs/              charts (.png), summary tables (.csv), write-ups (.md), slide deck (.pptx)
```

## License

MIT (see `LICENSE`).

## How this was made

This analysis was built with AI assistance (Claude Code). Claude Code wrote the code and first drafts of the write-ups. I set the questions, the cleaning rules and the privacy constraints, reviewed each step's results, and decided what to keep and how to present it.
