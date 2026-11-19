"""Builds presentation/anTSP_presentation.pptx (needs: pip install python-pptx).

    python presentation/make_assets.py   # pictures + animation (once)
    python presentation/build_deck.py

The speaker script of every slide is stored in the slide notes (and in presentation/script.md).
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = HERE / "assets"
PLOTS = ROOT / "results" / "experiments" / "full" / "plots"
OUT = HERE / "anTSP_presentation.pptx"

INK = RGBColor(0x1B, 0x1B, 0x1A)
MUTED = RGBColor(0x6B, 0x6A, 0x66)
TINT = RGBColor(0xF3, 0xF2, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x14, 0x14, 0x13)
DARK_TEXT = RGBColor(0xC3, 0xC2, 0xB7)
ORANGE = RGBColor(0xEB, 0x68, 0x34)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
GREEN = RGBColor(0x1F, 0x9D, 0x5C)
RED = RGBColor(0xE3, 0x49, 0x48)

HEAD = "Arial"
BODY = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
slide_count = 0


# ---------- helpers ----------

def new_slide(dark=False):
    global slide_count
    slide_count += 1
    slide = prs.slides.add_slide(BLANK)
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = DARK if dark else WHITE
    if slide_count > 1:
        text(slide, 12.2, 7.0, 0.6, 0.3, str(slide_count), size=11, color=MUTED, align=PP_ALIGN.RIGHT)
    return slide


def text(slide, x, y, w, h, paragraphs, size=16, color=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=6, line_spacing=None, name=None):
    """paragraphs: str, or list of paragraphs; a paragraph is a str or a list of (text, options) runs."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, 0)
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    for index, paragraph in enumerate(paragraphs):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line_spacing:
            p.line_spacing = line_spacing
        runs = [(paragraph, {})] if isinstance(paragraph, str) else paragraph
        for run_text, options in runs:
            run = p.add_run()
            run.text = run_text
            run.font.name = options.get("font", font)
            run.font.size = Pt(options.get("size", size))
            run.font.bold = options.get("bold", bold)
            run.font.italic = options.get("italic", False)
            run.font.color.rgb = options.get("color", color)
    return box


def shape(slide, kind, x, y, w, h, fill, line=None, name=None):
    item = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    item.fill.solid()
    item.fill.fore_color.rgb = fill
    if line is None:
        item.line.fill.background()
    else:
        item.line.color.rgb = line
    item.shadow.inherit = False
    if name:
        item.name = name
    return item


def card(slide, x, y, w, h, name=None):
    item = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, TINT, name=name)
    item.adjustments[0] = 0.08
    return item


def dot(slide, x, y, size, color, label=None, label_size=14):
    circle = shape(slide, MSO_SHAPE.OVAL, x, y, size, size, color)
    if label:
        frame = circle.text_frame
        for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(frame, side, 0)
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        run.font.size = Pt(label_size)
        run.font.bold = True
        run.font.name = HEAD
        run.font.color.rgb = WHITE
    return circle


def header(slide, kicker, title, color, dark=False):
    """The motif: a colored dot + small kicker label above every title."""
    dot(slide, 0.6, 0.52, 0.16, color)
    text(slide, 0.88, 0.45, 8, 0.3, kicker.upper(), size=12, bold=True, color=color, font=HEAD)
    text(slide, 0.6, 0.82, 12.1, 0.9, title, size=34, bold=True, color=WHITE if dark else INK, font=HEAD,
         name="Title")


def picture(slide, path, x, y, w=None, h=None, name=None):
    kwargs = {}
    if w is not None:
        kwargs["width"] = Inches(w)
    if h is not None:
        kwargs["height"] = Inches(h)
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kwargs)
    if name:
        pic.name = name
    return pic


def stat(slide, x, y, w, number, label, color, number_size=40):
    text(slide, x, y, w, 0.75, number, size=number_size, bold=True, color=color, font=HEAD)
    text(slide, x, y + 0.8, w, 0.9, label, size=14, color=INK)


def notes(slide, speaker, minutes, script):
    slide.notes_slide.notes_text_frame.text = f"[{speaker} · ~{minutes}]\n\n{script.strip()}"


def caption(slide, x, y, w, words):
    text(slide, x, y, w, 0.3, words, size=11, color=MUTED)


# ---------- slides ----------

SCRIPT = {}  # filled below, also written to script.md


WORDS_PER_MINUTE = 130  # calm presenting pace
TECH_NOTES = {7: "Tech note (not to be read out): the animation is a GIF and plays in PowerPoint and Google Slides "
                 "in presentation mode. If it does not, insert presentation/assets/simulation.mp4 or run "
                 "'python anTSP.py --seed 30 --algo-seed 4 -s 6' live."}


def add(number, speaker, _estimate, script):
    """The time of every slide is computed from its word count."""
    seconds = round(len(script.split()) / WORDS_PER_MINUTE * 60 / 5) * 5
    SCRIPT[number] = (speaker, f"{seconds // 60}:{seconds % 60:02d}", script.strip())


# 1 - title
s = new_slide(dark=True)
picture(s, ASSETS / "simulation_last_frame.png", 7.15, 1.1, w=5.6, name="Simulator screenshot")
dot(s, 0.6, 1.62, 0.16, ORANGE)
dot(s, 0.85, 1.62, 0.16, BLUE)
text(s, 0.6, 1.95, 6.4, 1.8, ["Ants vs.", "Brute Force"], size=48, bold=True, color=WHITE, font=HEAD,
     space_after=0)
text(s, 0.6, 3.85, 6.2, 1.2, "Solving the Travelling Salesman Problem with Ant Colony Optimization, "
                             "and checking it against exact algorithms", size=20, color=DARK_TEXT)
text(s, 0.6, 5.3, 6.2, 1.0, [[("Wiktoria PARZYCH  ·  Jordy GODJO  ·  Rita GAYITMAZOVA", {"bold": True})]],
     size=16, color=WHITE)
text(s, 0.6, 5.75, 6.2, 0.4, "github.com/wikapar/anTSP", size=14, color=DARK_TEXT)
add(1, "Jordy", "0:30", """
Hi everyone, we are Wiktoria, Jordy and Rita. Our project is about a very old puzzle, the Travelling Salesman
Problem, and about a surprising way to attack it: by copying ants.
We will show you why solving it exactly breaks down, how an ant colony algorithm works, and then we put both
head to head on 90 random maps and tell you honestly who wins, and where.
""")

# 2 - what is the TSP
s = new_slide()
header(s, "The problem", "One salesman, n cities, one question", ORANGE)
text(s, 0.6, 1.95, 4.6, 3.6, [
    [("Visit every city ", {}), ("exactly once", {"bold": True}), (", return home, with the ", {}),
     ("shortest total route", {"bold": True}), (".", {})],
    "",
    [("Where it shows up", {"bold": True})],
    "Delivery and pickup routes",
    "Drilling holes in circuit boards",
    "Ordering DNA fragments",
], size=17, space_after=4)
picture(s, ASSETS / "tsp_intro.png", 5.4, 2.0, w=7.4, name="Random vs shortest tour")
card(s, 5.4, 5.35, 7.4, 1.05)
text(s, 5.65, 5.47, 7.0, 0.85, [[("Same 12 cities, different order: ", {}),
                                  ("2.3× longer", {"bold": True, "color": ORANGE}),
                                  (". The order is the whole problem.", {})]], size=17,
     anchor=MSO_ANCHOR.MIDDLE)
add(2, "Jordy", "1:00", """
So, what is the TSP? You get a list of cities and the distances between them. You must visit every city
exactly once and come back to where you started, and you want the shortest total route. That's it, a child
understands the problem.
And it is everywhere: delivery vans planning routes, machines drilling thousands of holes into circuit boards,
even putting pieces of DNA in the right order.
Look at the picture: these are the same 12 cities. On the left a random order: 3868 units long. On the right
the best possible order: 1678. Same cities, and the order alone makes the route more than twice as long.
So the question is: how do we find the picture on the right?
""")

# 3 - combinatorial explosion
s = new_slide()
header(s, "The problem", "Why not just try every tour?", ORANGE)
text(s, 0.6, 1.9, 12, 0.5, [[("Number of different tours: ", {}), ("(n − 1)! / 2", {"bold": True}),
                             ("   (fix the start, a tour and its reverse are the same)", {"color": MUTED})]],
     size=18)
for i, (n, tours, time) in enumerate((("10 cities", "181,440", "less than a millisecond"),
                                      ("20 cities", "6 × 10¹⁶", "about 2 years"),
                                      ("50 cities", "3 × 10⁶²", "about 10⁴⁶ years"))):
    x = 0.6 + i * 4.1
    card(s, x, 2.65, 3.8, 2.65)
    text(s, x + 0.3, 2.85, 3.3, 0.4, n, size=16, bold=True, color=MUTED, font=HEAD)
    text(s, x + 0.3, 3.3, 3.3, 0.9, tours, size=40, bold=True, color=[GREEN, ORANGE, RED][i], font=HEAD)
    text(s, x + 0.3, 4.25, 3.3, 0.9, [[("at 10⁹ tours per second: ", {"color": MUTED})], time], size=15)
text(s, 0.6, 5.65, 12.1, 1.0, [
    [("For comparison: the universe is about 1.4 × 10¹⁰ years old. ", {}),
     ("The TSP is NP-hard: ", {"bold": True}),
     ("no known algorithm solves every instance in polynomial time.", {})]], size=17)
add(3, "Jordy", "1:15", """
The obvious idea: try every order and keep the shortest. With n cities there are (n minus 1) factorial over 2
different tours.
For 10 cities that's 181 thousand: a computer does that in a blink.
For 20 cities it's 6 times 10 to the 16. Even at one billion tours per second, that's about two years.
For 50 cities, still a tiny delivery route, it's 3 times 10 to the 62: about 10 to the 46 years. The universe
is only about 10 to the 10 years old.
And it's not just us being lazy: the TSP is NP-hard. Nobody knows an algorithm that solves every instance in
polynomial time. Find one, and you have also solved P versus NP, which comes with a million-dollar prize.
Rita will now show how far we can push the exact approach anyway.
""")

# 4 - exact algorithms
s = new_slide()
header(s, "Exact methods", "Exact algorithms: smarter, but still exponential", BLUE)
picture(s, ASSETS / "pruning_tree.png", 0.45, 1.85, w=6.3, name="Branch and bound tree")
blocks = [
    ("Backtracking", "Builds the tour city by city, depth-first. Without pruning: every one of the (n−1)! leaves."),
    ("Branch & bound", "Cut a branch when path + MST of the remaining cities ≥ best tour. "
                       "Search each tour in one direction only. Start from a greedy tour."),
    ("Held–Karp (1962)", "Dynamic programming over subsets of cities: n² · 2ⁿ steps instead of n!."),
]
for i, (title, body) in enumerate(blocks):
    y = 1.95 + i * 1.5
    card(s, 7.05, y, 5.7, 1.3)
    text(s, 7.3, y + 0.15, 5.25, 0.4, title, size=17, bold=True, color=BLUE, font=HEAD)
    text(s, 7.3, y + 0.55, 5.25, 0.75, body, size=14)
text(s, 7.05, 6.5, 5.7, 0.5, [[("Always optimal. ", {"bold": True}), ("But the cost still explodes, just later.", {})]],
     size=16)
add(4, "Rita", "1:15", """
We implemented two exact methods. Backtracking builds the tour city by city, like walking down this tree; every
leaf is a complete tour. Plain backtracking visits every leaf: that's the explosion from the last slide.
The trick is branch and bound. We keep the best tour so far, and at every node we compute a lower bound: the
path so far plus the minimum spanning tree of the cities that are left. The rest of the route must connect
those cities, so it can't be shorter than that tree. If the bound is already worse than our best tour, the
whole branch is cut: the red nodes. We also search each tour in one direction only, and start with a quick
greedy tour, so we have a good bound from the first step.
The second method, Held-Karp from 1962, uses dynamic programming over subsets of cities: n squared times 2 to
the n steps. Much better than n factorial, but still exponential.
Both always return the optimal tour. The cost still explodes, just later.
""")

# 5 - ants in nature
s = new_slide()
header(s, "Ant colony", "What ants know about shortest paths", ORANGE)
picture(s, ASSETS / "double_bridge.png", 0.5, 1.85, w=7.3, name="Double bridge experiment")
text(s, 8.2, 2.0, 4.6, 4.3, [
    [("The double-bridge experiment", {"bold": True, "color": ORANGE, "font": HEAD})],
    "Argentine ants, a nest, food, and two paths of different length (Goss et al., 1989).",
    [("Ants leave ", {}), ("pheromone", {"bold": True}), (" and prefer strong trails.", {})],
    "The short path is reinforced faster, so the colony ends up using it.",
    [("No ant knows the map: the shortest path ", {}), ("emerges", {"bold": True}),
     (" from simple local rules.", {})],
], size=16, space_after=10)
add(5, "Wiktoria", "1:00", """
So if being exact is too expensive, maybe we can be clever instead, and this is where the ants come in.
In 1989 biologists gave an Argentine ant colony two bridges of different length leading to food. At first
ants pick a branch randomly. But ants leave pheromone, a chemical trail, and they prefer to follow strong
trails. Ants on the short branch come back sooner, so that branch is reinforced faster. More ants choose it,
it gets even more pheromone, and after a while most of the colony uses the short path. At the same time
pheromone evaporates, so the long path is slowly forgotten.
No single ant knows the map. The short path emerges from very simple rules. In the early 1990s Marco Dorigo
turned exactly this into an optimization algorithm.
""")

# 6 - the algorithm
s = new_slide()
header(s, "Ant colony", "Ant Colony Optimization in four steps", ORANGE)
steps = [
    ("Build", [[("Each ant builds a tour. Next city j with probability", {})],
               [("p ∝ τ", {"bold": True}), ("ij", {"size": 11, "bold": True}), ("^α · (1/d", {"bold": True}),
                ("ij", {"size": 11, "bold": True}), (")^β", {"bold": True})],
               [("τ = pheromone, d = distance", {"color": MUTED})]]),
    ("Evaporate", [[("All trails fade:", {})], [("τ ← (1 − ρ) · τ", {"bold": True})],
                   [("bad old choices are forgotten", {"color": MUTED})]]),
    ("Deposit", [[("Each ant adds", {})], [("Q / L", {"bold": True})],
                 [("on its tour: shorter tour, more pheromone", {"color": MUTED})]]),
    ("Repeat", [[("100 iterations,", {})], [("keep the best tour", {"bold": True})],
                [("no guarantee it is optimal", {"color": MUTED})]]),
]
for i, (title, body) in enumerate(steps):
    x = 0.6 + i * 3.1
    card(s, x, 1.95, 2.85, 2.75)
    dot(s, x + 0.25, 2.15, 0.5, ORANGE, str(i + 1), 16)
    text(s, x + 0.9, 2.2, 1.8, 0.45, title, size=18, bold=True, font=HEAD)
    text(s, x + 0.25, 2.85, 2.4, 1.8, body, size=15, space_after=4)
text(s, 0.6, 5.0, 12.1, 0.4, "Variants we implemented", size=16, bold=True, color=ORANGE, font=HEAD)
variants = [("Ant System", "every ant deposits (Dorigo et al., 1996)"),
            ("Elitist AS", "extra pheromone on the best tour so far"),
            ("MAX-MIN AS", "only the best ant deposits, trails kept within [τmin, τmax] (Stützle & Hoos, 2000)"),
            ("+ 2-opt", "each ant removes crossing edges from its tour")]
for i, (name, body) in enumerate(variants):
    x = 0.6 + i * 3.1
    text(s, x, 5.45, 2.85, 1.3, [[(name, {"bold": True})], body], size=14, space_after=2)
add(6, "Wiktoria", "1:15", """
Here is the algorithm. In every iteration each virtual ant builds a full tour. At each city it picks the next
one randomly, but not uniformly: the probability depends on tau, the pheromone on that road, and on one over
the distance, so close cities are attractive. Alpha and beta set how much we trust each.
Then all trails evaporate by a factor rho, and every ant puts pheromone on its own tour: Q over L, so shorter
tours leave more. Repeat 100 times, keep the best tour.
Besides the classic Ant System we built two improved versions: Elitist, which rewards the best tour so far, and
MAX-MIN, where only the best ant deposits and trails stay within limits, so the colony doesn't get stuck too
early. Optionally each ant also untangles crossing roads in its tour, called 2-opt.
Important: this is a heuristic, with no guarantee. That's exactly why we compare it with the exact methods.
""")

# 7 - simulation
s = new_slide()
header(s, "Our tool", "Same map, two strategies, live", ORANGE)
picture(s, ASSETS / "simulation.gif", 0.6, 1.85, h=5.15, name="Simulation animation (GIF)")
text(s, 8.65, 1.95, 4.1, 5.0, [
    [("Left: ", {"bold": True, "color": ORANGE}), ("ants. Orange = pheromone, green = best tour.", {})],
    [("Right: ", {"bold": True, "color": BLUE}), ("branch & bound. Dashed = path being explored.", {})],
    [("Bottom: ", {"bold": True}), ("best length found so far.", {})],
    "",
    [("Ants find the optimum at ", {}), ("step 77", {"bold": True, "color": ORANGE}), (".", {})],
    [("Backtracking finds it at ", {}), ("step 1660", {"bold": True, "color": BLUE}),
     (" and proves it at step 1704.", {})],
], size=16, space_after=8)
caption(s, 8.65, 6.65, 4.1, "python anTSP.py --seed 30 --algo-seed 4")
add(7, "Wiktoria", "1:15", """
This is our simulator. Both algorithms run on the same 10-city map, one step each at a time.
On the left, the ants. The orange lines are the pheromone trails, and you can see them concentrating. The green
line is the best tour so far. On the right, backtracking with the MST bound; the dashed blue line is the path it
is exploring right now. At the bottom you see the best length found so far for both.
Watch the orange line: the ants hit the optimal tour after only 77 steps. Backtracking keeps improving, finds
the same tour at step 1660, and finishes at step 1704. Only at that moment do we actually know it is optimal.
That difference, finding versus proving, is the main theme of our results.
""")

# 8 - method
s = new_slide()
header(s, "Method", "How we compared them fairly", GREEN)
cells = [
    ("90 random maps", "18 sizes from 5 to 50 cities, 5 maps each"),
    ("1,380 runs", "every ACO variant 3× per map (different seeds), 100 iterations"),
    ("Work = edge evaluations", "how often an algorithm reads a road length; machine independent, plus CPU time"),
    ("Quality = gap", "% above the optimal tour; for n ≥ 25 above the best tour anyone found"),
    ("30 s limit", "for exact algorithms; after a timeout they skip bigger maps"),
    ("Reproducible", "all seeds and settings saved; one command reruns everything"),
]
for i, (title, body) in enumerate(cells):
    x = 0.6 + (i % 3) * 4.1
    y = 1.95 + (i // 3) * 2.45
    card(s, x, y, 3.8, 2.15)
    dot(s, x + 0.3, y + 0.3, 0.22, GREEN)
    text(s, x + 0.3, y + 0.7, 3.25, 0.5, title, size=19, bold=True, font=HEAD)
    text(s, x + 0.3, y + 1.2, 3.25, 0.9, body, size=14)
add(8, "Rita", "1:00", """
One animation proves nothing, so we ran a real experiment: 90 random maps from 5 to 50 cities, and every ACO
variant 3 times per map with different seeds. 1380 runs in total.
How do you compare a step of an ant with a step of backtracking? You don't. We count edge evaluations, how often
an algorithm reads the length of a road, which doesn't depend on the computer. We also report CPU time.
Quality is the gap to the optimal length. Up to about 25 cities the exact algorithms gave us the optimum, and
they always agreed with each other, a nice correctness check. Above that we compare with the best tour anyone
found. Exact algorithms were stopped after 30 seconds, and everything is seeded, so anyone can rerun it.
""")

# 9 - runtime
s = new_slide()
header(s, "Result 1", "Exact methods hit a wall, ACO keeps going", GREEN)
picture(s, PLOTS / "01_runtime_vs_n.png", 0.45, 1.75, w=9.0, name="Runtime vs n")
for i, (number, label, color) in enumerate((("> 30 s", "no pruning at 11 cities (3 s at 10)", RED),
                                            ("7 s", "Held–Karp at 20 cities", INK),
                                            ("0.8 s", "Ant System at 50 cities", ORANGE))):
    stat(s, 9.75, 1.95 + i * 1.65, 3.1, number, label, color, number_size=36)
add(9, "Rita", "1:00", """
First result: runtime, on a log scale, so every grid line means ten times more.
The red line is backtracking without pruning: 3 seconds at 10 cities, and at 11 cities none of the five maps
finished within 30 seconds. That's the factorial explosion, live.
Held-Karp, in gray, reaches 20 cities in 7 seconds, but its time and memory double with every city we add.
Branch and bound, in blue, also reaches 20.
The ant algorithms, orange and green, grow slowly: under 2 seconds even at 50 cities.
Fair to say: for small maps the exact methods are actually faster. If you have 10 cities, just solve it exactly.
""")

# 10 - pruning
s = new_slide()
header(s, "Result 2", "Better bounds move the wall, but don't remove it", BLUE)
picture(s, PLOTS / "03_exact_algorithms.png", 0.45, 1.75, w=9.0, name="Exact algorithms")
for i, (number, label, color) in enumerate((("11 s", "simple bound, 12 cities", RED),
                                            ("0.14 s", "MST bound, 12 cities (80× faster)", BLUE),
                                            ("3 of 5", "maps solved at 25 cities within 30 s", INK))):
    stat(s, 9.75, 1.95 + i * 1.65, 3.1, number, label, color, number_size=36)
add(10, "Rita", "0:45", """
This zooms in on the exact methods, because the improvements were dramatic.
With a simple bound, cutting when the path is already too long, we reach 12 cities in 11 seconds. With the
MST lower bound the same 12 cities take 0.14 seconds, about 80 times faster, and we get to 20 cities in under
2 seconds.
But look at 25 cities: only 3 of the 5 maps finished in 30 seconds. A better bound moves the wall; it doesn't
remove it.
Jordy will now show what the ants do in the meantime.
""")

# 11 - convergence
s = new_slide()
header(s, "Result 3", "Finding is cheap, proving is expensive", GREEN)
picture(s, PLOTS / "06_convergence_n12.png", 0.45, 1.75, w=9.0, name="Convergence n=12")
for i, (number, label, color) in enumerate((("11k", "evaluations: Ant System reaches its best tour", ORANGE),
                                            ("51k", "branch & bound (MST) finishes the proof", BLUE),
                                            ("4.8M", "same proof with the simple bound", RED))):
    stat(s, 9.75, 1.95 + i * 1.65, 3.1, number, label, color, number_size=36)
caption(s, 9.75, 6.8, 3.1, "medians over 5 maps with 12 cities")
add(11, "Jordy", "1:15", """
This is our favourite plot. All maps with 12 cities. The x-axis is work, edge evaluations on a log scale, and
the y-axis is how far the best tour found so far is from the optimum. Solid lines are ACO, dashed lines are
exact algorithms, and a square means that algorithm finished and proved optimality.
The ant curves drop to zero after roughly ten thousand evaluations; in the median, Ant System reaches its final
tour after about 11 thousand. Branch and bound with the MST bound needs about 51 thousand to finish its proof,
and with the simple bound it's almost 5 million.
So the ants are fast at finding a very good tour. What they can never do is tell you it is the best one. The
exact methods spend most of their effort on that proof.
""")

# 12 - quality
s = new_slide()
header(s, "Result 4", "How good are the ants?", ORANGE)
picture(s, PLOTS / "04_aco_gap_vs_n.png", 0.45, 1.75, w=9.0, name="ACO gap vs n")
for i, (number, label, color) in enumerate((("95 %", "Ant System runs that found the optimum (n ≤ 25)", ORANGE),
                                            ("100 %", "MAX-MIN AS + 2-opt, all 219 runs", GREEN),
                                            ("+5.1 %", "Ant System at 50 cities (+0.05 % with MAX-MIN + 2-opt)",
                                             INK))):
    stat(s, 9.75, 1.95 + i * 1.65, 3.1, number, label, color, number_size=36)
add(12, "Jordy", "1:00", """
So how good are the ants? Up to 25 cities, where we know the optimum, plain Ant System found the optimal tour in
209 of 219 runs, about 95 percent, and when it missed, it was less than one percent too long. MAX-MIN with 2-opt
found the optimum in every single run.
Beyond 25 cities is the gray zone, where we compare with the best tour anyone found. At 50 cities Ant System is
about 5 percent above it, MAX-MIN about 3 percent, and MAX-MIN with 2-opt 0.05 percent.
One surprise: the Elitist variant was not better than plain Ant System on our maps. Our guess is that giving the
best tour so much extra weight makes the colony settle too early, but we did not test that further.
""")

# 13 - parameters
s = new_slide()
header(s, "Result 5", "Parameters matter: distance information is essential", ORANGE)
picture(s, PLOTS / "08_sensitivity_alpha_beta.png", 0.45, 1.8, w=6.4, name="Alpha beta heatmap")
picture(s, PLOTS / "09_sensitivity_rho.png", 6.95, 1.8, w=5.9, name="Evaporation rate")
text(s, 0.6, 5.35, 12.1, 1.4, [
    [("β = 0 (pheromone only): ", {"bold": True}), ("over 200 % worse. ", {}),
     ("Best: α = 1, β = 3 ", {"bold": True}), ("with 0.9 %.", {})],
    [("Evaporation: ", {"bold": True}), ("too little (ρ = 0.02) keeps bad trails: 5.5 %; sweet spot ρ ≈ 0.2–0.6. ", {}),
     ("Ants: ", {"bold": True}), ("1 ant 13 %, 40 ants 1.1 %.", {})],
], size=16, space_after=6)
caption(s, 0.6, 6.75, 12, "Ant System on 40-city maps, 3 maps × 3 runs per setting; gap to the best known tour")
add(13, "Wiktoria", "1:00", """
ACO has knobs, so we tested them on 40-city maps, 3 maps times 3 runs for each setting.
The heatmap shows alpha, the weight of the pheromone, against beta, the weight of the distance. The left column
is beta equal to zero: ants that only follow pheromone and ignore distance. They are more than 200 percent worse.
So the distance information is essential; pheromone alone is not enough. The best combination was alpha 1 and
beta 3, under 1 percent.
On the right is evaporation. With almost no evaporation, 0.02, old bad trails never disappear: 5.5 percent.
Around 0.2 to 0.6 is the sweet spot.
And more ants help: 1 ant gives 13 percent, 40 ants about 1 percent, but every ant also costs time.
""")

# 14 - conclusions
s = new_slide()
header(s, "Conclusions", "What we learned", GREEN)
columns = [
    (BLUE, "Exact algorithms", ["Always optimal, and they prove it.",
                                "With good pruning, fast up to ~20–25 cities.",
                                "Then the cost explodes, no matter the bound."]),
    (ORANGE, "Ant colony", ["No guarantee, but optimal in ~95 % of small cases.",
                            "A few % from the best at 50 cities, cost grows slowly.",
                            "MAX-MIN + 2-opt: practically always optimal."]),
    (GREEN, "Best of both", ["The ants' tour as the starting bound for branch & bound:",
                             "ants find, the exact method proves.",
                             "(implemented: --initial-tour aco)"]),
]
for i, (color, title, lines) in enumerate(columns):
    x = 0.6 + i * 4.1
    card(s, x, 1.95, 3.8, 2.85)
    dot(s, x + 0.3, 2.2, 0.22, color)
    text(s, x + 0.65, 2.12, 3.0, 0.45, title, size=19, bold=True, font=HEAD, color=color)
    text(s, x + 0.3, 2.7, 3.25, 2.0, lines, size=15, space_after=6)
text(s, 0.6, 5.1, 12.1, 0.4, "Limitations", size=16, bold=True, color=MUTED, font=HEAD)
text(s, 0.6, 5.5, 12.1, 1.3, [
    "Uniformly random points: real road networks can behave differently.",
    "Python on one laptop: compare the trends, not the absolute times (Concorde solves "
    "instances with tens of thousands of cities exactly).",
    "For n ≥ 25 the reference is the best known tour, not a proven optimum.",
], size=14, space_after=3)
add(14, "Rita", "1:15", """
To sum up. Exact algorithms give a guarantee, and with good pruning they're fast for small problems: up to
about 20 to 25 cities in our Python code. After that the cost explodes, no matter how clever the bound.
Ant colony optimization gives no guarantee, but it found the optimum in about 95 percent of the small cases,
stayed within a few percent at 50 cities, and its cost grows slowly.
And the two combine nicely: the ants' tour can be the starting bound for branch and bound. The ants find, the
exact method proves. Our tool supports that.
To be honest about limitations: our maps are random points, not real roads; it's Python on one laptop, so trust
the trends, not the absolute times. Professional solvers like Concorde solve tens of thousands of cities
exactly. And above 25 cities our reference is the best known tour, not a proven optimum.
""")

# 15 - thanks
s = new_slide(dark=True)
dot(s, 0.6, 1.62, 0.16, ORANGE)
dot(s, 0.85, 1.62, 0.16, BLUE)
text(s, 0.6, 2.0, 7, 1.0, "Thank you!", size=48, bold=True, color=WHITE, font=HEAD)
text(s, 0.6, 3.05, 6.4, 0.6, "Questions?", size=24, color=DARK_TEXT)
text(s, 0.6, 4.3, 6.4, 1.6, [
    [("Try it yourself", {"bold": True, "color": WHITE})],
    [("python anTSP.py", {"font": "Courier New", "color": WHITE})],
    [("python -m experiments.run_experiments", {"font": "Courier New", "color": WHITE})],
    [("github.com/wikapar/anTSP", {"color": DARK_TEXT})],
], size=16, space_after=6)
text(s, 0.6, 6.3, 7, 0.4, "Wiktoria PARZYCH  ·  Jordy GODJO  ·  Rita GAYITMAZOVA", size=14, color=DARK_TEXT)
picture(s, ASSETS / "simulation_frame.png", 7.15, 1.4, w=5.6, name="Simulator screenshot")
add(15, "All", "0:20", """
Thank you! The code is on GitHub. You can run python anTSP.py and watch the ants yourself, or rerun all our
experiments with one command. We're happy to take your questions.
""")

# notes + script.md
for index, slide in enumerate(prs.slides, start=1):
    speaker, minutes, script = SCRIPT[index]
    notes(slide, speaker, minutes, script + ("\n\n" + TECH_NOTES[index] if index in TECH_NOTES else ""))

prs.save(OUT)
print("saved", OUT)

titles = {1: "Title", 2: "One salesman, n cities, one question", 3: "Why not just try every tour?",
          4: "Exact algorithms: smarter, but still exponential", 5: "What ants know about shortest paths",
          6: "Ant Colony Optimization in four steps", 7: "Same map, two strategies, live (animation)",
          8: "How we compared them fairly", 9: "Result 1: Exact methods hit a wall, ACO keeps going",
          10: "Result 2: Better bounds move the wall, but don't remove it",
          11: "Result 3: Finding is cheap, proving is expensive",
          12: "Result 4: How good are the ants?", 13: "Result 5: Parameters matter",
          14: "Conclusions: What we learned", 15: "Thank you / Questions"}
lines = ["# anTSP presentation: speaker script", "",
         "Audience: other students. Allowed length: 10 to 15 minutes.",
         "Speaker split (change freely): Jordy = intro + results 3-4, Wiktoria = ants + demo + parameters, "
         "Rita = exact methods + method + results 1-2 + conclusions.", "",
         "The same text is in the speaker notes of every slide.", ""]
total = 0
for index in sorted(SCRIPT):
    speaker, minutes, script = SCRIPT[index]
    m, sec = minutes.split(":")
    total += int(m) * 60 + int(sec)
    lines += [f"## Slide {index}: {titles[index]}", f"**{speaker}**, about {minutes} min", "",
              " ".join(script.split("\n")).replace("  ", " "), ""]
lines.insert(3, f"Timings assume a calm {WORDS_PER_MINUTE} words per minute: {total // 60}:{total % 60:02d} min in total. "
                "At a normal pace (about 145 words per minute) it is about 12.5 min, which leaves room for speaker changes. "
                "If you run long, shorten slide 10 or 13.")
(HERE / "script.md").write_text("\n".join(lines), encoding="utf-8")
print("saved", HERE / "script.md", f"({total // 60}:{total % 60:02d} min)")
