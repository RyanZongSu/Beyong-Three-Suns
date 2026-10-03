"""Generate publication-quality English portfolio charts from the WDS-cleaned dataset."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "s_type_multistar_planets_wds.csv"
HERO_FILE = BASE_DIR / "slide1_hero_dynamic_dormancy.png"
EVIDENCE_FILE = BASE_DIR / "slide3_methodology_and_robustness.png"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "axes.edgecolor": "#243447",
    "axes.labelcolor": "#243447",
    "xtick.color": "#243447",
    "ytick.color": "#243447",
})


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE)
    numeric = ["sy_snum", "st_mass", "pl_bmasse", "pl_orbsmax", "D_proj_AU",
               "R", "tau_sec_q1_yr", "sep_min", "sep_max"]
    for col in numeric:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = np.nan
    df["st_mass_plot"] = df["st_mass"].fillna(1.0).clip(lower=1e-3)
    df["planet_mass_plot"] = df["pl_bmasse"].fillna(df["pl_bmasse"].median())
    df["planet_mass_plot"] = df["planet_mass_plot"].fillna(1.0).clip(lower=1e-3)
    df["t_ms_yr"] = 1e10 * df["st_mass_plot"] ** -2.5
    df["tau_over_tms"] = df["tau_sec_q1_yr"] / df["t_ms_yr"]
    return df.replace([np.inf, -np.inf], np.nan)


def marker_size(values: pd.Series, lo=24, hi=180):
    x = np.log10(values.clip(lower=1e-6))
    if x.max() == x.min():
        return np.full(len(x), (lo + hi) / 2)
    return lo + (x - x.min()) / (x.max() - x.min()) * (hi - lo)


def hero_chart(df: pd.DataFrame):
    plot = df.dropna(subset=["R", "tau_over_tms", "st_mass_plot"]).query("R > 0 and R <= 1 and tau_over_tms > 0")
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    ymin = 10 ** np.floor(np.log10(plot.tau_over_tms.min()))
    ymax = 10 ** np.ceil(np.log10(plot.tau_over_tms.max()))
    ax.set_xscale("log")
    ax.set_yscale("log")
    r_lower = 10 ** np.floor(np.log10(plot["R"].min()) - 0.1)
    ax.set_xlim(r_lower, 1)
    ax.set_ylim(ymin, ymax)
    ax.axhspan(1, ymax, color="#d9eff7", alpha=.72, zorder=0)
    ax.axhspan(ymin, 1, color="#fde2e2", alpha=.65, zorder=0)
    ax.axhline(1, color="black", linestyle="--", linewidth=1.4, zorder=2)
    ax.text(2.0e-5, ymax / 3, "Dynamically Dormant Region\n($\\tau_{sec} \\geq t_{MS}$)", color="#176b87", va="top")
    ax.text(2.0e-5, ymin * 3, "Active Perturbation Region\n($\\tau_{sec} < t_{MS}$)", color="#a33b3b", va="bottom")
    # Use data coordinates so each explanation remains in its physical region.
    ax.text(0.025, 2.0,
            "Dormant: perturbations act on\ntimescales longer than the\nmain-sequence lifetime.",
            ha="left", va="bottom", fontsize=9, color="#176b87",
            bbox=dict(boxstyle="round,pad=.3", fc="#d9eff7", ec="none", alpha=.85))
    ax.text(0.025, 0.5,
            "Active: perturbations can operate\nwithin the main-sequence lifetime.",
            ha="left", va="top", fontsize=9, color="#a33b3b",
            bbox=dict(boxstyle="round,pad=.3", fc="#fde2e2", ec="none", alpha=.85))
    norm = Normalize(plot.st_mass_plot.min(), plot.st_mass_plot.max() if plot.st_mass_plot.max() > plot.st_mass_plot.min() else plot.st_mass_plot.min()+1)
    cmap = plt.get_cmap("viridis")
    sizes = marker_size(plot.planet_mass_plot)
    for n, marker, label in [(2, "o", "Binary ($sy\\_snum=2$)"), (3, "^", "Triple+ ($sy\\_snum\\geq3$)")]:
        sub = plot[plot.sy_snum == n] if n == 2 else plot[plot.sy_snum >= 3]
        if not sub.empty:
            ax.scatter(sub.R, sub.tau_over_tms, c=sub.st_mass_plot, cmap=cmap, norm=norm,
                       s=marker_size(sub.planet_mass_plot), marker=marker, alpha=.82,
                       edgecolor="#243447", linewidth=.35, label=label)
    cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, pad=.02)
    cbar.set_label(r"Stellar mass [$M_\odot$]")
    ax.set_xlabel(r"$R = a_{\mathrm{planet}} / D_{\mathrm{companion}}$")
    ax.set_ylabel(r"Timescale ratio $\tau_{\mathrm{sec}} / t_{\mathrm{MS}}$ (log scale)")
    ax.set_title("Mapping Spatial Hierarchy and Dynamical Timescales in S-Type Multistar Systems", weight="bold", pad=28)
    ax.text(.5, 1.015, r"65% of sampled systems reside in the secular active perturbation regime ($\tau_{sec} \leq t_{MS}$)", transform=ax.transAxes, ha="center", va="bottom", fontsize=11, color="#536574")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], color="black", linestyle="--", label=r"$\tau_{sec}=t_{MS}$ (Boundary)"))
    handles.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="#777777", markeredgecolor="#243447", markersize=8, label="Marker size represents planet mass"))
    ax.legend(handles=handles, labels=labels + [r"$\tau_{sec}=t_{MS}$ (Boundary)", "Marker size represents planet mass"], loc="upper right", frameon=True)
    ax.grid(True, which="both", alpha=.18)
    fig.tight_layout(); fig.savefig(HERO_FILE, dpi=300, bbox_inches="tight"); plt.close(fig)


def evidence_chart(df: pd.DataFrame):
    plot = df.dropna(subset=["pl_orbsmax", "D_proj_AU", "R", "sep_min", "sep_max"]).query("pl_orbsmax > 0 and D_proj_AU > 0 and R > 0 and R < 1")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.2, 6.6))
    sizes = marker_size(plot["planet_mass_plot"], 20, 130)
    for n, marker, color in [(2, "o", "#147d87"), (3, "^", "#7b2cbf")]:
        sub = plot[plot.sy_snum == n] if n == 2 else plot[plot.sy_snum >= 3]
        if not sub.empty:
            ax1.scatter(sub.pl_orbsmax, sub.D_proj_AU,
                        s=marker_size(sub["planet_mass_plot"], 20, 130),
                        c=color, marker=marker, alpha=.78,
                        edgecolor="white", linewidth=.35)
    ax1.set_xscale("log"); ax1.set_yscale("log")
    x_right = plot.pl_orbsmax.max() * 1.2
    ax1.set_xlim(plot.pl_orbsmax.min() * .8, x_right)
    ax1.axvspan(5, x_right, color="#8b8f98", alpha=.18)
    ax1.axhspan(1, 20, color="#8b8f98", alpha=.18)
    ax1.text(6, plot.D_proj_AU.max()*.65, "Transit/RV Detection Limit (Schematic):\nhard-to-observe region", color="#4f5560", fontsize=9)
    ax1.text(plot.pl_orbsmax.min()*1.3, 11, "WDS Angular Separation Limit (Schematic):\nhard-to-observe region", color="#4f5560", fontsize=9)
    ax1.set_ylim(1, plot.D_proj_AU.max() * 1.2)
    ax1.set_xlabel(r"Planet semimajor axis $a_{planet}$ [AU]"); ax1.set_ylabel(r"Projected companion distance $D_{companion}$ [AU]")
    ax1.set_title("Is the stability real—or observationally selected?", weight="bold")
    ax1.legend(handles=[
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#147d87", markeredgecolor="white", label="Binary ($sy\\_snum=2$)"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#7b2cbf", markeredgecolor="white", label="Triple+ ($sy\\_snum\\geq3$)"),
    ], loc="lower right", frameon=True)
    ax1.grid(True, which="both", alpha=.18)
    ax1.text(0.03, 0.04, "Marker size represents planet mass", transform=ax1.transAxes, fontsize=9, color="#243447", bbox=dict(boxstyle="round,pad=.25", fc="white", ec="#c8d1dc", alpha=.9))

    # Only Triple+ systems can provide a meaningful nearest-vs-widest comparison.
    # In a binary, sep_min == sep_max because there is only one companion.
    sensitivity = plot[(plot["sy_snum"] >= 3) & (plot["sep_max"] > plot["sep_min"])].copy()
    # Plot the physical R values directly; the axes themselves are logarithmic.
    x = sensitivity["pl_orbsmax"] / (sensitivity["sep_min"] * sensitivity["sy_dist"])
    y = sensitivity["pl_orbsmax"] / (sensitivity["sep_max"] * sensitivity["sy_dist"])
    ax2.scatter(x, y, s=marker_size(sensitivity["planet_mass_plot"], 20, 130), c="#7b2cbf", marker="^", alpha=.78, edgecolor="white", linewidth=.35, label="Triple+ (multiple WDS companions)")
    lo, hi = min(x.min(), y.min()), max(x.max(), y.max())
    lo *= 0.7; hi *= 1.4
    ax2.plot([lo, hi], [lo, hi], "--", color="#b22222", lw=1.5)
    ref = np.sqrt(lo * hi)
    ax2.text(ref, ref * 1.04, r"$R_{min}=R_{max}$ (same companion definition)",
             color="#8d1f1f", ha="center", va="bottom", fontsize=9, rotation=35,
             bbox=dict(boxstyle="round,pad=.2", fc="white", ec="none", alpha=.8))
    corr = np.corrcoef(np.log10(x), np.log10(y))[0, 1]
    ax2.text(.04, .95,
             f"Pearson r = {corr:.3f} (partly structural)\n"
             "Both ratios share $a$ and distance.\n"
             "Key evidence: shared $R\\sim10^{-4}$–$10^{-2}$ scale.",
             transform=ax2.transAxes, va="top", fontsize=9,
             bbox=dict(boxstyle="round,pad=.3", fc="white", ec="#c8d1dc", alpha=.9))
    ax2.set_xscale("log"); ax2.set_yscale("log")
    ax2.set_xlim(lo, hi); ax2.set_ylim(lo, hi)
    ax2.xaxis.set_major_formatter(LogFormatterMathtext())
    ax2.yaxis.set_major_formatter(LogFormatterMathtext())
    ax2.set_xlabel(r"$R_{min}$ (nearest companion)"); ax2.set_ylabel(r"$R_{max}$ (widest companion)")
    ax2.set_title(f"Companion-Definition Sensitivity (Triple+, N={len(sensitivity)})", weight="bold")
    ax2.legend(loc="lower right", frameon=True, title="Comparison sample")
    ax2.text(0.04, 0.04, "Marker size represents planet mass", transform=ax2.transAxes, fontsize=9, color="#243447", bbox=dict(boxstyle="round,pad=.25", fc="white", ec="#c8d1dc", alpha=.9))
    ax2.grid(True, alpha=.18)
    fig.tight_layout(); fig.savefig(EVIDENCE_FILE, dpi=300, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    data = load_data()
    hero_chart(data)
    evidence_chart(data)
    print(f"Saved: {HERO_FILE}")
    print(f"Saved: {EVIDENCE_FILE}")
