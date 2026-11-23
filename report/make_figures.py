#!/usr/bin/env python3
"""Generate the figures for the gem5 LRU cache-sweep progress report.

Reads report/lru_sweep_runs.csv and writes four 300 dpi PNGs to report/figures/.
Run from anywhere:  python3 report/make_figures.py
"""
import csv
import math
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "lru_sweep_runs.csv")
OUT = os.path.join(HERE, "figures")

# ---------------------------------------------------------------------------
# Style (dataviz skill reference palette, light mode)
# ---------------------------------------------------------------------------
FAMILIES = ["seq", "chase", "tr"]
LABEL = {"seq": "Sequential", "chase": "Pointer chase", "tr": "Transpose"}
COLOR = {"seq": "#2a78d6", "chase": "#eb6834", "tr": "#1baf7a"}  # slots 1-3, validated
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BYTES_PER_ELEM = {"seq": lambda n: 4 * n, "chase": lambda n: 64 * n, "tr": lambda n: 8 * n * n}
L1D_BYTES, L2_BYTES = 16 * 1024, 256 * 1024

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "semibold",
    "axes.titlecolor": INK,
    "axes.labelsize": 9.5,
    "axes.labelcolor": INK2,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "grid.linestyle": "-",
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.minor.size": 1.5,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "legend.labelcolor": INK2,
    "lines.linewidth": 1.8,
    "lines.markersize": 5.5,
    "lines.markeredgewidth": 1.2,
    "lines.markeredgecolor": "white",  # the 2px surface ring
    "savefig.dpi": 300,
    "figure.dpi": 100,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def parse_size(s):
    m = re.fullmatch(r"(\d+)([kKmM]?)B", s.strip())
    n, u = int(m.group(1)), m.group(2).lower()
    return n * {"": 1, "k": 1024, "m": 1024 ** 2}[u]


def fmt_bytes(b):
    """512 B, 1 kB, 64 kB, 4 MB  (for power-of-two values)."""
    if b < 1024:
        return f"{b:g} B"
    if b < 1024 ** 2:
        return f"{b / 1024:g} kB"
    return f"{b / 1024 ** 2:g} MB"


def load():
    rows = []
    with open(CSV, newline="") as f:
        for r in csv.DictReader(f):
            m = re.fullmatch(r"(seq|chase|tr)_n(\d+)_(small|medium|large)", r["run"])
            fam, n, tag = m.group(1), int(m.group(2)), m.group(3)
            rows.append({
                "family": fam, "n": n, "tag": tag,
                "footprint": BYTES_PER_ELEM[fam](n),
                "l1d": parse_size(r["l1d"]), "l2": parse_size(r["l2"]),
                "cpi": float(r["cpi"]), "ipc": float(r["ipc"]),
                "l1d_mpki": float(r["l1d_mpki"]), "l2_mpki": float(r["l2_mpki"]),
            })
    return rows


def select(rows, **kw):
    out = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    return sorted(out, key=lambda r: (r["footprint"], r["l2"]))


# ---------------------------------------------------------------------------
# Axis helpers
# ---------------------------------------------------------------------------
def log2_bytes_axis(ax, lo, hi, label_every=2):
    """log2 x-axis spanning [lo, hi] bytes; major labels every `label_every` doublings."""
    ax.set_xscale("log", base=2)
    ax.set_xlim(lo / 1.4, hi * 1.4)
    powers = [2 ** k for k in range(int(math.log2(lo)), int(math.log2(hi)) + 1)]
    ax.xaxis.set_major_locator(FixedLocator(powers[::label_every]))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_bytes(v)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(False, which="minor")


def cache_boundaries(ax, y_frac=0.97):
    return  # reference lines removed for a simpler figure


def family_legend(ax, families=FAMILIES, **kw):
    handles = [Line2D([], [], color=COLOR[f], marker="o", label=LABEL[f]) for f in families]
    ax.legend(handles=handles, **kw)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------------------
# Figure 1: IPC vs working-set footprint (baseline)
# ---------------------------------------------------------------------------
def fig1(rows):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for fam in FAMILIES:
        d = select(rows, family=fam, tag="large")
        ax.plot([r["footprint"] for r in d], [r["ipc"] for r in d],
                color=COLOR[fam], marker="o", label=LABEL[fam], zorder=3)
    log2_bytes_axis(ax, 512, 4 * 1024 ** 2)
    cache_boundaries(ax)
    ax.set_ylim(0, 4.6)
    ax.set_xlabel("Working-set footprint")
    ax.set_ylabel("IPC")
    ax.set_title("IPC vs working-set size, baseline caches (L1D 16 kB / L2 256 kB, LRU)")
    family_legend(ax, loc="upper right", bbox_to_anchor=(1.0, 0.90))
    save(fig, "fig1_ipc_vs_workingset_baseline.png")


# ---------------------------------------------------------------------------
# Figure 2: CPI stacked into core + memory (baseline)
# ---------------------------------------------------------------------------
def fig2(rows):
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    Y0 = 0.1  # log-axis floor the bars grow from
    width, gap = 0.82, 1.2
    x = 0.0
    centres, tick_labels, group_centres = [], [], []
    for fam in FAMILIES:
        d = select(rows, family=fam, tag="large")
        core = d[0]["cpi"]  # CPI at the smallest footprint = "core" component
        xs = []
        for r in d:
            mem = max(r["cpi"] - core, 0.0)
            # core segment (capped at the total where CPI dips below the "core" value)
            ax.bar(x, min(core, r["cpi"]) - Y0, bottom=Y0, width=width, color=COLOR[fam],
                   linewidth=0, zorder=3)
            # memory segment, tint of the family colour, 2px-ish surface gap below it
            if mem > 0.02 * core:
                ax.bar(x, mem, bottom=core, width=width, color=COLOR[fam], alpha=0.35,
                       linewidth=0, zorder=3)
                ax.bar(x, 0, bottom=core, width=width, edgecolor="white",
                       linewidth=1.6, zorder=4)
            ax.text(x, r["cpi"] * 1.12, f"{r['cpi']:.2f}", ha="center", va="bottom",
                    fontsize=7.5, color=INK2, zorder=5)
            centres.append(x)
            tick_labels.append(fmt_bytes(r["footprint"]).replace(" ", " "))
            xs.append(x)
            x += 1
        group_centres.append((sum(xs) / len(xs), fam, core))
        x += gap

    ax.set_yscale("log")
    ax.set_ylim(Y0, 120)
    ax.set_yticks([0.1, 0.3, 1, 3, 10, 30, 100])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(False, axis="x")
    ax.set_xticks(centres)
    ax.set_xticklabels(tick_labels, fontsize=7.5)
    ax.tick_params(axis="x", length=0)
    for gx, fam, core in group_centres:
        ax.text(gx, -0.09, f"{LABEL[fam]}  (core CPI {core:.2f})", transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=9, color=INK)
    ax.set_xlabel("Working-set footprint", labelpad=34)
    ax.set_ylabel("CPI (log scale)")
    ax.set_title("CPI split into core and memory components, baseline caches (L1D 16 kB / L2 256 kB)")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#898781", label="Core (CPI at smallest footprint)"),
        plt.Rectangle((0, 0), 1, 1, color="#898781", alpha=0.35, label="Memory (CPI − core)"),
    ]
    ax.legend(handles=handles, loc="upper left")
    save(fig, "fig2_cpi_stack_baseline.png")


# ---------------------------------------------------------------------------
# Figure 3: L2 MPKI vs footprint (baseline)
# ---------------------------------------------------------------------------
def fig3(rows):
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for fam in FAMILIES:
        d = select(rows, family=fam, tag="large")
        ax.plot([r["footprint"] for r in d], [r["l2_mpki"] for r in d],
                color=COLOR[fam], marker="o", label=LABEL[fam], zorder=3)
    log2_bytes_axis(ax, 512, 4 * 1024 ** 2)
    cache_boundaries(ax)
    ax.set_ylim(0, 230)
    ax.set_xlabel("Working-set footprint")
    ax.set_ylabel("L2 misses per 1000 instructions")
    ax.set_title("L2 MPKI vs working-set size, baseline caches (L1D 16 kB / L2 256 kB, LRU)")
    family_legend(ax, loc="upper left", bbox_to_anchor=(0.0, 0.90))
    save(fig, "fig3_l2_mpki_baseline.png")


# ---------------------------------------------------------------------------
# Figure 4: CPI vs L2 size for selected (family, n)
# ---------------------------------------------------------------------------
def fig4(rows):
    picks = [("chase", 128), ("chase", 1024), ("chase", 8192),
             ("tr", 64), ("tr", 256), ("seq", 16384)]
    styles = [("o", "-"), ("s", "--"), ("^", ":")]  # per n within a family
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    seen = {}
    for fam, n in picks:
        marker, ls = styles[seen.get(fam, 0)]
        seen[fam] = seen.get(fam, 0) + 1
        d = select(rows, family=fam, n=n)
        fp = fmt_bytes(BYTES_PER_ELEM[fam](n))
        ax.plot([r["l2"] for r in d], [r["cpi"] for r in d], color=COLOR[fam],
                marker=marker, linestyle=ls, label=f"{LABEL[fam]}, n={n} ({fp})", zorder=3)
    ax.set_xscale("log", base=2)
    sizes = [8 * 1024, 64 * 1024, 256 * 1024]
    ax.set_xticks(sizes)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_bytes(v)))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.set_xlim(sizes[0] / 1.6, sizes[-1] * 1.6)
    ax.set_yscale("log")
    ax.set_ylim(0.15, 80)
    ax.set_yticks([0.2, 0.5, 1, 2, 5, 10, 20, 50])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("L2 size (L1D scales with it: 1 kB / 4 kB / 16 kB)")
    ax.set_ylabel("CPI (log scale)")
    ax.set_title("CPI vs cache size for selected workloads")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, "fig4_cpi_vs_l2size.png")


if __name__ == "__main__":
    data = load()
    fig1(data)
    fig2(data)
    fig3(data)
    fig4(data)
