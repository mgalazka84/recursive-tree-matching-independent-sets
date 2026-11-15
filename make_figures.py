"""Rebuild the three vector figures from the manuscript examples and formulas."""

from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from verify_results import encode


FIGURES = Path(__file__).resolve().parent / "figures"
INK = "#20313b"
BLUE = "#175578"
LIGHT = "#737d81"
RED = "#954326"


def matching(parents, accept_first):
    used = set()
    accepted = []
    for child, parent in enumerate(parents, 2):
        if parent not in used and (child != 2 or accept_first):
            used.update((parent, child))
            accepted.append((parent, child))
    return accepted


def draw_tree(ax, parents, accepted, positions):
    for child, parent in enumerate(parents, 2):
        xa, ya = positions[parent]
        xb, yb = positions[child]
        chosen = (parent, child) in accepted
        ax.plot([xa, xb], [ya, yb], color=BLUE if chosen else LIGHT,
                lw=4.0 if chosen else 1.15, zorder=1)
    for vertex, (x, y) in positions.items():
        ax.scatter([x], [y], s=205, facecolors="white", edgecolors=INK,
                   linewidths=1.0, zorder=2)
        ax.text(x, y, str(vertex), ha="center", va="center", color=INK,
                fontsize=9, zorder=3)
    ax.set_aspect("equal")
    ax.axis("off")


def save(fig, filename):
    fig.savefig(FIGURES / filename, format="pdf", metadata={"CreationDate": None})
    plt.close(fig)


def first_decision():
    parents = (1, 1, 2)
    positions = {3: (0, 0), 1: (.8, 0), 2: (1.6, 0), 4: (2.4, 0)}
    fig, axes = plt.subplots(1, 2, figsize=(6.5, .90))
    fig.subplots_adjust(left=.02, right=.98, top=.70, bottom=.08, wspace=.21)
    expected = [1, 2]
    for ax, keep_first, title, size in zip(
            axes, (True, False), ("Accept the first edge", "Reject the first edge"), expected):
        accepted = matching(parents, keep_first)
        assert len(accepted) == size
        draw_tree(ax, parents, accepted, positions)
        ax.set(xlim=(-.22, 2.62), ylim=(-.21, .21))
        ax.set_title(title, fontsize=10, color=INK, pad=5)
    for keep_first in (False, True):
        total = sum(len(matching((1, 1, last_parent), keep_first))
                    for last_parent in (1, 2, 3))
        assert Fraction(total, 3) == Fraction(4, 3)
    save(fig, "first_decision.pdf")


def bijection_example():
    parents = (1, 1, 3, 2, 5)
    word, size = encode(parents)
    assert word == (2, 4, 3, 5, 1) and size == 3
    positions = {1: (0, 1), 2: (-.62, .35), 3: (.62, .35),
                 4: (.62, -.3), 5: (-.62, -.3), 6: (-.62, -.95)}
    fig, (left, right) = plt.subplots(1, 2, figsize=(6.5, 2.22),
                                       gridspec_kw={"width_ratios": [1, 1.35]})
    fig.subplots_adjust(left=.03, right=.97, bottom=.21, top=.83, wspace=.18)
    draw_tree(left, parents, matching(parents, True), positions)
    left.set(xlim=(-1.05, 1.05), ylim=(-1.19, 1.25))
    left.set_title("Three accepted edges", color=INK, fontsize=10)
    positions_word = list(range(1, len(word) + 1))
    right.plot(positions_word, word, lw=1.25, color=LIGHT)
    for i, value in enumerate(word):
        is_peak = 0 < i < len(word) - 1 and word[i - 1] < value > word[i + 1]
        right.scatter(i + 1, value, s=55 if is_peak else 24,
                      marker="D" if is_peak else "o", color=BLUE if is_peak else INK,
                      zorder=3)
        right.text(i + 1, value + .27, str(value), ha="center", fontsize=9, color=INK)
    right.set(xlim=(.6, 5.4), ylim=(.5, 5.95), xticks=positions_word, yticks=[],
              xlabel="Position in the permutation")
    right.set_title("Two interior peaks", color=INK, fontsize=10)
    for side in ("top", "right", "left"):
        right.spines[side].set_visible(False)
    right.spines["bottom"].set_color(LIGHT)
    right.tick_params(length=3)
    save(fig, "bijection.pdf")


def rejection_costs():
    horizon = 10
    arrivals = list(range(2, horizon + 1))
    edge = [Fraction((s - 1) * (s - 2), (horizon - 1) * (horizon - 2)) for s in arrivals]
    vertex = [Fraction(s - 1, horizon - 1) for s in arrivals]
    assert (edge[3], vertex[3]) == (Fraction(1, 6), Fraction(4, 9))
    fig, ax = plt.subplots(figsize=(6.5, 2.57))
    fig.subplots_adjust(left=.12, right=.96, bottom=.24, top=.94)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#d4d8da", lw=.55)
    ax.plot(arrivals, list(map(float, vertex)), linestyle="--", color=RED, lw=1.2,
            marker="s", markersize=4.8, markerfacecolor="white", label="Independent set")
    ax.plot(arrivals, list(map(float, edge)), linestyle="-", color=BLUE, lw=1.5,
            marker="o", markersize=4.1, label="Matching")
    ax.annotate("4/9", (5, float(vertex[3])), xytext=(-6, 7), textcoords="offset points",
                ha="right", color=RED, fontsize=9)
    ax.annotate("1/6", (5, float(edge[3])), xytext=(4, -13), textcoords="offset points",
                ha="left", color=BLUE, fontsize=9)
    ax.set(xlim=(1.8, 10.2), ylim=(-.055, 1.08), xticks=arrivals,
           yticks=[0, .25, .5, .75, 1], yticklabels=["0", "¼", "½", "¾", "1"],
           xlabel="Arrival number", ylabel="Expected loss")
    ax.tick_params(length=3)
    ax.legend(loc="upper left", frameon=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    save(fig, "rejection_costs.pdf")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "text.color": INK, "axes.labelcolor": INK, "pdf.fonttype": 42})
    FIGURES.mkdir(exist_ok=True)
    first_decision()
    bijection_example()
    rejection_costs()
