import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COLORS = {"1a": "#2a78d6", "1a-gil": "#eb6834", "1c": "#1baf7a", "2": "#eda100"}
LABELS = {
    "1a": "Task 1a, free-threaded",
    "1a-gil": "Task 1a, GIL on",
    "1c": "Task 1c (workers)",
    "2": "Task 2, USB drive",
}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
})


def load(name):
    path = Path("results") / f"{name}.csv"
    if not path.exists():
        return None
    runs = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            runs[row["task"], int(row["threads"])].append(row)
    return runs


def medians(runs):
    keys = sorted(runs, key=lambda k: k[1])
    threads = [t for _, t in keys]
    time_s = [statistics.median(float(r["time_ms"]) for r in runs[k]) / 1000 for k in keys]
    mem_mb = [statistics.median(int(r["peak_kb"]) for r in runs[k]) / 1024 for k in keys]
    return threads, time_s, mem_mb


def scaling(out, title, keys, cores=True):
    series = {k: medians(r) for k in keys if (r := load(k))}
    if not series:
        return
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9))
    max_t = max(max(t) for t, _, _ in series.values())
    for key, (threads, time_s, mem_mb) in series.items():
        speedup = [time_s[0] / s for s in time_s]
        for ax, ys in zip(axes, (time_s, speedup, mem_mb)):
            ax.plot(threads, ys, color=COLORS[key], lw=2, marker="o", ms=6,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, label=LABELS[key], zorder=3)
        axes[1].annotate(f"{speedup[-1]:.1f}×", (threads[-1], speedup[-1]), xytext=(6, 0),
                         textcoords="offset points", va="center", color=INK, fontsize=9)
    ideal = [t for t in (1, 2, 4, 8, 16) if t <= max_t]
    axes[1].plot(ideal, ideal, color=MUTED, lw=1, ls="--", zorder=2)
    axes[1].annotate("ideal", (ideal[-1], ideal[-1]), xytext=(6, 0), textcoords="offset points",
                     va="center", color=MUTED, fontsize=9)
    ticks = sorted({x for threads, _, _ in series.values() for x in threads})
    for ax, name in zip(axes, ("Time (s)", "Speed-up vs 1 thread", "Peak memory (MB)")):
        ax.set_xscale("log", base=2)
        ax.set_xticks(ticks, [str(t) for t in ticks])
        ax.minorticks_off()
        ax.set_xlabel("threads")
        ax.set_title(name, loc="left", color=INK, fontsize=11)
        ax.set_ylim(bottom=0)
        if cores:
            for t, txt in ((8, "8 cores"), (16, "16 logical")):
                ax.axvline(t, color=GRID, lw=1.2, zorder=1)
                if ax is axes[0]:
                    ax.annotate(txt, (t, 1), xycoords=("data", "axes fraction"), xytext=(3, -2),
                                textcoords="offset points", va="top", color=MUTED, fontsize=8)
    if len(series) > 1:
        fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=len(series),
                   frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(title, x=0.01, ha="left", y=1.08 if len(series) > 1 else 1.0,
                 fontsize=13, fontweight="bold", color=INK)
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)


def versions(out):
    runs = load("1b")
    if not runs:
        return
    names = {"1b-v1": "v1  shared, no lock", "1b-v2": "v2  shared + mutex", "1b-v3": "v3  per-thread counters"}
    keys = sorted(k for k in runs if k[0] in names)
    times = [statistics.median(float(r["time_ms"]) for r in runs[k]) / 1000 for k in keys]
    expected = Path("data/expected.txt").read_text().strip()
    correct = [all(",".join([r["negative"], r["positive"], r["zero"], r["total"]]) == expected for r in runs[k]) for k in keys]
    fig, ax = plt.subplots(figsize=(9, 2.6))
    y = list(range(len(keys)))[::-1]
    ax.barh(y, times, height=0.55, color=COLORS["1a"], zorder=3)
    for yi, t, ok in zip(y, times, correct):
        ax.annotate(f"{t:.2f} s · {'correct totals' if ok else 'wrong totals'}", (t, yi), xytext=(6, 0),
                    textcoords="offset points", va="center", color=INK, fontsize=9)
    ax.set_yticks(y, [names[k[0]] for k in keys])
    ax.set_xlabel("time (s), 16 threads, median of runs")
    ax.grid(axis="x", color=GRID)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(right=max(times) * 1.35)
    ax.set_title("Task 1b: three ways to count", loc="left", color=INK, fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    Path("charts").mkdir(exist_ok=True)
    scaling("charts/task1a.png", "Task 1a: counting with threads", ["1a", "1a-gil"])
    versions("charts/task1b.png")
    scaling("charts/task1c.png", "Task 1c: producer and consumers (vs Task 1a)", ["1c", "1a"])
    scaling("charts/task2.png", "Task 2: 8 files on a USB drive", ["2"], cores=False)
    print("charts written to charts/")
