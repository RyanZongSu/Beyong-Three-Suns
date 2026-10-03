"""NASA multistar planets cross-matched with WDS physical companions."""
from __future__ import annotations
import io, logging, random, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np, pandas as pd, requests
from astropy.coordinates import SkyCoord
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_DIR = Path(__file__).resolve().parent
NASA_FILE = BASE_DIR / "PSCompPars_2026.10.01_(nolessthan2).csv"
OUTPUT_FILE = BASE_DIR / "s_type_multistar_planets_wds.csv"
CACHE_FILE = BASE_DIR / "wds_match_cache.csv"
VIZIER_URL = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
WDS_RADIUS_ARCSEC = 60.0
MAX_WORKERS = 2
REQUEST_TIMEOUT = 60
TEST_LIMIT: int | None = None  # Set to 20 for a test run; None runs all rows.
Q_ASSUMED = 1.0
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

def make_session():
    s = requests.Session()
    retry = Retry(total=5, connect=5, read=5, backoff_factor=1.5,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET", "POST"}),
                  respect_retry_after_header=True)
    a = HTTPAdapter(max_retries=retry); s.mount("https://", a); s.mount("http://", a)
    s.headers["User-Agent"] = "Beyond-Three-Suns-WDS-research/2.0"
    return s
HTTP = make_session()

def load_nasa():
    if not NASA_FILE.exists(): raise FileNotFoundError(f"NASA input file not found: {NASA_FILE}")
    df = pd.read_csv(NASA_FILE, comment="#")
    df.columns = [str(c).strip().lower() for c in df.columns]
    for c in ("ra", "dec", "sy_dist", "pl_orbsmax", "pl_orbper", "st_mass", "sy_snum"):
        if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
    p = df["pl_orbper"] / 365.25
    df["pl_orbsmax"] = df["pl_orbsmax"].fillna((df["st_mass"] * p**2) ** (1 / 3))
    req = ["hostname", "pl_name", "ra", "dec", "sy_dist", "pl_orbsmax", "pl_orbper", "sy_snum"]
    df = df.dropna(subset=req)
    df = df[(df.sy_snum >= 2) & (df.sy_dist > 0) & (df.pl_orbsmax > 0) & (df.pl_orbper > 0)]
    if "default_flag" in df: df = df[df.default_flag == 1]
    if "cb_flag" in df: df = df[(df.cb_flag == 0) | df.cb_flag.isna()]
    if TEST_LIMIT is not None:
        if not isinstance(TEST_LIMIT, int) or TEST_LIMIT <= 0: raise ValueError("TEST_LIMIT must be None or positive integer")
        df = df.head(TEST_LIMIT)
    return df.reset_index(drop=True)

def physical_mask(s):
    x = s.fillna("").astype(str).str.upper().str.strip()
    return x.str.match(r"^A(?:$|[\s,;/\-]*[A-Z0-9]+)") & x.ne("")

def query_wds(ra, dec):
    try:
        SkyCoord(ra, dec, unit="deg", frame="icrs")
        time.sleep(0.2 + random.uniform(0, .1))
        r = HTTP.get(VIZIER_URL, params={"-source":"B/wds", "-c":f"{ra:.8f} {dec:.8f}", "-c.rs":str(WDS_RADIUS_ARCSEC), "-out.max":"200", "-out.form":"mini"}, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        lines = [x for x in r.text.splitlines() if x.strip() and not x.startswith("#")]
        if len(lines) < 2: return np.nan, np.nan, "no_match"
        w = pd.read_csv(io.StringIO("\n".join(lines)), sep="\t"); w.columns = [str(c).strip().lower() for c in w.columns]
        comp = next((c for c in ("comp", "component") if c in w), None)
        sepcol = next((c for c in ("sep1", "sep", "separation") if c in w), None)
        if comp is None or sepcol is None: return np.nan, np.nan, "missing_component_or_sep1"
        w = w[physical_mask(w[comp])]
        sep = pd.to_numeric(w[sepcol], errors="coerce"); sep = sep[(sep > 0) & np.isfinite(sep)]
        return (float(sep.min()), float(sep.max()), "matched") if len(sep) else (np.nan, np.nan, "no_physical_companion")
    except (requests.RequestException, ValueError, pd.errors.ParserError) as e:
        log.warning("WDS query failed at (%.6f, %.6f): %s", ra, dec, e); return np.nan, np.nan, "request_error"

def crossmatch(nasa):
    nasa = nasa.copy(); nasa["coord_key"] = nasa.ra.round(7).astype(str) + "," + nasa.dec.round(7).astype(str)
    unique = nasa[["coord_key", "ra", "dec"]].drop_duplicates("coord_key")
    expected = ["coord_key", "sep_min", "sep_max", "wds_status", "search_radius_arcsec"]
    if CACHE_FILE.exists():
        cache = pd.read_csv(CACHE_FILE)
        # Old sep1-only caches did not apply the required Component filter.
        # Treat them as stale so every coordinate is rechecked under the new definition.
        if "sep_min" not in cache.columns and "sep1_arcsec" in cache.columns:
            log.info("Legacy WDS cache detected; rechecking coordinates with Component filtering")
            cache = pd.DataFrame(columns=expected)
        else:
            cache = cache.reindex(columns=expected, fill_value=np.nan)
        cache["search_radius_arcsec"] = pd.to_numeric(cache["search_radius_arcsec"], errors="coerce")
        cache = cache[cache.search_radius_arcsec == WDS_RADIUS_ARCSEC].drop_duplicates("coord_key", keep="last")
    else: cache = pd.DataFrame(columns=expected)
    pending = unique[~unique.coord_key.isin(set(cache.coord_key.astype(str)))]
    log.info("Unique coordinates: %d; cache hits: %d; pending: %d", len(unique), len(unique)-len(pending), len(pending))
    def worker(row):
        key, ra, dec = row; a, b, status = query_wds(float(ra), float(dec))
        return {"coord_key":key, "sep_min":a, "sep_max":b, "wds_status":status, "search_radius_arcsec":WDS_RADIUS_ARCSEC}
    rows = []; total = len(pending)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(worker, row) for row in pending.itertuples(index=False, name=None)]
        for done, f in enumerate(as_completed(futures), 1):
            rows.append(f.result())
            if done % 10 == 0 or done == total: log.info("[Progress: %d/%d (%.1f%%)]", done, total, 100*done/total if total else 100)
    if rows:
        cache = pd.concat([cache, pd.DataFrame(rows)], ignore_index=True).reindex(columns=expected, fill_value=np.nan).drop_duplicates("coord_key", keep="last")
        cache.to_csv(CACHE_FILE, index=False); log.info("WDS cache saved: %s", CACHE_FILE)
    return nasa.merge(cache[expected], on="coord_key", how="left")

def calculate(df):
    out = df.copy()
    for c in ("sep_min", "sep_max", "sy_dist", "pl_orbsmax", "pl_orbper"): out[c] = pd.to_numeric(out[c], errors="coerce")
    out["D_proj_AU"] = out.sep_min * out.sy_dist
    out["R"] = pd.to_numeric(out.pl_orbsmax / out.D_proj_AU, errors="coerce")
    valid = out.R.notna() & np.isfinite(out.R) & (out.R > 0) & (out.R < 1)
    out = out.loc[valid].copy()  # Filter before R**-3.
    out["pl_orbper_yr"] = out.pl_orbper / 365.25; out["q_assumed"] = Q_ASSUMED
    out["tau_sec_q1_yr"] = out.pl_orbper_yr * out.R.pow(-3) / Q_ASSUMED
    return out.replace([np.inf, -np.inf], np.nan).dropna(subset=["tau_sec_q1_yr"])

def main():
    nasa = load_nasa(); log.info("NASA S-type multistar planet records: %d", len(nasa))
    m = crossmatch(nasa); n = m.sep_min.notna().sum()
    log.info("Physical WDS companion matches: %d/%d (%.2f%%)", n, len(m), 100*n/len(m))
    out = calculate(m)
    if out.empty: raise RuntimeError("No records survived physical R and tau_sec filters")
    log.info("Final valid samples: %d", len(out))
    log.info("R (sep_min): min=%.6g max=%.6g median=%.6g q25=%.6g q75=%.6g", out.R.min(), out.R.max(), out.R.median(), out.R.quantile(.25), out.R.quantile(.75))
    log.info("Mean log10(R): %.6f", np.log10(out.R).mean())
    log.info("Median tau_sec_q1_yr: %.6e yr (order-of-magnitude estimate assuming q = M_comp/M_star = 1.0)", out.tau_sec_q1_yr.median())
    out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8"); log.info("Saved final dataset: %s", OUTPUT_FILE)

if __name__ == "__main__": main()
