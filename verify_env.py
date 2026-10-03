# Verify the Python environment and inspect the Beyond Three Suns dataset.
import numpy as np
import pandas as pd
import scipy
import matplotlib
import astropy

print("=" * 52)
print("Environment OK:")
print(f"  numpy:      {np.__version__}")
print(f"  pandas:     {pd.__version__}")
print(f"  scipy:      {scipy.__version__}")
print(f"  matplotlib: {matplotlib.__version__}")
print(f"  astropy:    {astropy.__version__}")
print("=" * 52)

CSV = "PSCompPars_2026.09.29_13.58.01.csv"
df = pd.read_csv(CSV, comment="#")
print(f"Dataset loaded: {df.shape[0]} systems x {df.shape[1]} columns")
print("Host stars per system (sy_snum) distribution:")
print(df["sy_snum"].value_counts().sort_index())
n_multi = int((df["sy_snum"] >= 3).sum())
print(f"Systems with >= 3 host stars (Beyond Three Suns): {n_multi}")
print("Verify OK.")
