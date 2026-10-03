# Beyond-Three-Suns

**Dynamic Dormancy in S-Type Planets of Multi-Star Systems**

A data-driven planetary-science project: using NASA Exoplanet Archive and the Washington Double Star (WDS) catalog to ask whether planets living around stars in multi-star systems behave like they have "only one sun."

---

## Research Question

Inspired by the "chaotic three-body world" of the science fiction novel *The Three-Body Problem*, this project asks a real-data question:

> For planets in multi-star systems (two or more stars), how stable are their orbits — do they sense multiple suns, or, because companions are far away, effectively only one?

## What I Did

1. **Query** confirmed S-type planets (orbiting a single primary) in multi-star systems from the NASA Exoplanet Archive (sy_snum ≥ 2, cb_flag = 0).
2. **Cross-match** each system to the WDS binary-star catalog to obtain the real angular separation of companion stars (`sep`, in arcsec), via VizieR.
3. **Convert** angular separation × system distance into a projected companion distance `D` (in AU).
4. **Define** the dimensionless ratio

   $$R = \frac{a_{\mathrm{planet}}}{D_{\mathrm{companion}}}$$

   which measures how small a planet's orbit is relative to how far away its companion star is.
5. **Estimate** the secular (long-term) perturbation timescale

   $$\tau_{\mathrm{sec}} \approx P_{\mathrm{planet}}\, \left(\frac{M_\star}{M_{\mathrm{comp}}}\right) R^{-3}$$

   and compare it to the main-sequence lifetime of the host star, `t_MS = 10¹⁰ (M★/M☉)^-2.5 yr`.

## Key Findings

- **R is almost always tiny** (`10⁻⁴`–`10⁻²`): observed multi-star planets orbit very close to their primary, far from the companion.
- **~2/3 of sampled systems** fall in the *secular active* regime (`τ_sec ≤ t_MS`) — the companion can perturb within the stellar lifetime; only ~1/3 are dynamically dormant (`τ_sec > t_MS`). This is under the conservative `q = M_comp/M_★ = 1` assumption.
- **The result is robust** to companion choice: using the nearest vs. widest companion both keep `R` in the `10⁻⁴`–`10⁻²` range.
- A fraction of the "all-tiny-R" pattern is **observational selection**: detection limits (transit/RV) and angular-resolution limits shape which systems are observable.

## Repository Structure

```
.
├── README.md
├── s_type_multistar_wds.py        # Main pipeline: NASA + WDS cross-match, computes R and τ_sec
├── make_charts.py                 # Generates the figures (slide0–3)
├── make_R_distribution.py         # R-distribution (ECDF/KDE) figure
├── make_geometry_schematic.py     # Geometric schematic of the a vs D hierarchy
├── verify_env.py                  # Environment sanity check
├── PSCompPars_2026.10.01_(nolessthan2).csv   # Raw NASA input (sy_snum ≥ 2, S-type)
├── s_type_multistar_planets_wds.csv          # Processed dataset (159 samples)
├── wds_match_cache.csv            # Cached WDS companion lookups
├── slide0–3_*.png                 # Publication-quality output charts
```

## How to Reproduce

### 1. Environment

Tested on Python 3.11 with conda:

```bash
conda create -n beyond_threesuns python=3.11 -y
conda activate beyond_threesuns
pip install numpy pandas scipy matplotlib astropy requests
python verify_env.py
```

### 2. Run the data pipeline

```bash
python s_type_multistar_wds.py
```

Reads the local NASA CSV, cross-matches with WDS, computes `R`, `τ_sec`, filters, and writes `s_type_multistar_planets_wds.csv`.

### 3. Generate figures

```bash
python make_charts.py
```

Writes the publication-quality output figures.

## Data Sources

- **NASA Exoplanet Archive — Planetary Systems Composite Parameters (PSCompPars):** https://exoplanetarchive.ipac.caltech.edu
- **Washington Double Star (WDS) catalog via VizieR `B/wds`:** https://vizier.cds.unistra.fr

## Assumptions & Caveats

- `D` is a **projected** separation (angular sep × distance); the true 3-D separation is ≥ this value, so `R` is systematically **overestimated**.
- `τ_sec` is an **order-of-magnitude** estimate; the companion mass ratio is assumed `q = M_comp/M_★ = 1` by default.
- `t_MS = 10¹⁰ (M★/M☉)^-2.5 yr` is a standard mass–lifetime scaling law (order-of-magnitude).
- The "active vs dormant" boundary is `τ_sec = t_MS`; it is a physical timescale comparison, not a rigorous Hill-stability criterion.

## Author

A self-directed research project in planetary science. Contact via GitHub.
