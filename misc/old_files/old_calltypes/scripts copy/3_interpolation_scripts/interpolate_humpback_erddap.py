'''
This script interpolates the latitude, longitude, depth of glider (m), and surrounding water temperature (°C), salinity (PSU), and dissolved oxygen concentration (μmol/L) for each acoustic detection of a single species during a single mission. Values are interpolated using datetime data present in both the detections dataframe (created through acoustic analysis) and the ERDDAP dataframe (data collected by the glider and attached scientific sensors continuously throughout the mission).

Input detections .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed; input ERDDAP .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/missionname/data/2_data_processed/erddap_processed
Output interpolated detections .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/4_data_interpolated

𖠺 Created by Keiley Gregory on February 10, 2026
Last updated on March 2, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION

#%%
from pathlib import Path
import pandas as pd
import numpy as np

#%% Import ERDDAP and species detections CSVs
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
erddap_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/erddap_processed/CLEAN_erddap_UVI2_Around_STX_20250306.csv")
erddap_raw = pd.read_csv(erddap_path)

#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
whaledetections_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/humpback_analyzed_UVI2_Around_STX_20250306.csv")
wd_raw = pd.read_csv(whaledetections_path)

#%% Variables to interpolate from ERDDAP df
ENV_VARS_TO_INTERP = [
    "glider_depth_m",
    "water_temperature_C",
    "salinity_PSU",
    "oxygen_concentration_μmol_L"
]

LAT = "latitude"
LON = "longitude"

#%% Define date-time cols to match by in each df
erddap_dt_col   = "datetime_UTC"
wd_start_dt_col = "start_datetime_UTC"
wd_end_dt_col   = "end_datetime_UTC"
wd_av_dt_col    = "av_datetime_UTC"

#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#· PARSE/NORMALIZE DATE-TIME VALUES TO datetime64[ns, UTC]                                                 
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#%% Create copies of raw dfs
erddap = erddap_raw.copy()
wd = wd_raw.copy()

# Store raw WD row count + create persistent row id (so removed rows can be reported)
wd_n_raw = len(wd)
wd["wd_row_id"] = np.arange(len(wd), dtype=np.int64)

#%% Convert date-time cols data type
erddap[erddap_dt_col] = pd.to_datetime(erddap[erddap_dt_col], utc=True, errors="coerce")

for c in [wd_start_dt_col, wd_end_dt_col, wd_av_dt_col]:
    if c not in wd.columns:
        raise KeyError(f"Detections df is missing required datetime column: {c}")
    wd[c] = pd.to_datetime(wd[c], utc=True, errors="coerce")

# Print warning message if any timestamps in either df could not be parsed
if erddap[erddap_dt_col].isna().any():
    bad = erddap.loc[erddap[erddap_dt_col].isna(), [erddap_dt_col]].head(10)
    raise ValueError(
        f"Some ERDDAP {erddap_dt_col} values could not be parsed. Example:\n{bad}"
    )
for c in [wd_start_dt_col, wd_end_dt_col, wd_av_dt_col]:
    if wd[c].isna().any():
        bad = wd.loc[wd[c].isna(), [c]].head(10)
        raise ValueError(
            f"Some WD {c} values could not be parsed. Example:\n{bad}"
        )


#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#· COLLAPSE DUPLICATE ERDDAP ROWS WITH EXACT SAME DATE-TIME BY AVERAGING VALUES + SORT ROWS BY DATETIME    
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#%% Keep only columns in ERDDAP df used in interpolation; print warning message if any missing
ERDDAP_VARS_TO_KEEP = [LAT, LON] + ENV_VARS_TO_INTERP

missing_cols = [c for c in ERDDAP_VARS_TO_KEEP if c not in erddap.columns]
if missing_cols:
    raise KeyError(f"ERDDAP is missing required columns: {missing_cols}")

erddap_refinecols = erddap[[erddap_dt_col] + ERDDAP_VARS_TO_KEEP].copy()

# Count duplicate rows and unique rows before collapsing (for QC print message at end of script)
n_dup_rows = int(erddap_refinecols[erddap_dt_col].duplicated(keep=False).sum())
n_unique_before = int(erddap_refinecols[erddap_dt_col].nunique())

#%% Collapse duplicate ERDDAP rows (exact same datetime_UTC) by averaging numeric values (*ignores non-numeric columns (numeric_only=True)) AND enforce sorting
erddap_nodup = (
    erddap_refinecols
    .groupby(erddap_dt_col, as_index=False)[ERDDAP_VARS_TO_KEEP]
    .mean(numeric_only=True)
    .sort_values(erddap_dt_col)
    .reset_index(drop=True)
).copy()

# Count unique rows after collapsing (for QC print message at end of script)
n_unique_after = int(erddap_nodup[erddap_dt_col].nunique())


#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#· INTERPOLATE ERDDAP VARIABLES TO EACH DETECTION ROW BY DATE-TIME                                         
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#%% Function to interpolate a single variable from nearest *NON-NA* ERDDAP points onto detection times
def interpolate_from_non_na(erddap_df: pd.DataFrame, time_col: str, value_col: str, target_times: pd.Series) -> pd.Series:
    # build time-indexed series (if a variable is NA for a datetime stamp in ERDDAP df, that dt stamp gets dropped ONLY from that variable's series but REMAINS in all other variable's series that have a value for that dt stamp)
    s = erddap_df.set_index(time_col)[value_col].sort_index().dropna()
    # if ERDDAP has no valid values at all for this variable, return NA for all rows
    if s.empty:
        return pd.Series(pd.NA, index=target_times.index, dtype="Float64")
    # create combined index of (non-NA ERDDAP times) U (detection times)
    combined_index = s.index.union(target_times)
    # reindex, interpolate in time, and fill edges with nearest available non-NA
    s2 = s.reindex(combined_index).sort_index()
    s2 = s2.interpolate(method="time")  # uses nearest non-NA bracketing points
    s2 = s2.ffill().bfill()             # edge detections use single nearest non-NA (ffill() = forward fill; bfill() = backward fill)
    # return values at detection times, aligned to target_times index
    out = s2.reindex(target_times).to_numpy()
    return pd.Series(out, index=target_times.index)

#%% Create wd_out df with desired cols (dt cols to match by defined at beginning of script + string acoustics/taxonomy/call type cols)
wd_out = wd.copy()

#%%
#༚ INTERPOLATE LAT AND LON FOR START, END, AND AVERAGE DATETIME STAMPS IN BACKGROUND CONDITIONS DF
start_times = wd[wd_start_dt_col]
end_times   = wd[wd_end_dt_col]
av_times    = wd[wd_av_dt_col]

wd_out["start_latitude"]  = interpolate_from_non_na(erddap_nodup, erddap_dt_col, LAT, start_times).values
wd_out["end_latitude"]    = interpolate_from_non_na(erddap_nodup, erddap_dt_col, LAT, end_times).values
wd_out["av_latitude"]     = interpolate_from_non_na(erddap_nodup, erddap_dt_col, LAT, av_times).values

wd_out["start_longitude"] = interpolate_from_non_na(erddap_nodup, erddap_dt_col, LON, start_times).values
wd_out["end_longitude"]   = interpolate_from_non_na(erddap_nodup, erddap_dt_col, LON, end_times).values
wd_out["av_longitude"]    = interpolate_from_non_na(erddap_nodup, erddap_dt_col, LON, av_times).values

#%%
#༚ INTERPOLATE ENVIRONMENTAL VARIABLES FOR AVERAGE DATETIME STAMP ONLY
for v in ENV_VARS_TO_INTERP:
    wd_out[v] = interpolate_from_non_na(erddap_nodup, erddap_dt_col, v, av_times).values

#%% QC count after interpolation BEFORE dedup
n_rows_post_interp_pre_dedup = len(wd_out)


#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#· REMOVE **EXACT DUPLICATES IN ALL INTERPOLATED COLUMNS** ANYWHERE IN DF                                  
#· keep ONE row per duplicate-value group: the one whose av_datetime_UTC is closest to a real ERDDAP timestamp
#· (prevents ArcGIS point overlap when mapping -and- prevents skewed data from multiple exact same enviro var values all interpolated from same row in ERDDAP data)
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#%% Define full set of interpolated columns that *MUST be unique as a group* for a row to be considered an exact duplicate
interp_cols = ["start_latitude", "end_latitude", "av_latitude", "start_longitude", "end_longitude", "av_longitude"] + ENV_VARS_TO_INTERP

#%% Helper function to compute absolute time delta to nearest ERDDAP timestamp (vectorized)
def nearest_erddap_abs_timedelta(erddap_times: pd.Series, target_times: pd.Series) -> pd.Series:
    et = pd.Series(erddap_times).dropna().sort_values().to_numpy()
    tt = pd.Series(target_times).to_numpy()
    if len(et) == 0:
        return pd.Series(pd.NaT, index=target_times.index)
    # searchsorted gives insertion points; nearest is either left neighbor or right neighbor
    pos = np.searchsorted(et, tt, side="left")
    left_idx = np.clip(pos - 1, 0, len(et) - 1)
    right_idx = np.clip(pos, 0, len(et) - 1)
    left_dt = et[left_idx]
    right_dt = et[right_idx]
    # absolute timedelta to each candidate neighbor
    d_left = np.abs(tt - left_dt)
    d_right = np.abs(right_dt - tt)
    # choose smaller absolute delta
    d = np.minimum(d_left, d_right)
    return pd.Series(d, index=target_times.index)

#%% Find duplicate groups (*EXACT MATCH across ALL interpolated columns*)
dup_mask_all_interp = wd_out.duplicated(subset=interp_cols, keep=False)
n_dup_rows_all_interp = int(dup_mask_all_interp.sum())

# Create empty df to append only if duplicate rows exist
removed_dup_rows = pd.DataFrame()
n_removed = 0

#%% Determine closest ("best") row per duplicate group and drop all others
if n_dup_rows_all_interp > 0:
    # score each row by closeness of av_datetime_UTC to the nearest ERDDAP timestamp
    wd_out["_abs_dt_to_nearest_erddap"] = nearest_erddap_abs_timedelta(erddap_nodup[erddap_dt_col], wd_out[wd_av_dt_col])
    # if any deltas are missing (shouldn’t happen), push them to the bottom (worst); avoid timedelta overflow; use a large-but-safe timedelta so NaTs sort last
    wd_out["_abs_dt_to_nearest_erddap"] = wd_out["_abs_dt_to_nearest_erddap"].fillna(pd.Timedelta(days=100_000))
    # within each duplicate-value group, keep row with smallest time delta (tie-breaker: keep the latest start_datetime_UTC, then highest wd_row_id for deterministic behavior)
    dup_df = wd_out.loc[dup_mask_all_interp].copy()
    # sort so "best" row per group comes first
    dup_df = dup_df.sort_values(by=["_abs_dt_to_nearest_erddap", wd_start_dt_col, "wd_row_id"], ascending=[True, False, False], kind="mergesort")
    # pick first row per identical interpolated-values group
    keep_idx = (dup_df.groupby(interp_cols, dropna=False, sort=False, as_index=False).head(1).index)
    # remove everything else in the duplicated set (besides first "best" row)
    remove_idx = dup_df.index.difference(keep_idx)
    #update QC counter
    n_removed = int(len(remove_idx))
    # store removed rows for QC reporting
    removed_dup_rows = (
        wd_out.loc[remove_idx, ["wd_row_id", wd_start_dt_col, wd_end_dt_col, wd_av_dt_col] + interp_cols]
        .sort_values(by=wd_av_dt_col, kind="mergesort")
        .reset_index(drop=True)
    )
    # apply removal
    wd_out = wd_out.drop(index=remove_idx).reset_index(drop=True)
    # cleanup helper column
    wd_out = wd_out.drop(columns=["_abs_dt_to_nearest_erddap"], errors="ignore")


#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#· QC SUMMARY REPORT                                                                                       
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#%% Calculate summary counts for QC print out message using "nearest non-NA" interpolation method (per variable)
def qc_counts_non_na(erddap_df: pd.DataFrame, time_col: str, value_col: str, target_times: pd.Series):
    s = erddap_df.set_index(time_col)[value_col].sort_index().dropna()
    n_total = len(target_times)
    # if ERDDAP has NO non-NA values for this variable, everything will be missing
    if s.empty:
        return n_total, 0, 0, 0
    
    # exact match cases = target time exactly equals a non-NA ERDDAP timestamp for this variable
    exact_mask = target_times.isin(s.index)

    # edge cases = target time outside non-NA time span for this variable (so ffill/bfill used)
    t_min = s.index.min()
    t_max = s.index.max()
    edge_mask = (target_times < t_min) | (target_times > t_max)

    # true interpolation cases = target datetime within non-NA ERDDAP range but NOT exact match (true interpolation cases calculated by "interpolate(method="time")")
    interp_mask = (~exact_mask) & (~edge_mask)
    return n_total, int(exact_mask.sum()), int(interp_mask.sum()), int(edge_mask.sum())

#%% Print QC summary message
print("\n==================== QC REPORT (per variable) ====================")
print(f"Raw detection rows total (input file):             {wd_n_raw:,}")
print(f"Rows after interpolation (pre-dedup):              {n_rows_post_interp_pre_dedup:,}")
print(f"Rows after removing exact duplicates (ALL interp): {len(wd_out):,}")
print("-----------------------------------------------------")
print(f"ERDDAP rows with duplicate timestamps (raw count): {n_dup_rows:,}")
print(f"ERDDAP unique timestamps before collapse:          {n_unique_before:,}")
print(f"ERDDAP unique timestamps after collapse:           {n_unique_after:,}")
print("-----------------------------------------------------")
print(f"Exact-duplicate rows detected across ALL interp cols: {n_dup_rows_all_interp:,}")
print(f"Exact-duplicate rows removed:                        {n_removed:,}")

# for QC after dedup, use post-dedup time series (counts now match rows kept)
start_times_qc = wd_out[wd_start_dt_col]
end_times_qc   = wd_out[wd_end_dt_col]
av_times_qc    = wd_out[wd_av_dt_col]

# env vars (av dt stamp)
for v in ENV_VARS_TO_INTERP:
    n_total, n_exact, n_interp, n_edge = qc_counts_non_na(erddap_nodup, erddap_dt_col, v, av_times_qc)
    print(f"\nVariable: {v}  (target = av_datetime_UTC)")
    print(f"WD rows total:                           {n_total:,}")
    print(f"Exact datetime matches (best case):      {n_exact:,}")
    print(f"Interpolated between ERDDAP points:      {n_interp:,}")
    print(f"Edge rows filled with nearest ERDDAP:    {n_edge:,}")

# lat/lon (start + end + AV dt stamps)
for label, tseries in [("start_datetime_UTC", start_times_qc), ("end_datetime_UTC", end_times_qc), ("av_datetime_UTC", av_times_qc),]:
    for v in [LAT, LON]:
        n_total, n_exact, n_interp, n_edge = qc_counts_non_na(erddap_nodup, erddap_dt_col, v, tseries)
        print(f"\nVariable: {v}  (target = {label})")
        print(f"WD rows total:                           {n_total:,}")
        print(f"Exact datetime matches (best case):      {n_exact:,}")
        print(f"Interpolated between ERDDAP points:      {n_interp:,}")
        print(f"Edge rows filled with nearest ERDDAP:    {n_edge:,}")

# if applicable, show which rows in duplicate groups were removed (by wd_row_id + datetimes)
if len(removed_dup_rows) > 0:
    print("\nRemoved rows (wd_row_id identifies original row in humpback_analyzed input file):")
    # print full table (but avoid spam in rare case that duplicate rmeoval is large)
    if len(removed_dup_rows) <= 200:
        print(removed_dup_rows.to_string(index=False))
    else:
        print(removed_dup_rows.head(100).to_string(index=False))
        print("\n... (truncated) ...\n")
        print(removed_dup_rows.tail(100).to_string(index=False))

print("\n===================================================\n")
print("Missing counts in interpolated columns:")
print(wd_out[interp_cols].isna().sum().rename("n_missing"))


#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#· EXPORT INTERPOLATED DETECTION DATA AS CSV !                                                             
#· ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭
#%% Create copy of wd_out df to use for final output CSV
wd_final = wd_out.copy()

#%% Convert mission_name + taxonomy + call_type_description columns to pandas string dtype
string_cols = ["mission_name", "family", "genus", "species", "common_name", "call_type_description"]
wd_final[string_cols] = wd_final[string_cols].astype("string")

#%% Reorder columns for output CSV
wd_final = wd_final[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "spectrogram_range_kHz",
        "family",
        "genus",
        "species",
        "common_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC",
        "start_latitude",
        "end_latitude",
        "av_latitude",
        "start_longitude",
        "end_longitude",
        "av_longitude",
        "call_type",
        "call_type_description",
        "glider_depth_m",
        "water_temperature_C",
        "salinity_PSU",
        "oxygen_concentration_μmol_L"
    ]
]

#%% Check data type of all cols (one per line)
for col, dt in wd_final.dtypes.items():
    print(f"{col}: {dt}")

        #⋄ PRINT OUT SHOULD MATCH THIS:
        # mission_name: string
        # n_channels: int64
        # sample_rate_kHz: int64
        # bit_depth: int64
        # spectrogram_range_kHz: int64
        # family: string
        # genus: string
        # species: string
        # common_name: string
        # start_datetime_UTC: datetime64[ns, UTC]
        # end_datetime_UTC: datetime64[ns, UTC]
        # av_datetime_UTC: datetime64[ns, UTC]
        # start_latitude: float64
        # end_latitude: float64
        # av_latitude: float64
        # start_longitude: float64
        # end_longitude: float64
        # av_longitude: float64
        # call_type: int64
        # call_type_description: string
        # glider_depth_m: float64
        # water_temperature_C: float64
        # salinity_PSU: float64
        # oxygen_concentration_μmol_L: float64

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
wd_final = wd_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Export CSV with detection mins with interpolated data!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
out_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/4_data_interpolated/humpback_interpolated_UVI2_Around_STX_20250306.csv")
wd_final.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")





###########################################################################################
# ==================== QC REPORT (per variable) ====================
# Raw detection rows total (input file):             1,721
# Rows after interpolation (pre-dedup):              1,721
# Rows after removing exact duplicates (ALL interp): 1,714
# -----------------------------------------------------
# ERDDAP rows with duplicate timestamps (raw count): 680,200
# ERDDAP unique timestamps before collapse:          1,371,537
# ERDDAP unique timestamps after collapse:           1,371,537
# -----------------------------------------------------
# Exact-duplicate rows detected across ALL interp cols: 8
# Exact-duplicate rows removed:                        7

# Variable: glider_depth_m  (target = av_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,187
# Interpolated between ERDDAP points:      526
# Edge rows filled with nearest ERDDAP:    1

# Variable: water_temperature_C  (target = av_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,152
# Interpolated between ERDDAP points:      561
# Edge rows filled with nearest ERDDAP:    1

# Variable: salinity_PSU  (target = av_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,152
# Interpolated between ERDDAP points:      561
# Edge rows filled with nearest ERDDAP:    1

# Variable: oxygen_concentration_μmol_L  (target = av_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,015
# Interpolated between ERDDAP points:      698
# Edge rows filled with nearest ERDDAP:    1

# Variable: latitude  (target = start_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,630
# Interpolated between ERDDAP points:      83
# Edge rows filled with nearest ERDDAP:    1

# Variable: longitude  (target = start_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,630
# Interpolated between ERDDAP points:      83
# Edge rows filled with nearest ERDDAP:    1

# Variable: latitude  (target = end_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,629
# Interpolated between ERDDAP points:      84
# Edge rows filled with nearest ERDDAP:    1

# Variable: longitude  (target = end_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,629
# Interpolated between ERDDAP points:      84
# Edge rows filled with nearest ERDDAP:    1

# Variable: latitude  (target = av_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,642
# Interpolated between ERDDAP points:      71
# Edge rows filled with nearest ERDDAP:    1

# Variable: longitude  (target = av_datetime_UTC)
# WD rows total:                           1,714
# Exact datetime matches (best case):      1,642
# Interpolated between ERDDAP points:      71
# Edge rows filled with nearest ERDDAP:    1

# Removed rows (wd_row_id identifies original row in humpback_analyzed input file):
#  wd_row_id        start_datetime_UTC          end_datetime_UTC           av_datetime_UTC  start_latitude  end_latitude  av_latitude  start_longitude  end_longitude  av_longitude  glider_depth_m  water_temperature_C  salinity_PSU  oxygen_concentration_μmol_L
#          0 2025-03-06 19:14:46+00:00 2025-03-06 19:15:46+00:00 2025-03-06 19:15:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822
#          1 2025-03-06 19:15:46+00:00 2025-03-06 19:16:46+00:00 2025-03-06 19:16:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822
#          2 2025-03-06 19:16:46+00:00 2025-03-06 19:17:46+00:00 2025-03-06 19:17:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822
#          3 2025-03-06 19:17:46+00:00 2025-03-06 19:18:46+00:00 2025-03-06 19:18:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822
#          4 2025-03-06 19:19:46+00:00 2025-03-06 19:20:46+00:00 2025-03-06 19:20:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822
#          5 2025-03-06 19:20:46+00:00 2025-03-06 19:21:46+00:00 2025-03-06 19:21:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822
#          6 2025-03-06 19:21:46+00:00 2025-03-06 19:22:46+00:00 2025-03-06 19:22:16+00:00       18.159154     18.159154    18.159154       -64.757156     -64.757156    -64.757156             0.0              27.3896     36.819275                      193.822

# ===================================================

# Missing counts in interpolated columns:
# start_latitude                 0
# end_latitude                   0
# av_latitude                    0
# start_longitude                0
# end_longitude                  0
# av_longitude                   0
# glider_depth_m                 0
# water_temperature_C            0
# salinity_PSU                   0
# oxygen_concentration_μmol_L    0
# Name: n_missing, dtype: int64
###########################################################################################
