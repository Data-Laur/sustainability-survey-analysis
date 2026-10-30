"""Shared chart colors and style. Edit the hex codes here to re-color every chart."""
import matplotlib.pyplot as plt

FOREST = "#34681E"
LEAF = "#6EAC42"
SKY = "#0081C3"
NAVY = "#344582"
RED = "#BB3E3E"
MAROON = "#723333"
DARK = "#2B2B2B"    # text
MID = "#808080"     # neutral gray
LIGHT = "#D9D9D9"   # light neutral gray


def apply():
    plt.rcParams.update({
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": MID, "axes.labelcolor": DARK, "text.color": DARK,
        "xtick.color": DARK, "ytick.color": DARK,
        "axes.grid": True, "grid.color": "#EAEAEA", "grid.linewidth": 0.8, "axes.axisbelow": True,
        "axes.titleweight": "bold", "axes.titlesize": 12, "font.family": "sans-serif",
        "figure.facecolor": "white", "axes.facecolor": "white",
    })
