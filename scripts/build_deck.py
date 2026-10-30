"""Build the findings deck (outputs/survey_findings_deck.pptx) from the charts and numbers produced in steps 3-11.

Re-run steps 03-09 first if the charts change. Colors match scripts/chart_style.py.
"""
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

NAVY, FOREST, LEAF = "344582", "34681E", "6EAC42"
SKY, RED, DARK, TINT, WHITE, GRAY = "0081C3", "BB3E3E", "2B2B2B", "EEF1F6", "FFFFFF", "6B6B6B"
HEAD, BODY = "Cambria", "Calibri"
W, H = 13.333, 7.5
OUT = "outputs/survey_findings_deck.pptx"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
cp = prs.core_properties
cp.title, cp.author, cp.last_modified_by, cp.comments = "Sustainability Festival Survey: Findings", "", "", ""
TITLE_ONLY = prs.slide_layouts[5]


def rgb(h):
    return RGBColor.from_string(h)


def bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(color)


def text(slide, x, y, w, h, paras, size=16, color=DARK, bold=False, font=BODY, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, bullets=False, space_after=0, name=None):
    """paras: str or list of str. Text box with no inner padding so edges line up with neighbours."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, p_text in enumerate([paras] if isinstance(paras, str) else paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = p_text
        r.font.size, r.font.bold, r.font.name = Pt(size), bold, font
        r.font.color.rgb = rgb(color)
        if bullets:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", "285750"); pPr.set("indent", "-285750")
            bu = etree.SubElement(pPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}buChar")
            bu.set("char", "•")
    return tb


def new_slide(title, dark=False, number=None):
    s = prs.slides.add_slide(TITLE_ONLY)
    bg(s, NAVY if dark else WHITE)
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.6), Inches(0.4), Inches(W - 1.2), Inches(0.95)
    tf = t.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    f = p.runs[0].font
    f.size, f.bold, f.name = Pt(34), True, HEAD
    f.color.rgb = rgb(WHITE if dark else NAVY)
    if number:
        text(s, W - 1.1, H - 0.5, 0.5, 0.3, str(number), size=11, color="C9D1E6" if dark else GRAY,
             align=PP_ALIGN.RIGHT, name="Slide number")
    return s


def picture(slide, path, x, y, w, alt):
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic


def card(slide, x, y, w, h, fill=TINT):
    c = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.adjustments[0] = 0.04
    c.fill.solid(); c.fill.fore_color.rgb = rgb(fill)
    c.line.fill.background()
    c.shadow.inherit = False
    return c


def notes(slide, body):
    slide.notes_slide.notes_text_frame.text = body


# ---------------------------------------------------------------- 1. Title
s = prs.slides.add_slide(TITLE_ONLY)
bg(s, NAVY)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(0.9), Inches(2.3), Inches(W - 1.8), Inches(1.6)
t.text_frame.word_wrap = True
t.text_frame.text = "Sustainability Festival Survey"
t.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
p = t.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
f = p.runs[0].font; f.size, f.bold, f.name = Pt(48), True, HEAD; f.color.rgb = rgb(WHITE)
text(s, 0.9, 4.15, W - 1.8, 0.5, "What 336 festival visitors told us, and what to do next", size=22, color="DDE3F3")
text(s, 0.9, 4.85, W - 1.8, 0.4, "Two festivals (Campus A and Campus B)  ·  273 students  ·  63 faculty and staff",
     size=16, color="AEB9D8")
notes(s, "Purpose: share the main findings from the two festival surveys and recommend three actions. "
         "Staff and students answered different questions, so findings are reported for each group separately.")

# ---------------------------------------------------------------- 2. Takeaway
s = new_slide("Awareness is the gap, not interest", number=2)
stats = [("60%", RED, "of staff have not heard of the Reuse Teams group (37 of 62)"),
         ("7 in 10", SKY, "students asking for bottle stations or clothing swaps already recognize them as existing programs"),
         ("76%", FOREST, "of students want at least one repair or sharing program that is not on today's list")]
for i, (big, col, label) in enumerate(stats):
    x = 0.6 + i * (3.85 + 0.3)
    card(s, x, 1.8, 3.85, 3.2)
    text(s, x + 0.35, 2.1, 3.15, 1.1, big, size=54, color=col, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.35, 3.4, 3.15, 1.4, label, size=17, color=DARK)
text(s, 0.6, 5.4, W - 1.2, 1.0,
     "Interest is high: 68% of students want to learn more. It does not depend on campus or on what they already know.",
     size=19, color=NAVY, bold=True)
notes(s, "Three headline numbers. (1) Staff: 37 of 62 not aware of the Reuse Teams group. "
         "(2) Students: of those wanting bottle filling stations, 72% already recognize them; for clothing swaps 67%. "
         "(3) Students: 204 of 270 chose at least one of fix-it clinics, sharing shelf, digital sharing platform (95% range 70-80%). "
         "Caveat: festival visitors chose to answer; students had a stamp-card incentive.")

# ---------------------------------------------------------------- 3. Who answered
s = new_slide("Who answered: mostly students", number=3)
picture(s, "outputs/03_representativeness.png", 1.07, 1.45, 11.2,
        "Bar charts comparing the share of students and staff in the survey sample with the school population, overall and by campus")
text(s, 0.6, 5.95, W - 1.2, 0.9,
     ["Staff are 19% of respondents but 23% of the school. The gap comes from Campus B: 21 staff, 13% of that sample.",
      "Visitors chose to take part, and students earned a stamp toward a free water bottle. Results describe engaged festival-goers."],
     size=15, color=DARK, space_after=6)
notes(s, "Overall role mix: 273 students (81.2%) and 63 staff (18.8%) against a school split of 76.8% / 23.2% (borderline, p = 0.053). "
         "Campus A matches the school almost exactly; Campus B over-represents students (86.8%, p = 0.003). "
         "Source: outputs/03_representativeness.png")

# ---------------------------------------------------------------- 4. Staff
s = new_slide("Staff don't know the Reuse Teams group", number=4)
picture(s, "outputs/06_staff_funnel.png", 0.6, 1.65, 7.3,
        "Bar chart: of 62 staff answering, 25 are aware of the Reuse Teams group, 17 have used it, and 11 asked for help")
rows = [("60%", RED, "have not heard of the group (37 of 62)"),
        ("1 in 3", NAVY, "of those who know it have never used it (8 of 25)"),
        ("6 of 11", FOREST, "staff who asked for help had never heard of the group")]
for i, (big, col, label) in enumerate(rows):
    y = 1.65 + i * 1.65
    text(s, 8.5, y, 4.3, 0.75, big, size=38, color=col, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 8.5, y + 0.8, 4.3, 0.7, label, size=16, color=DARK)
notes(s, "The group exists to solve the barrier staff name most: 56% (34 of 61) say lack of awareness of reuse/sharing options; "
         "36% (22) say it is hard to find items or who has them. 11 of the 21 who answered the help question asked for help or more information. "
         "Caveat: only 62 staff (21 at Campus B), margins of about +/-12 points; 'unsure' answers were common. Source: outputs/06_staff_funnel.png")

# ---------------------------------------------------------------- 5. Students ask for what exists
s = new_slide("Students ask for what already exists", number=5)
picture(s, "outputs/06_student_want_vs_recognized.png", 1.07, 1.45, 11.2,
        "Stacked bars: of students, share who want a program and recognize it, want it and do not, recognize it only, or neither, for bottle filling stations and clothing swaps")
text(s, 0.6, 6.05, W - 1.2, 0.85,
     "72% of students who want bottle stations and 67% who want clothing swaps already recognize them. "
     "The ask is likely for more locations or better visibility, not new programs.",
     size=15, color=DARK)
notes(s, "Paired test within the same students: wanting vs recognizing differs for bottle stations (p < 0.001) and clothing swaps (p = 0.007). "
         "The top request, reusable containers (58%), also overlaps: 83% of those asking recognize the reuse program, "
         "assuming that program covers containers (to confirm with the office). "
         "Caveat: the survey cannot separate 'wants more of it' from 'did not know it exists'. Source: outputs/06_student_want_vs_recognized.png")

# ---------------------------------------------------------------- 6. New ideas
s = new_slide("Three new ideas have real demand", number=6)
picture(s, "outputs/09_unmet_demand.png", 0.9, 1.4, 11.5,
        "Bar charts: percent of students wanting each program, and percent of staff reporting each need or request")
text(s, 0.6, 5.95, W - 1.2, 0.9,
     "76% of students (204 of 270) want at least one of fix-it clinics, a sharing shelf, or a digital sharing platform, "
     "which were not on the existing-programs list. Confirm none already exists before acting.",
     size=15, color=DARK)
notes(s, "34% of students want two or more of the three; 39 want all three. Same pattern at both campuses (72% at A, 79% at B; not significantly different). "
         "Staff say it is hard to find who has items (36%) and a third of students want a digital platform: a possible single tool for both groups (hypothesis). "
         "Caveat: ticking 'want' is cheap, so this is interest, not expected use. Source: outputs/09_unmet_demand.png")

# ---------------------------------------------------------------- 7. Interest
s = new_slide("Interest is broad, not predictable", number=7)
picture(s, "outputs/07_logistic_odds_ratios.png", 0.6, 1.7, 7.3,
        "Odds ratio chart: none of five factors clearly predicts whether a student wants to learn more")
text(s, 8.5, 1.6, 4.3, 1.0, "68%", size=54, color=FOREST, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
text(s, 8.5, 2.65, 4.3, 0.5, "of students want to learn more", size=17, color=DARK)
text(s, 8.5, 3.4, 4.3, 3.2,
     ["No factor we tested predicts who says yes",
      "Interested students know no more programs than others (4.1 vs 4.0 of 8)",
      "The two festivals look alike: no campus difference held up after correction"],
     size=16, color=DARK, bullets=True, space_after=10)
notes(s, "Logistic regression on 260 students (177 yes, 83 no) with five predictors. The model is no better than always guessing 'yes' "
         "(68% vs 68%; AUC 0.60). 23 campus comparisons were run; none survived correction for multiple testing. "
         "Implication: offer information to everyone instead of targeting a student type. "
         "Caveat: 'no effect found' can hide small effects. Source: outputs/07_logistic_odds_ratios.png, outputs/05_effect_sizes.png")

# ---------------------------------------------------------------- 8. Actions (dark)
s = new_slide("Recommended next steps", dark=True, number=8)
actions = [("1", FOREST, "Reach the staff who asked",
            "Contact the 11 staff who asked for help. Promote the Reuse Teams group in department channels."),
           ("2", SKY, "Make existing programs visible",
            "Add signs with locations and hours for bottle filling stations, clothing swaps and the reuse program."),
           ("3", RED, "Pilot one new idea",
            "Run a sharing shelf or one fix-it clinic day and count who shows up. Check first that neither already exists.")]
for i, (num, col, head, body) in enumerate(actions):
    x = 0.6 + i * (3.85 + 0.3)
    card(s, x, 1.75, 3.85, 4.5, fill=WHITE)
    circ = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.35), Inches(2.1), Inches(0.75), Inches(0.75))
    circ.fill.solid(); circ.fill.fore_color.rgb = rgb(col); circ.line.fill.background(); circ.shadow.inherit = False
    ctf = circ.text_frame; ctf.margin_left = ctf.margin_right = ctf.margin_top = ctf.margin_bottom = 0
    ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
    ctf.text = num
    cp_ = ctf.paragraphs[0]; cp_.alignment = PP_ALIGN.CENTER
    cf = cp_.runs[0].font; cf.size, cf.bold, cf.name = Pt(26), True, HEAD; cf.color.rgb = rgb(WHITE)
    text(s, x + 0.35, 3.1, 3.15, 0.9, head, size=22, color=NAVY, bold=True, font=HEAD)
    text(s, x + 0.35, 4.1, 3.15, 2.0, body, size=16, color=DARK)
notes(s, "Each action maps to a finding: (1) finding 1, staff awareness; (2) finding 3, visibility of existing programs; (3) finding 2, new-program demand. "
         "Track awareness and program use next year so the effect can be measured.")

# ---------------------------------------------------------------- 9. Limits & next year
s = new_slide("Limits and next year's survey", number=9)
text(s, 0.6, 1.7, 5.8, 0.5, "What to keep in mind", size=22, color=NAVY, bold=True, font=HEAD)
text(s, 0.6, 2.35, 5.8, 4.4,
     ["Visitors chose to answer, and students had a stamp-card incentive",
      "Staff and students answered different questions, so they can't be compared",
      "Only 62 staff, and 21 at Campus B",
      "No questions on what people actually do, only on awareness and interest"],
     size=17, color=DARK, bullets=True, space_after=12)
text(s, 6.9, 1.7, 5.8, 0.5, "Next year", size=22, color=FOREST, bold=True, font=HEAD)
text(s, 6.9, 2.35, 5.8, 4.4,
     ["Ask staff and students the same core questions",
      "Add behavior questions, such as how often people use reusables",
      "For each program ask: never heard of it, heard of it, or used it",
      "Record the campus directly and collect emails in a separate form"],
     size=17, color=DARK, bullets=True, space_after=12)
notes(s, "Full list of 14 limitations and the detailed suggestions are in outputs/11_limitations_and_next_year.md. "
         "Also: 28% of students ticked all four 'high-impact' options, so that question is a weak measure; text answers were mostly one word.")

prs.save(OUT)
print(f"Saved {OUT} with {len(prs.slides)} slides")
