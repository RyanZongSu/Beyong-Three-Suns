"""Create a minimal single-axis histogram of the dimensionless orbit ratio R."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "s_type_multistar_planets_wds.csv"
OUTPUT_FILE = BASE_DIR / "slide2_dimensionless_ratio_R_distribution.png"


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    r = pd.to_numeric(df["R"], errors="coerce")
    r = r[(r > 0) & (r <= 1)].dropna().to_numpy()
    if len(r) == 0:
        raise RuntimeError("No valid R values found in the dataset.")

    total = len(r)
    log_r = np.log10(r)
    # Half-decade bins preserve the order-of-magnitude structure without clutter.
    edges = np.arange(-6.0, 0.001, 0.5)
    counts, _ = np.histogram(log_r, bins=edges)
    centers = (edges[:-1] + edges[1:]) / 2
    widths = np.diff(edges) * 0.88
    threshold = 1e-1
    left = r < threshold
    close = r >= threshold
    left_pct = 100 * left.sum() / total
    close_pct = 100 * close.sum() / total

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 12,
        "axes.titlesize": 18,
        "axes.labelsize": 14,
        "savefig.dpi": 300,
    })
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    colors = ["#176b87" if c < -1 else "#b9c7d4" for c in centers]
    ax.bar(centers, counts, width=widths, color=colors, edgecolor="white", linewidth=0.8, align="center")

    # Directly emphasize the core interval without adding a legend or second axis.
    ax.axvspan(-6, -1, color="#176b87", alpha=0.07, zorder=0)
    ymax = max(counts.max(), 1)
    ax.text(-3.0, ymax * 1.08,
            f"{left_pct:.0f}% of systems have R < 1/10",
            ha="center", va="bottom", fontsize=15, color="#12566b", weight="bold")
    ax.text(-0.72, ymax * 0.72,
            f"{close_pct:.0f}% of systems have R ≥ 1/10\nClose-companion systems",
            ha="center", va="center", fontsize=13, color="#536574", weight="bold")
    ax.axvline(-1, color="#536574", linestyle="--", linewidth=1.5)
    median_log = float(np.median(log_r))
    ax.axvline(median_log, color="#b22222", linestyle=":", linewidth=1.8)
    ax.text(median_log + .06, ymax * .72,
            f"Median R = {10**median_log:.2g}", color="#8d1f1f",
            fontsize=11, rotation=90, va="center", ha="left",
            bbox=dict(boxstyle="round,pad=.2", fc="white", ec="#d9a0a0", alpha=.9))

    tick_positions = np.arange(-5, 1)
    tick_labels = [
        "$10^{-5}$\n(1/100,000)",
        "$10^{-4}$\n(1/10,000)",
        "$10^{-3}$\n(1/1,000)",
        "$10^{-2}$\n(1/100)",
        "$10^{-1}$\n(1/10)",
        "$10^{0}$\n(1/1)",
    ]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.set_xlim(-5.35, 0.05)
    ax.set_ylim(0, ymax * 1.36)
    ax.set_xlabel("Orbit Ratio R = Planet Distance (a) / Companion Distance (D)", labelpad=14)
    ax.set_ylabel(f"Number of Systems (Out of {total})")
    ax.set_title("Distribution of Orbit Ratio R in Multi-Star Systems", weight="bold", pad=18)
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#334e68")
    ax.spines["bottom"].set_color("#334e68")
    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUTPUT_FILE}")
    print(f"N={total}; R < 1e-1: {left.sum()} ({left_pct:.2f}%); R >= 1e-1: {close.sum()} ({close_pct:.2f}%); median R={10**median_log:.6g}")


if __name__ == "__main__":
    main()
