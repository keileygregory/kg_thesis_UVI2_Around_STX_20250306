'''
This script interpolates the latitude and longitude of each detection point (across multiple profiles), as well as the glider depth and the at-depth and sea surface water temperature, salinity, and dissolved oxygen concentration (*within the matching profile only*) from the mission raw glider (ERDDAP) .nc files. All calculations are done with both standard and profile-based variables from the ERDDAP raw .nc files data. 

Input detections .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/3_data_analyzed/LF_analyzed; Input raw .nc files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/1_data_raw/erddap_raw
Output interpolated detections .csv file directory: Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/4_data_interpolated

𖠺 Created by Keiley Gregory on February 10, 2026
Last updated on July 15, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd
import numpy as np
import xarray as xr
import glob

#%% Import DETECTIONS csv
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
csv_raw = pd.read_csv(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/humpback_analyzed_UVI2_Around_STX_20250306.csv")

# Import ERDDAP **RAW .NC FILES**
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
nc_folder = r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/1_data_raw/erddap_raw"

#%% Create copy of wd_raw for edits
csv = csv_raw.copy()

#%% Create list of all .nc files in raw erddap data folder
nc_files = sorted(glob.glob(nc_folder + "/*.nc"))
# print files loaded for confirmation
print("Files found:", len(nc_files))
for f in nc_files:
    print(f)

#%% Create list to store data extracted from nc files in and define list of key variables
nc_dfs = []

#❋ Full set of raw .nc variables you want if available
wanted_vars = [
    "profile_time",
    "time",
    "profile_id",
    "latitude",
    "longitude",
    "profile_lat",
    "profile_lon",
    "depth",
    "temperature",
    "salinity",
    "oxygen_concentration"
]

#%% Read each raw .nc file separately, keep available variables, add missing expected columns as NA, then combine into one dataframe
#˓ NOTE: files missing some wanted_vars are still used — missing columns are filled with NaN (some variables are better than none)
for file in nc_files:
    ds = xr.open_dataset(file, engine="netcdf4")
    existing_vars = [v for v in wanted_vars if v in ds.variables]
    missing_vars  = [v for v in wanted_vars if v not in ds.variables]
    print("\n" + "=" * 80)
    print(f"FILE: {Path(file).name}")
    print(f"Variables found: {existing_vars}")
    if missing_vars:
        print(f"⚠️ Missing variables in this file: {missing_vars}")
    if not existing_vars:
        print("⚠️ No wanted variables found in this file. File skipped.")
        ds.close()
        continue
    df = ds[existing_vars].to_dataframe().reset_index()
    for col in wanted_vars:
        if col not in df.columns:
            df[col] = np.nan
    df = df[wanted_vars].copy()
    df["glider_nc_file"] = Path(file).name
    nc_dfs.append(df)
    ds.close()

# combine all .nc dataframes into one dataframe
if not nc_dfs:
    raise ValueError("No usable .nc files were read. Check variable names and file contents.")
nc_df = pd.concat(nc_dfs, ignore_index=True)

#%% Create numeric profile # column where each unique profile_id gets its own integer label (starting at 1)
nc_df["profile_id_enum"] = nc_df["profile_id"].factorize()[0] + 1

#%%
#˚ Double check that profile IDs are globally unique (aka each profile recorded during the mission has an id NOT shared with any other profiles recorded during this mission) and do NOT have any issues with identical profile ids being used for different profiles in separate .nc files (such as if profile id naming system restarted from same number in each separate .nc file)... (I don't think the glider would log data stupidly enough to mess this up, but check just to be safe)
_ids_per_file = nc_df.groupby("glider_nc_file")["profile_id"].nunique()
_n_files = nc_df["glider_nc_file"].nunique()
_n_unique_ids = nc_df["profile_id"].nunique()
_max_ids_in_a_file = _ids_per_file.max()
print(f"{'#' * 80}")
print("PROFILE_ID UNIQUENESS CHECK")
print(f"  Total .nc files:                  {_n_files}")
print(f"  Unique profile_id values:         {_n_unique_ids}")
print(f"  Max profile_ids in a single file: {_max_ids_in_a_file}")
print(f"{'#' * 80}")

#%% 
#❋ Subset desired variables from raw ERDDAP .nc files into combined df of all ERDDAP mission data
nc_subset = nc_df[
    [
        "profile_time",
        "time",
        "profile_id",
        "profile_id_enum",
        "glider_nc_file",
        "latitude",
        "longitude",
        "profile_lat",
        "profile_lon",
        "depth",
        "temperature",
        "salinity",
        "oxygen_concentration"
    ]
].copy()


#❥ 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟
#❥ PART ONE: INTERPOLATE LAT + LON FOR EACH ROW IN ACOUSTIC DF FROM NC FILE DATA **ACROSS PROFILES**              
#❥ lat/lon are interpolated ACROSS multiple profiles because (1) a location is required for ever single row in the acoustic df and (2) the GPS location is only recorded when the glider is at the surface, so it is interpolated regardless
#❥ 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟
#%% Subset .nc file data to only rows with VALID data in all 3 cols: time, latitude, longitude
nc_latlon = nc_subset[["time", "latitude", "longitude"]].dropna(
    subset=["time", "latitude", "longitude"]
).copy()

#%% Parse .nc 'time' col to datetime64 dt (and create QC counters for print message of rows that failed parsing)
_raw_nc_time = nc_latlon["time"].copy()
nc_latlon["time"] = pd.to_datetime(nc_latlon["time"], utc=True, errors='coerce')
_nc_time_failed = nc_latlon["time"].isna() & _raw_nc_time.notna()
# print warning message of any rows that failed parsing
if _nc_time_failed.any():
    print(f"\n[WARNING: FAILED PARSE] Failed rows in 'nc_latlon[\"time\"]' = {_nc_time_failed.sum()}")
    for _idx, _val in _raw_nc_time[_nc_time_failed].items():
        print(f"  Row {_idx}: {_val!r}")

#❋ If .nc data has multiple rows with SAME EXACT timestamp but different lat/lon values, *AVERAGE* the lat/lon values for all rows with matching timestamp and collapse to single column
#%% Remove duplicates
nc_latlon_nodup = nc_latlon.groupby("time", as_index=False)[["latitude", "longitude"]].mean()

# Sort by time so np.interp works correctly (groupby() can mess with original row order)
nc_latlon_nodup = nc_latlon_nodup.sort_values("time").reset_index(drop=True)

#%% Strip UTC tz and convert .nc 'time' col to numeric (seconds since epoch) for interpolation
nc_latlon_time_numeric = nc_latlon_nodup["time"].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[ns]").astype(np.int64).values / 1e9

# Compute .nc time bounds ONCE — used by all three interpolation blocks below
nc_latlon_time_min = nc_latlon_time_numeric.min()
nc_latlon_time_max = nc_latlon_time_numeric.max()

#✦ INTERPOLATE START_LATITUDE_DD AND START_LONGITUDE_DD COLS IN CSV DF FROM 'TIME', 'LATITUDE', AND 'LONGITUDE' VARIABLES IN .NC FILES DATA
#%% Parse start_datetime_UTC col to datetime64 dt (and create QC counters for print message of rows that failed parsing)
_raw_csv_startdt = csv["start_datetime_UTC"].copy()
csv["start_datetime_UTC"] = pd.to_datetime(csv["start_datetime_UTC"], utc=True, errors='coerce')
_csv_startdt_failed = csv["start_datetime_UTC"].isna() & _raw_csv_startdt.notna()
# print warning message of any rows that failed parsing
if _csv_startdt_failed.any():
    print(f"\n[WARNING: FAILED PARSE] Failed rows in 'csv[\"start_datetime_UTC\"]' = {_csv_startdt_failed.sum()}")
    for _idx, _val in _raw_csv_startdt[_csv_startdt_failed].items():
        print(f"  Row {_idx}: {_val!r}")

#%% Strip UTC tz and convert start_datetime_UTC col to numeric (seconds since epoch) for interpolation
csv_starttime_numeric = csv["start_datetime_UTC"].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[ns]").astype(np.int64).values / 1e9

#༝ Interpolate latitude and longitude
#%% np.interp = linear interpolation (*timestamps outside .nc files time range will be extrapolated to nearest endpoint value (end-clamped))
csv["start_latitude_DD"] = np.interp(
    csv_starttime_numeric,
    nc_latlon_time_numeric,
    nc_latlon_nodup["latitude"].values
)
csv["start_longitude_DD"] = np.interp(
    csv_starttime_numeric,
    nc_latlon_time_numeric,
    nc_latlon_nodup["longitude"].values
)

# track rows where CSV time falls OUTSIDE .nc time range for QC print out (*will all be END-CLAMPED to same lat/lon value matching lat/lon of first or last row in .nc data)
csv["start_interp_flag"] = "interpolated"
csv.loc[csv_starttime_numeric < nc_latlon_time_min, "start_interp_flag"] = "extrapolated_before"
csv.loc[csv_starttime_numeric > nc_latlon_time_max, "start_interp_flag"] = "extrapolated_after"

# print QC summary of lat/lon interpolation
print(f"{'#' * 80}")
print("START LAT/LON INTERPOLATION SUMMARY")
print(f"  Total CSV rows:        {len(csv)}")
print(f"  Interpolated:          {(csv['start_interp_flag'] == 'interpolated').sum()}")
print(f"  Extrapolated (before): {(csv['start_interp_flag'] == 'extrapolated_before').sum()}")
print(f"  Extrapolated (after):  {(csv['start_interp_flag'] == 'extrapolated_after').sum()}")
print(f"  Lat NaN count:         {csv['start_latitude_DD'].isna().sum()}")
print(f"  Lon NaN count:         {csv['start_longitude_DD'].isna().sum()}")
print(f"{'=' * 50}")

#✦ INTERPOLATE END_LATITUDE_DD AND END_LONGITUDE_DD COLS IN CSV DF FROM 'TIME', 'LATITUDE', AND 'LONGITUDE' VARIABLES IN .NC FILES DATA
#%% Parse end_datetime_UTC col to datetime64 dt (and create QC counters for print message of rows that failed parsing)
_raw_csv_enddt = csv["end_datetime_UTC"].copy()
csv["end_datetime_UTC"] = pd.to_datetime(csv["end_datetime_UTC"], utc=True, errors='coerce')
_csv_enddt_failed = csv["end_datetime_UTC"].isna() & _raw_csv_enddt.notna()
# print warning message of any rows that failed parsing
if _csv_enddt_failed.any():
    print(f"\n[WARNING: FAILED PARSE] Failed rows in 'csv[\"end_datetime_UTC\"]' = {_csv_enddt_failed.sum()}")
    for _idx, _val in _raw_csv_enddt[_csv_enddt_failed].items():
        print(f"  Row {_idx}: {_val!r}")

#%% Strip UTC tz and convert end_datetime_UTC col to numeric (seconds since epoch) for interpolation
csv_endtime_numeric = csv["end_datetime_UTC"].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[ns]").astype(np.int64).values / 1e9

#༝ Interpolate latitude and longitude
#%% np.interp = linear interpolation (*timestamps outside .nc files time range will be extrapolated to nearest endpoint value (end-clamped))
csv["end_latitude_DD"] = np.interp(
    csv_endtime_numeric,
    nc_latlon_time_numeric,
    nc_latlon_nodup["latitude"].values
)
csv["end_longitude_DD"] = np.interp(
    csv_endtime_numeric,
    nc_latlon_time_numeric,
    nc_latlon_nodup["longitude"].values
)

# track rows where CSV time falls OUTSIDE .nc time range for QC print out (*will all be END-CLAMPED to same lat/lon value matching lat/lon of first or last row in .nc data)
csv["end_interp_flag"] = "interpolated"
csv.loc[csv_endtime_numeric < nc_latlon_time_min, "end_interp_flag"] = "extrapolated_before"
csv.loc[csv_endtime_numeric > nc_latlon_time_max, "end_interp_flag"] = "extrapolated_after"

# print QC summary of lat/lon interpolation
print("END LAT/LON INTERPOLATION SUMMARY")
print(f"  Total CSV rows:        {len(csv)}")
print(f"  Interpolated:          {(csv['end_interp_flag'] == 'interpolated').sum()}")
print(f"  Extrapolated (before): {(csv['end_interp_flag'] == 'extrapolated_before').sum()}")
print(f"  Extrapolated (after):  {(csv['end_interp_flag'] == 'extrapolated_after').sum()}")
print(f"  Lat NaN count:         {csv['end_latitude_DD'].isna().sum()}")
print(f"  Lon NaN count:         {csv['end_longitude_DD'].isna().sum()}")
print(f"{'=' * 50}")

#✦ INTERPOLATE AV_LATITUDE_DD AND AV_LONGITUDE_DD COLS IN CSV DF FROM 'TIME', 'LATITUDE', AND 'LONGITUDE' VARIABLES IN .NC FILES DATA
#%% Parse av_datetime_UTC col to datetime64 dt (and create QC counters for print message of rows that failed parsing)
_raw_csv_avdt = csv["av_datetime_UTC"].copy()
csv["av_datetime_UTC"] = pd.to_datetime(csv["av_datetime_UTC"], utc=True, errors='coerce')
_csv_avdt_failed = csv["av_datetime_UTC"].isna() & _raw_csv_avdt.notna()
# print warning message of any rows that failed parsing
if _csv_avdt_failed.any():
    print(f"\n[WARNING: FAILED PARSE] Failed rows in 'csv[\"av_datetime_UTC\"]' = {_csv_avdt_failed.sum()}")
    for _idx, _val in _raw_csv_avdt[_csv_avdt_failed].items():
        print(f"  Row {_idx}: {_val!r}")

#%% Strip UTC tz and convert av_datetime_UTC col to numeric (seconds since epoch) for interpolation
csv_avtime_numeric = csv["av_datetime_UTC"].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[ns]").astype(np.int64).values / 1e9

#༝ Interpolate latitude and longitude
#%% np.interp = linear interpolation (*timestamps outside .nc files time range will be extrapolated to nearest endpoint value (end-clamped))
csv["av_latitude_DD"] = np.interp(
    csv_avtime_numeric,
    nc_latlon_time_numeric,
    nc_latlon_nodup["latitude"].values
)
csv["av_longitude_DD"] = np.interp(
    csv_avtime_numeric,
    nc_latlon_time_numeric,
    nc_latlon_nodup["longitude"].values
)

# track rows where CSV time falls OUTSIDE .nc time range for QC print out (*will all be END-CLAMPED to same lat/lon value matching lat/lon of first or last row in .nc data)
csv["av_interp_flag"] = "interpolated"
csv.loc[csv_avtime_numeric < nc_latlon_time_min, "av_interp_flag"] = "extrapolated_before"
csv.loc[csv_avtime_numeric > nc_latlon_time_max, "av_interp_flag"] = "extrapolated_after"

# print QC summary of lat/lon interpolation
print("AV LAT/LON INTERPOLATION SUMMARY")
print(f"  Total CSV rows:        {len(csv)}")
print(f"  Interpolated:          {(csv['av_interp_flag'] == 'interpolated').sum()}")
print(f"  Extrapolated (before): {(csv['av_interp_flag'] == 'extrapolated_before').sum()}")
print(f"  Extrapolated (after):  {(csv['av_interp_flag'] == 'extrapolated_after').sum()}")
print(f"  Lat NaN count:         {csv['av_latitude_DD'].isna().sum()}")
print(f"  Lon NaN count:         {csv['av_longitude_DD'].isna().sum()}")
print(f"{'#' * 80}")

#˚ REMOVE ROWS WITH *EXACT DUPLICATES* IN *ALL FOUR* LAT/LON COLUMNS: START_LATITUDE_DD, START_LONGITUDE_DD, END_LATITUDE_DD, END_LONGITUDE_DD, AV_LATITUDE_DD, AV_LONGITUDE_DD
#˚ keep one row per duplicate group that has closest time to time in .nc files that lat/lon values were interpolated from
#‧ IMPORTANT NOTE ON DUPLICATE COORDINATE ROWS REMOVAL:
#‧ Rows with exact same interpolated lat/lon usually created by extrapolation (end-clamped rows before/after the first/last time covered in .nc files are all assigned same lat/lon values that equal the lat/lon of first/last timestamp)
#‧ If multiple minutes in the acoustic data (aka rows in the imported CSV file) fall BEFORE or AFTER the first/last timestamp in the .nc file, all of these rows in the CSV will be assigned the lat/lon of the first/last timestamp available in the .nc files (since no data on other "side" of these rows to interpolate with).
#‧ For the purposes of GIS mapping and calculations AND the purpose of not skewing the environmental conditions data for the acoustic dataset, only one row with the exact same lat/lon is kept (if there are 20 points all with the same location and therefore the same water temp, salinity, bathymetric depth, etc., it is going to skew the preferred environmental conditions of this dataset towards the conditions at that location EVEN THOUGH all of these acoustic detections/possible detection minutes did NOT actually occur at this one specific location). The duplicate rows removal function selects the row in the duplicate group by finding which row has the closest timestamp to the first/last timestamp available in the .nc files (aka the actual time when the glider was at this lat/lon).
#%% Define columns that must ALL match for a row to be considered a duplicate
_dup_cols = ["start_latitude_DD", "start_longitude_DD", "end_latitude_DD", "end_longitude_DD", "av_latitude_DD", "av_longitude_DD"]

#‧ extrapolated_before groups → reference = earliest .nc timestamp (first glider fix)
#‧ extrapolated_after  groups → reference = latest .nc timestamp (last  glider fix)
#%% Convert numeric .nc boundary times back to UTC datetimes for reference time comparisons
nc_latlon_dt_min = pd.Timestamp(nc_latlon_time_numeric.min(), unit='s', tz='UTC')
nc_latlon_dt_max = pd.Timestamp(nc_latlon_time_numeric.max(), unit='s', tz='UTC')

#‧ coincidental interpolation duplicates (rare) → reference = nearest nc timestamp to each row's av_datetime_UTC; keep row with smallest gap (since those lat/lon values came from BETWEEN two nc timestamps--not one boundary--we find nearest nc timestamp to each row's av_datetime_UTC and keep row with smallest gap)
#%% Sorted array of all unique nc timestamps (seconds since epoch) used as reference for coincidental interpolation duplicates
_all_nc_times_numeric = np.unique(nc_latlon_time_numeric)

#%% Function for each lat/lon duplicate group (*identical values in all four lat/lon cols*) to keep only the ONE row whose av_datetime_UTC is closest to the .nc timestamp that produced the lat/lon values possessed by the duplicate group
# returns the *index label* of the row to keep (not the row itself) so that csv.loc[...] can reconstruct all columns intact (avoids pandas 2.2+ include_groups column-drop issue)
def _keep_closest_to_nc_time(group):
    if len(group) == 1:
        return group.index[0]
    flags = set(group["start_interp_flag"].tolist() + group["end_interp_flag"].tolist() + group["av_interp_flag"].tolist())
    if "extrapolated_before" in flags:
        ref_time = nc_latlon_dt_min
        time_diffs = (group["av_datetime_UTC"] - ref_time).abs()
    elif "extrapolated_after" in flags:
        ref_time = nc_latlon_dt_max
        time_diffs = (group["av_datetime_UTC"] - ref_time).abs()
    else:
        # coincidental interpolation duplicate: for each row find its nearest nc timestamp, then keep row with the smallest gap to that nc timestamp
        row_times_numeric = group["av_datetime_UTC"].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[ns]").astype(np.int64) / 1e9
        nearest_nc_gap = row_times_numeric.apply(
            lambda t: np.abs(_all_nc_times_numeric - t).min()
        )
        return nearest_nc_gap.idxmin()
    return time_diffs.idxmin()

# Call duplicate removal function for csv df that has interpolated lat/lon cols; output results in new df 'csv_dedup'
_n_before_dedup = len(csv)
_keep_idx = (
    csv
    .groupby(_dup_cols, group_keys=False, sort=False)
    .apply(_keep_closest_to_nc_time, include_groups=False)
    .values
)
csv_dedup = csv.loc[_keep_idx].reset_index(drop=True)
_n_removed_dedup = _n_before_dedup - len(csv_dedup)

# print QC summary of duplicate coordinate rows removal
print(f"{'#' * 80}")
print("DUPLICATE INTERPOLATED COORDINATE ROWS REMOVAL SUMMARY")
print(f"  Rows before dedup:     {_n_before_dedup}")
print(f"  Rows removed:          {_n_removed_dedup}")
print(f"  Rows after dedup:      {len(csv_dedup)}")
print(f"{'#' * 80}")


#❥ 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟
#❥ PART TWO: DETERMINE DEPTH OF GLIDER + ENVIRONMENTAL VARIABLES FROM SPECIFIC PROFILE IDs IN RAW .NC FILES       
#❥ must use individual profile data for environmental variables to preserve the actual measured vertical water-column structure the true glider profiles; interpolating these variables across multiple profiles can result in blending data from separate dive/climb profiles
#❥ 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟
#%% Create copy of csv_dedup df to interpolate environmental variables by specific profile ID in
csv_env = csv_dedup.copy()

#❋ PARSE AND CONVERT DATETIME VALUES PROFILE ID MATCHING AND INTERPOLATION BELOW
#%% Build nc env lookup: parse time, drop rows missing time or profile_id, sort by time
nc_env = nc_subset[["time", "profile_id", "glider_nc_file", "depth", "temperature", "salinity", "oxygen_concentration"]].copy()
nc_env["time"] = pd.to_datetime(nc_env["time"], utc=True, errors="coerce")
nc_env = nc_env.dropna(subset=["time", "profile_id"]).sort_values("time").reset_index(drop=True)

#%% Convert nc time + csv_env av_datetime_UTC to numeric seconds since epoch for fast nearest-time search
nc_env_time_num = (
    nc_env["time"].dt.tz_convert("UTC").dt.tz_localize(None)
    .astype("datetime64[ns]").astype(np.int64) / 1e9
).values
# (do not need to parse csv_env av_datetime_UTC (like did for nc_env in build lookup code above) because was already parsed to UTC datetime in part 1)
csv_env_time_num = (
    csv_env["av_datetime_UTC"].dt.tz_convert("UTC").dt.tz_localize(None)
    .astype("datetime64[ns]").astype(np.int64) / 1e9
).values

# print warnings for any invalid/missing datetime values in nc_env (nc_env["time"] can't have NaN here — dropna already removed those rows; instead report how many rows were dropped)
_nc_env_rows_dropped = len(nc_subset) - len(nc_env)
if _nc_env_rows_dropped > 0:
    print(f"{'#' * 80}")
    print(f"[WARNING: INVALID DATETIME] {_nc_env_rows_dropped} row(s) dropped from nc_env due to missing time or profile_id")
else:
    print(f"{'#' * 80}")
    print("[OK] nc_env: no rows dropped due to missing time or profile_id")

# print warnings for any invalid/missing datetime values in csv_env
_csv_env_dt_nan_count = csv_env["av_datetime_UTC"].isna().sum()
if _csv_env_dt_nan_count > 0:
    print(f"[WARNING: INVALID DATETIME] {_csv_env_dt_nan_count} NaN value(s) in 'csv_env[\"av_datetime_UTC\"]'")
    print("  Affected row indices:", csv_env.index[csv_env["av_datetime_UTC"].isna()].tolist())
else:
    print("[OK] csv_env[\"av_datetime_UTC\"]: no NaN values")

_csv_env_time_num_nan_count = np.isnan(csv_env_time_num).sum()
if _csv_env_time_num_nan_count > 0:
    print(f"[WARNING: INVALID DATETIME] {_csv_env_time_num_nan_count} NaN value(s) in 'csv_env_time_num' after numeric conversion")
    print(f"{'#' * 80}")
else:
    print("[OK] csv_env_time_num: no NaN values after numeric conversion")
    print(f"{'#' * 80}")

#✦ .•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•.
#✦ DETERMINE GLIDER PROFILE ID AND SOURCE .NC FILE FOR EACH ROW IN CSV_ENV                                       
#✦ .•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•.
#%% Function to find nearest nc row by time for each csv_env row → assign profile_id and nc_file
def _nearest_sorted_idx(sorted_arr, queries):
    # return index of nearest value in sorted_arr for each query (boundary-clamped)
    idx = np.searchsorted(sorted_arr, queries, side="left")
    idx_hi = np.clip(idx, 0, len(sorted_arr) - 1)
    idx_lo = np.clip(idx - 1, 0, len(sorted_arr) - 1)
    pick_lo = np.abs(sorted_arr[idx_lo] - queries) < np.abs(sorted_arr[idx_hi] - queries)
    return np.where(pick_lo, idx_lo, idx_hi)

# Call function for only on csv_env rows with a valid (non-NaN) timestamp
_valid_csv_time_mask = ~np.isnan(csv_env_time_num)
_nearest_nc_idx = np.full(len(csv_env), -1, dtype=int)
if _valid_csv_time_mask.any():
    _nearest_nc_idx[_valid_csv_time_mask] = _nearest_sorted_idx(
        nc_env_time_num, csv_env_time_num[_valid_csv_time_mask]
    )

# Extract profile_id and glider_nc_file from nearest nc row for each csv_env row
_profile_id_lookup = nc_env["profile_id"].values
_nc_file_lookup    = nc_env["glider_nc_file"].values
csv_env["glider_profile_id"] = [
    _profile_id_lookup[i] if i >= 0 else np.nan for i in _nearest_nc_idx
]
csv_env["glider_nc_file"] = [
    _nc_file_lookup[i] if i >= 0 else None for i in _nearest_nc_idx
]

# print QC summary of profile assignment
print(f"{'#' * 80}")
print("PROFILE ID ASSIGNMENT SUMMARY")
print(f"  Total CSV rows:              {len(csv_env)}")
print(f"  Rows with valid profile_ID:  {csv_env['glider_profile_id'].notna().sum()}")
print(f"  Rows missing profile_ID:     {csv_env['glider_profile_id'].isna().sum()}")
print(f"  Unique profiles assigned:    {csv_env['glider_profile_id'].nunique()}")
print(f"  Source .nc files referenced: {csv_env['glider_nc_file'].nunique()}")
print(f"{'#' * 80}")

#✦ .•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•.
#✦ INTERPOLATE GLIDER DEPTH AND **AT-DEPTH** ENVIRONMENTAL VARIABLES *WITHIN PROFILE* FOR EACH ROW IN CSV DF     
#✦ .•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•.
#%% Initialize output environmental variable columns as NaN
csv_env["glider_depth_m"]               = np.nan
csv_env["water_temperature_C"]          = np.nan
csv_env["salinity_PSU"]                 = np.nan
csv_env["oxygen_concentration_μmol_L"]  = np.nan

# Mapping: output column → source column in nc_env
_env_var_map = {
    "glider_depth_m":               "depth",
    "water_temperature_C":          "temperature",
    "salinity_PSU":                 "salinity",
    "oxygen_concentration_μmol_L":  "oxygen_concentration",
}

# Create empty list for QC tracking
_profile_interp_log = []

#༝ Interpolation uses only .nc data from the MATCHING PROFILE (not across profiles); np.interp = linear (*end-clamped if csv row time falls outside profile's time range); if a variable has no valid data in a profile, those csv_env cells remain NaN
#%% For each unique profile_id group assigned to csv_env rows, interpolate env variables
for pid, grp in csv_env.groupby("glider_profile_id", dropna=True):
    # *subset nc_env to this profile only (match by profile_id only), sorted by time*
    profile_nc = nc_env[
        # keep only rows where nc profile_id matches current pid
        nc_env["profile_id"] == pid
    # sort chronologically and reset integer index
    ].sort_values("time").reset_index(drop=True)

    # pull source .nc filename for this group (for logging); default to "unknown" if column absent
    ncf = grp["glider_nc_file"].iloc[0] if "glider_nc_file" in grp.columns else "unknown"
    # if no matching nc data exists for this profile, log it to QC list and skip to next profile
    if profile_nc.empty:
        _profile_interp_log.append((str(pid), ncf, len(grp), "no_nc_data"))
        continue

    # convert profile nc times to numeric seconds since epoch
    profile_time_num = (
        profile_nc["time"].dt.tz_convert("UTC").dt.tz_localize(None)
        .astype("datetime64[ns]").astype(np.int64) / 1e9
    ).values
    # extract numeric timestamps (seconds since epoch) for csv rows in this profile group
    grp_time_num    = csv_env_time_num[grp.index]
    valid_grp_mask  = ~np.isnan(grp_time_num)
    
    # create empty list to track which variables were successfully interpolated for this profile
    vars_filled = []

    # loop over each output column and its corresponding nc source column
    for out_col, nc_col in _env_var_map.items():
        # extract nc variable values as float array
        var_vals = profile_nc[nc_col].values.astype(float)
        # boolean mask: True where nc variable value is not NaN
        valid_var_mask = ~np.isnan(var_vals)

        # if variable has no valid values in this profile, leave output column as NaN and move on
        if valid_var_mask.sum() == 0:
            continue
        # use only valid (non-NaN) time/value pairs for interpolation
        valid_t = profile_time_num[valid_var_mask]  # nc timestamps at valid variable positions
        valid_v = var_vals[valid_var_mask]          # nc variable values at valid positions
        sort_order = np.argsort(valid_t)            # get indices to sort timestamps ascending
        valid_t = valid_t[sort_order]               # apply sort order to times (np.interp requires sorted x)
        valid_v = valid_v[sort_order]               # apply same sort order to values to keep pairs aligned

        # interpolate nc values onto CSV row timestamps (*only for rows with valid timestamps)
        if valid_grp_mask.any():                              # proceed only if at least one csv row has valid timestamp
            interp_result = np.full(len(grp), np.nan)         # pre-fill result array with NaN (covers invalid-timestamp rows)
            interp_result[valid_grp_mask] = np.interp(        # interpolate only at valid csv timestamps
                grp_time_num[valid_grp_mask],                 # x: target timestamps (csv rows with valid times)
                valid_t,                                      # xp: known nc timestamps (sorted)
                valid_v                                       # fp: known nc variable values
            )
            csv_env.loc[grp.index, out_col] = interp_result   # write interpolated values back into main csv df
            vars_filled.append(out_col)                       # record this variable as successfully filled
    
    # set log status based on whether any variables were interpolated
    status = "ok" if vars_filled else "all_vars_missing"
    _profile_interp_log.append((str(pid), ncf, len(grp), status))

# QC summary calculations and print summary message
_n_no_nc   = sum(1 for _, _, _, s in _profile_interp_log if s == "no_nc_data")
_n_missing = sum(1 for _, _, _, s in _profile_interp_log if s == "all_vars_missing")
print(f"{'#' * 80}")
print("ENVIRONMENTAL VARIABLE INTERPOLATION SUMMARY")
print(f"  Unique profiles processed:       {len(_profile_interp_log)}")
print(f"  Profiles with no nc data:        {_n_no_nc}")
print(f"  Profiles with all vars missing:  {_n_missing}")
print(f"  glider_depth_m       filled:     {csv_env['glider_depth_m'].notna().sum()} / {len(csv_env)}")
print(f"  water_temperature_C  filled:     {csv_env['water_temperature_C'].notna().sum()} / {len(csv_env)}")
print(f"  salinity_PSU         filled:     {csv_env['salinity_PSU'].notna().sum()} / {len(csv_env)}")
print(f"  oxygen_conc_μmol_L   filled:     {csv_env['oxygen_concentration_μmol_L'].notna().sum()} / {len(csv_env)}")
print(f"{'#' * 80}")

#✦ .•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•.
#✦ INTERPOLATE **SEA SURFACE** ENVIRONMENTAL VARIABLES *WITHIN PROFILE* FOR EACH ROW IN CSV DF                   
#✦ .•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•..•°•..•°°•..•°°•..•°°•.
#%% Create copy of csv_env df to interpolate sea surface environmental variables by specific profile ID in
csv_surf = csv_env.copy()

#%% Initialize sea surface output columns as NaN
csv_surf["sea_surface_water_temperature_C"]         = np.nan
csv_surf["sea_surface_salinity_PSU"]                = np.nan
csv_surf["sea_surface_oxygen_concentration_μmol_L"] = np.nan

# Mapping: output column → source column in nc_env (same variables as at-depth; no depth col since depth is already constrained to 1–5 m)
_surf_var_map = {
    "sea_surface_water_temperature_C":         "temperature",
    "sea_surface_salinity_PSU":                "salinity",
    "sea_surface_oxygen_concentration_μmol_L": "oxygen_concentration",
}

# Create empty list for QC tracking
_surf_interp_log = []

#༝ **Sea surface = 1–5 m depth**; interpolation uses only .nc data from the MATCHING PROFILE subset to 1–5 m (not across profiles); np.interp = linear (*end-clamped if csv row time falls outside profile's surface-depth time range); if a variable has no valid 1–5 m data in a profile, those csv_surf cells remain NaN
#%% For each unique profile_id group assigned to csv_surf rows, interpolate surface variables
for pid, grp in csv_surf.groupby("glider_profile_id", dropna=True):
    # subset nc_env to this profile only, then further subset to 1–5 m depth rows (*sea surface definition*)
    profile_nc_surf = nc_env[
        (nc_env["profile_id"] == pid) &
        (nc_env["depth"] >= 1) &
        (nc_env["depth"] <= 5)
    # sort by time
    ].sort_values("time").reset_index(drop=True)

    # pull source .nc filename for this group (for logging)
    ncf = grp["glider_nc_file"].iloc[0] if "glider_nc_file" in grp.columns else "unknown"
    # if no 1–5 m nc data exists for this profile, log and skip
    if profile_nc_surf.empty:
        _surf_interp_log.append((str(pid), ncf, len(grp), "no_surface_nc_data"))
        continue

    # convert surface-subset profile nc times to numeric seconds since epoch
    surf_time_num = (
        profile_nc_surf["time"].dt.tz_convert("UTC").dt.tz_localize(None)
        .astype("datetime64[ns]").astype(np.int64) / 1e9
    ).values
    # extract numeric timestamps for csv rows in this profile group
    grp_time_num   = csv_env_time_num[grp.index]
    valid_grp_mask = ~np.isnan(grp_time_num)

    # create empty list to track which variables were successfully interpolated for this profile
    surf_vars_filled = []

    # loop over each sea surface output column and its corresponding nc source column
    for out_col, nc_col in _surf_var_map.items():
        # extract nc variable values as float array (from 1–5 m subset)
        var_vals = profile_nc_surf[nc_col].values.astype(float)
        # boolean mask: True where nc variable value is not NaN
        valid_var_mask = ~np.isnan(var_vals)

        # if variable has no valid values in 1–5 m subset, leave output column as NaN and move on
        if valid_var_mask.sum() == 0:
            continue
        # use only valid (non-NaN) time/value pairs for interpolation
        valid_t = surf_time_num[valid_var_mask]
        valid_v = var_vals[valid_var_mask]
        sort_order = np.argsort(valid_t)
        valid_t = valid_t[sort_order]
        valid_v = valid_v[sort_order]

        # interpolate nc surface values onto CSV row timestamps (*only for rows with valid timestamps)
        if valid_grp_mask.any():
            interp_result = np.full(len(grp), np.nan)
            interp_result[valid_grp_mask] = np.interp(
                grp_time_num[valid_grp_mask],
                valid_t,
                valid_v
            )
            csv_surf.loc[grp.index, out_col] = interp_result
            surf_vars_filled.append(out_col)

    # set log status based on whether any surface variables were interpolated
    status = "ok" if surf_vars_filled else "all_surf_vars_missing"
    _surf_interp_log.append((str(pid), ncf, len(grp), status))

# QC summary calculations and print summary message
_n_surf_no_nc   = sum(1 for _, _, _, s in _surf_interp_log if s == "no_surface_nc_data")
_n_surf_missing = sum(1 for _, _, _, s in _surf_interp_log if s == "all_surf_vars_missing")
print(f"{'#' * 80}")
print("SEA SURFACE (1–5 m) ENVIRONMENTAL VARIABLE INTERPOLATION SUMMARY")
print(f"  Unique profiles processed:               {len(_surf_interp_log)}")
print(f"  Profiles with no 1–5 m nc data:          {_n_surf_no_nc}")
print(f"  Profiles with all surf vars missing:     {_n_surf_missing}")
print(f"  sea_surface_water_temperature_C  filled: {csv_surf['sea_surface_water_temperature_C'].notna().sum()} / {len(csv_surf)}")
print(f"  sea_surface_salinity_PSU         filled: {csv_surf['sea_surface_salinity_PSU'].notna().sum()} / {len(csv_surf)}")
print(f"  sea_surface_oxygen_conc_μmol_L   filled: {csv_surf['sea_surface_oxygen_concentration_μmol_L'].notna().sum()} / {len(csv_surf)}")
print(f"{'#' * 80}")


#❥ 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟
#❥ TIDY FINAL CSV FOR EXPORT                                                                                      
#❥ 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟 𓆝 𓆟 𓆞 𓆝 𓆟
#%% Copy df to make final edits in
csv_df_FINAL = csv_surf.copy()

# print list of all col names
print(csv_df_FINAL.columns.tolist())

#%% Convert any glider_depth_m values <0 to 0 (error reading when glider near/at surface)
csv_df_FINAL["glider_depth_m"] = pd.to_numeric(csv_df_FINAL["glider_depth_m"], errors="coerce")
n_negative_depth = (csv_df_FINAL["glider_depth_m"] < 0).sum()
csv_df_FINAL.loc[csv_df_FINAL["glider_depth_m"] < 0, "glider_depth_m"] = 0
# print summary count of rows changed
print(f"glider_depth_m values changed from < 0 to 0: {n_negative_depth}")

#%% Parse all datetime cols to datetime64[ns, UTC] data type
for c in [
    "start_datetime_UTC",
    "end_datetime_UTC",
    "av_datetime_UTC"
]:
    if c in csv_df_FINAL.columns:
        csv_df_FINAL[c] = pd.to_datetime(
            csv_df_FINAL[c],
            errors="coerce",
            utc=True,
        ).astype("datetime64[ns, UTC]")

#%% Convert text cols to pandas string dtype
string_cols = ["mission_name", "glider_nc_file", "glider_profile_id", "suborder", "family", "genus", "species", "common_name"]
present_string_cols = [c for c in string_cols if c in csv_df_FINAL.columns]
csv_df_FINAL[present_string_cols] = csv_df_FINAL[present_string_cols].astype("string")

#%% Reorder and drop unecessary columns for output CSV
csv_df_FINAL = csv_df_FINAL[
    [
        "mission_name",
        "glider_nc_file",
        "glider_profile_id",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "suborder",
        "family",
        "genus",
        "species",
        "common_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC",
        "start_latitude_DD",
        "start_longitude_DD",
        "end_latitude_DD",
        "end_longitude_DD",
        "av_latitude_DD",
        "av_longitude_DD",
        "glider_depth_m",
        "water_temperature_C",
        "sea_surface_water_temperature_C",
        "salinity_PSU",
        "sea_surface_salinity_PSU",
        "oxygen_concentration_μmol_L",
        "sea_surface_oxygen_concentration_μmol_L"
    ]
]

#%% Check data type of all cols
for col, dt in csv_df_FINAL.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ glider_nc_file: string
        #~ glider_profile_id: string
        #~ n_channels: int64
        #~ sample_rate_kHz: int64
        #~ bit_depth: int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC]   *
        #~ av_datetime_UTC: datetime64[ns, UTC]    *
        #~ start_latitude_DD: float64
        #~ start_longitude_DD: float64
        #~ end_latitude_DD: float64
        #~ end_longitude_DD: float64
        #~ av_latitude_DD: float64
        #~ av_longitude_DD: float64
        #~ glider_depth_m: float64
        #~ water_temperature_C: float64
        #~ sea_surface_water_temperature_C: float64
        #~ salinity_PSU: float64
        #~ sea_surface_salinity_PSU: float64
        #~ oxygen_concentration_μmol_L: float64
        #~ sea_surface_oxygen_concentration_μmol_L: float64

#%% Sort rows by ascending av_datetime_UTC (earliest → latest)
csv_df_FINAL = csv_df_FINAL.sort_values(
    by="av_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Create copy and replace empty strings / whitespace-only cells with proper missing values (NA)
df_final_fixNA = csv_df_FINAL.copy()
df_final_fixNA = df_final_fixNA.replace(r"^\s*$", pd.NA, regex=True)

#%% Export final dataframe to CSV
#𖠜 UPDATE FILE PATH FOR MISSION
output_path = r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/4_data_interpolated/humpback_INTERPOLATED_UVI2_Around_STX_20250306.csv"
df_final_fixNA.to_csv(output_path, index=False)
# print export confirmation and output CSV df shape
print(f"Exported file to: {output_path}")
print(f"Final output shape: {df_final_fixNA.shape}") # Final output shape: (2812, 27)



################################################################################
# PROFILE_ID UNIQUENESS CHECK
#   Total .nc files:                  580
#   Unique profile_id values:         580
#   Max profile_ids in a single file: 1
################################################################################

################################################################################
# START LAT/LON INTERPOLATION SUMMARY
#   Total CSV rows:        2819
#   Interpolated:          2811
#   Extrapolated (before): 8
#   Extrapolated (after):  0
#   Lat NaN count:         0
#   Lon NaN count:         0
# ==================================================
# END LAT/LON INTERPOLATION SUMMARY
#   Total CSV rows:        2819
#   Interpolated:          2811
#   Extrapolated (before): 8
#   Extrapolated (after):  0
#   Lat NaN count:         0
#   Lon NaN count:         0
# ==================================================
# AV LAT/LON INTERPOLATION SUMMARY
#   Total CSV rows:        2819
#   Interpolated:          2811
#   Extrapolated (before): 8
#   Extrapolated (after):  0
#   Lat NaN count:         0
#   Lon NaN count:         0
################################################################################

################################################################################
# DUPLICATE COORDINATE ROWS REMOVAL SUMMARY
#   Rows before dedup:     2819
#   Rows removed:          7
#   Rows after dedup:      2812
################################################################################

################################################################################
# [OK] nc_env: no rows dropped due to missing time or profile_id
# [OK] csv_env["av_datetime_UTC"]: no NaN values
# [OK] csv_env_time_num: no NaN values after numeric conversion
################################################################################

################################################################################
# PROFILE ID ASSIGNMENT SUMMARY
#   Total CSV rows:              2812
#   Rows with valid profile_ID:  2812
#   Rows missing profile_ID:     0
#   Unique profiles assigned:    297
#   Source .nc files referenced: 297
################################################################################

################################################################################
# ENVIRONMENTAL VARIABLE INTERPOLATION SUMMARY
#   Unique profiles processed:       297
#   Profiles with no nc data:        0
#   Profiles with all vars missing:  0
#   glider_depth_m       filled:     2812 / 2812
#   water_temperature_C  filled:     2706 / 2812
#   salinity_PSU         filled:     2706 / 2812
#   oxygen_conc_μmol_L   filled:     2706 / 2812
################################################################################

################################################################################
# SEA SURFACE (1–5 m) ENVIRONMENTAL VARIABLE INTERPOLATION SUMMARY
#   Unique profiles processed:               297
#   Profiles with no 1–5 m nc data:          2
#   Profiles with all surf vars missing:     10
#   sea_surface_water_temperature_C  filled: 2699 / 2812
#   sea_surface_salinity_PSU         filled: 2699 / 2812
#   sea_surface_oxygen_conc_μmol_L   filled: 2699 / 2812
################################################################################

################################################################################
# glider_depth_m values changed from < 0 to 0: 1
################################################################################