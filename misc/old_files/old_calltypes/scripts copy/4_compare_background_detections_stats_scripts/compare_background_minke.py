#%%
from pathlib import Path
import numpy as np
import pandas as pd

#%% Import background and minke .csv files (with interpolated enviro vars + arcgis calculations)
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
bg_path = Path("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_gis/LF_background_GIScalc_UVI2_Around_STX_20250306.csv")
bg = pd.read_csv(bg_path)

#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
mk_path = Path("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_gis/minke_GIScalc_UVI2_Around_STX_20250306.csv")
mk = pd.read_csv(mk_path)

print("BACKGROUND (available) shape:", bg.shape)
print("MINKE (used) shape:", mk.shape)

#༚ DEFINE VARIABLES TO BE COMPARED
#%% Environmental (glider-measured)
ENV_VARS = [
    "glider_depth_m",
    "water_temperature_c",
    "salinity_psu",
    "oxygen_concentration_μmol_L",
]

# Geomorphic (GIS-derived)
#𖠜 CHANGE VARS TO "RASTERDEPTH_m" AND "RASTERSLOPE_deg" IN FINAL VERSION OF SCRIPT
GEO_VARS = [
    "RASTERDEPTH_10m",    # bathymetric depth
    "RASTERSLOPE_10m",  # bathymetric slope (degrees)
    "NEAR_DIST",        # distance to nearest shoreline (meters)
]

COMPARE_VARS = ENV_VARS + GEO_VARS

#%% Check all variables exist in both dfs (they definitely should)
missing_bg = [c for c in COMPARE_VARS if c not in bg.columns]
missing_mk = [c for c in COMPARE_VARS if c not in mk.columns]

if missing_bg or missing_mk:
    print("\n⚠️ Column name mismatch detected.")
    if missing_bg:
        print("Missing from BACKGROUND:", missing_bg)
    if missing_mk:
        print("Missing from MINKE:", missing_mk)
    print("\nHere are the BACKGROUND columns:\n", list(bg.columns))
    print("\nHere are the MINKE columns:\n", list(mk.columns))
else:
    print("\n✅ All comparison variables found in both datasets.")

#%% Ensure all compare vars are numeric (should already be but just in case)
for c in COMPARE_VARS:
    bg[c] = pd.to_numeric(bg[c], errors="coerce")
    mk[c] = pd.to_numeric(mk[c], errors="coerce")

# Check if coercion created any missing values
na_bg = bg[COMPARE_VARS].isna().sum().sum()
na_mk = mk[COMPARE_VARS].isna().sum().sum()
print("\nTotal NA across compare vars:")
print("BACKGROUND:", na_bg)
print("MINKE:", na_mk)

#%% Add dataset labels + keep only what we need for comparisons
bg_cmp = bg[COMPARE_VARS].copy()
bg_cmp["dataset"] = "available_background"

mk_cmp = mk[COMPARE_VARS + ["call_density_rank"]].copy()
mk_cmp["dataset"] = "used_minke"

print("\nClean compare-ready dfs:")
print("bg_cmp:", bg_cmp.shape, "| columns:", list(bg_cmp.columns))
print("mk_cmp:", mk_cmp.shape, "| columns:", list(mk_cmp.columns))


#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
#· DESCRIPTIVE STATISTICS SUMMARY TABLE                                                             
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
#%% Function to compute basic descriptive stats for background vs minke conditions
def summarize_series(x: pd.Series) -> dict:
    x = pd.to_numeric(x, errors="coerce").dropna()
    # compute 25th percentile (Q1) and 75th percentile (Q3)
    q1 = x.quantile(0.25)
    q3 = x.quantile(0.75)
    # return dictionary where each key is a label and each value is one statistic
    return {
        "n": int(x.shape[0]),
        "mean": float(x.mean()),
        "sd": float(x.std(ddof=1)),
        "median": float(x.median()),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "min": float(x.min()),
        "max": float(x.max()),
    }

#%% Standardized Mean Difference (Cohen-like d using pooled SD)
#༝ SMD = (mean_used − mean_available) / pooled_SD --SOOO- it tells us *how many “standard deviations” higher or lower the minke-detection conditions are compared to the mission-available conditions*
#༝ positive SMD means minke detections tended to occur at higher values than were typical/available; negative SMD means detections tended to occur at lower values
#༝ magnitude rough guide: 0.2 small, 0.5 medium, 0.8+ large
def smd(x: pd.Series, y: pd.Series) -> float:
    # x = available/background values for a variable
    x = pd.to_numeric(x, errors="coerce").dropna().to_numpy()
    # y = used/minke values for the same variable
    y = pd.to_numeric(y, errors="coerce").dropna().to_numpy()
    # if either group has fewer than 2 values can’t compute sample variance, so returns NA (not enough data)
    if len(x) < 2 or len(y) < 2:
        return np.nan
    # vx = variance of available/background (ddof=1 means “sample” variance)
    vx = np.var(x, ddof=1)
    # vy = variance of used/minke
    vy = np.var(y, ddof=1)
    # pooled standard deviation
    pooled = np.sqrt(((len(x) - 1) * vx + (len(y) - 1) * vy) / (len(x) + len(y) - 2))
    if pooled == 0:
        return np.nan
    # used - available
    return float((np.mean(y) - np.mean(x)) / pooled)

#%% Cliff's delta
#༝ probability(y>x) - probability(y<x), ranges [-1,1] (here: y = used, x = available)
#༝ nonparametric effect size that measures how often values from the used group are higher than the available group minus how often they’re lower (range −1 to +1)
#༝ positive means detections tends to be higher than background
def cliffs_delta(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce").dropna().to_numpy()
    y = pd.to_numeric(y, errors="coerce").dropna().to_numpy()
    if len(x) == 0 or len(y) == 0:
        return np.nan
    # efficient-ish computation: sort x, then count how many x each y exceeds
    x_sorted = np.sort(x)
    n_x = len(x_sorted)
    n_y = len(y)
    # for each y, number of x < y is idx from searchsorted
    less_counts = np.searchsorted(x_sorted, y, side="left")
    # for each y, number of x <= y is idx from searchsorted with side="right"
    leq_counts = np.searchsorted(x_sorted, y, side="right")
    # pairs where y > x: sum( #x < y )
    n_gt = int(less_counts.sum())
    # pairs where y < x: sum( #x > y ) = sum( n_x - #x <= y )
    n_lt = int((n_x - leq_counts).sum())
    denom = n_x * n_y
    return float((n_gt - n_lt) / denom)

#༚ CREATE TABLE 1 - DESCRIPTIVE STATS OF VARIABLES FOR BACKGROUND CONDITIONS VS DETECTIONS
#%% Create empty list to ???
rows = []

#%% Loop to build 1 row in table 1 per each variable and combine all those rows into a single summary dataframe
for var in COMPARE_VARS:
    a = summarize_series(bg_cmp[var])
    u = summarize_series(mk_cmp[var])
    row = {
        "Variable": var,
        # count
        "n_background": a["n"],
        "n_detections": u["n"],
        # mean
        "mean_background": a["mean"],
        "mean_detections": u["mean"],
        # standard deviation
        "sd_background": a["sd"],
        "sd_detections": u["sd"],
        # median
        "median_background": a["median"],
        "median_detections": u["median"],
        # first quartile
        "q1_background": a["q1"],
        "q1_detections": u["q1"],
        # third quartile
        "q3_background": a["q3"],
        "q3_detections": u["q3"],
        # interquartile range (IQR)
        "iqr_background": a["iqr"],
        "iqr_detections": u["iqr"],
        # minimum
        "min_background": a["min"],
        "min_detections": u["min"],
        # maximum
        "max_background": a["max"],
        "max_detections": u["max"],
        # effect sizes (used - available)
        "SMD_detections_minus_background": smd(bg_cmp[var], mk_cmp[var]),
        "Cliffs_delta_detections_vs_background": cliffs_delta(bg_cmp[var], mk_cmp[var])
    }
    rows.append(row)

table1 = pd.DataFrame(rows)

#%% Rename Variable col values to readable labels (ONLY in Table 1; does NOT change df column names)
var_label_map = {
    "glider_depth_m": "Glider depth (m)",
    "water_temperature_c": "Water temperature (°C)",
    "salinity_psu": "Salinity (PSU)",
    "oxygen_concentration_μmol_L": "Dissolved Oxygen (μmol/L)",
    "RASTERDEPTH_10m": "Bathymetric depth (m)",
    "RASTERSLOPE_10m": "Bathymetric slope (°)",
    "NEAR_DIST": "Distance to nearest shoreline (m)",
}

# Replace names where mapping exists; leave anything else unchanged
table1["Variable"] = table1["Variable"].map(var_label_map).fillna(table1["Variable"])

#%% Export table 1
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
t1_out_path = "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_stats_output/sumtable_minke_vs_background.csv"
table1.to_csv(t1_out_path, index=False)
print(f"\n✅ Exported: {t1_out_path}")
