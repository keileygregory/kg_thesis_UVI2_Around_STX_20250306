'''
This script tidies and fixes errors (duplicates/invalid or missing values) in all low-frequency acoustic analysis data for the mission, separates the combined data by species (or surfacings), and outputs final .csv files for each species' acoustic analysis results.

Input combined .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/missionname/data/data_processed/acoustic_processed/LF_processed
Output species/surfacings .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/missionname/data/3_data_analyzed/acoustic_analyzed/LF_analyzed

𖠺 Created by Keiley Gregory on January 21, 2026
Last updated on March 2, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION

#%%
from pathlib import Path
import pandas as pd
import numpy as np
import re

#%% Import CSV of combined low-frequency selection table data
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_COMBINED.csv")
raw_data = pd.read_csv(csv_path)

#· TIDY DATAFRAME + EXTRACT START DATETIME FROM FILENAME + INSPECT SPECIES ID CODE DATA (IN PREPARATION TO SPLIT DF BY SPECIES)                                    
#%% Remove unnecessary columns output by Raven Pro and save as new dataframe
data = raw_data[
    [
        "Channel",
        "Begin File",
        "species",
        "call_type",
        "source_selection_table"
    ]
].copy()

#%% Rename columns
data = data.rename(columns={"Channel": "n_channels", "Begin File": "wav_file"})

#%% Add new manually set cols + cols for subsequent calculations and fill with pandas NA placeholder
new_cols = [
    "sample_rate_kHz",
    "bit_depth",
    "spectrogram_range_kHz",
    "start_datetime_UTC",
    "end_datetime_UTC",
    "av_datetime_UTC"
]
data[new_cols] = pd.NA

#%% Manually enter values in cols 'sample_rate_kHz', 'bit_depth', 'spectrogram_range_kHz', and 'mission_name' (same value for all rows in each col)
data["sample_rate_kHz"] = 2
data["bit_depth"] = 16
data["spectrogram_range_kHz"] = 1
#𖠜 CHANGE MISSION NAME FOR CURRENT MISSION
data["mission_name"] = "UVI2_Around_STX_20250306"

#%% Force any cells with "missing-like" tokens (NA/NaN/null/blank) to real missing values (pd.NA)
missing_tokens = {"na", "n/a", "nan", "none", "null", "<na>", "missing"}

def normalize_missing_series(s: pd.Series) -> pd.Series:
    # only operate on object/string-like columns safely
    if s.dtype == "object" or pd.api.types.is_string_dtype(s):
        # preserve missing values as <NA>
        s2 = s.astype("string")
        # remove leading/trailing whitespace
        s2 = s2.str.strip()
        # set cells with whitespace-only to <NA>
        s2 = s2.replace(r"^\s*$", pd.NA, regex=True)
        # token-based missing to <NA> (case-insensitive)
        s2 = s2.mask(s2.str.lower().isin(missing_tokens), pd.NA)
        return s2
    return s

for col in data.columns:
    data[col] = normalize_missing_series(data[col])

#%% Clean string columns (ensure string format, strip whitespace)
string_cols = ["wav_file", "species", "source_selection_table", "mission_name"]
for c in string_cols:
    data[c] = data[c].astype("string").str.strip()

#%% Convert all strings in 'species' col to lowercase (in case accidentally typed "H" instead of "h" (or etc) during acoustic analysis in Raven Pro)
data["species"] = data["species"].str.lower()

#%% Clean numeric columns (nullable integers, keep missing as <NA>)
int_cols = ["n_channels", "call_type", "sample_rate_kHz", "bit_depth", "spectrogram_range_kHz"]
for c in int_cols:
    # convert to numeric data type (if non-numeric (aka invalid) set as NaN)
    num = pd.to_numeric(data[c], errors="coerce")
    # convert NaN to <NA> while keeping integer dtype ('Int64' is pandas "nullable integer" data type = allows missing values)
    data[c] = num.round(0).astype("Int64")

#%% Reorder columns
data = data[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "spectrogram_range_kHz",
        "wav_file",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC",
        "species",
        "call_type",
        "source_selection_table"
    ]
]

#˖ EXTRACT START DATETIME OF AUDIO CLIP FROM .WAV FILENAME (IN 'WAV_FILE' COL) + CALCULATE END AND MIDPOINT DATETIME COLS
#%% Regex to extract start datetime from 'wav_file' col (naming convention: {glider}_{mission}_###_LF_{YYYYMMDD}_{hhmmss}.wav)
dt_regex = re.compile(r"_(\d{8})_(\d{6})\.wav$", re.IGNORECASE)

#%% Function to extract start datetime from each .wav filename (if no .wav filename matching regex pattern is found, return NaN)
def parse_start_datetime_utc(wav_name: str) -> pd.Timestamp:
    if pd.isna(wav_name):
        return pd.NaT
    m = dt_regex.search(str(wav_name))
    if not m:
        return pd.NaT
    yyyymmdd, hhmmss = m.group(1), m.group(2)
    # format extracted values as pandas datetime object
    ts = pd.to_datetime(f"{yyyymmdd}{hhmmss}", format="%Y%m%d%H%M%S", utc=True, errors="coerce")
    return ts

# Call function for data df
data["start_datetime_UTC"] = data["wav_file"].apply(parse_start_datetime_utc)

#%% Calculate end and midpoint datetimes from extracted start datetime (.to_timedelta = change in time (Δt) from value in 'start_datetime_UTC')
data["end_datetime_UTC"] = data["start_datetime_UTC"] + pd.to_timedelta(60, unit="s")
data["av_datetime_UTC"]  = data["start_datetime_UTC"] + pd.to_timedelta(30, unit="s")

#%% Check data type of all cols
for col, dt in data.dtypes.items():
    print(f"{col}: {dt}")

        #⋄ PRINT OUT SHOULD MATCH THIS:
        # mission_name: string
        # n_channels: Int64
        # sample_rate_kHz: Int64
        # bit_depth: Int64
        # spectrogram_range_kHz: Int64
        # wav_file: string
        # start_datetime_UTC: datetime64[ns, UTC] *
        # end_datetime_UTC: datetime64[ns, UTC] *
        # av_datetime_UTC: datetime64[ns, UTC] *
        # species: string
        # call_type: Int64
        # source_selection_table: string

#˖ DEFINE MATCH VALUE FUNCTION FOR MANUAL CORRECTIONS
#%% Function for manual corrections: if the value is missing (pd.NA/np.nan/None), match rows where the series is missing; otherwise match rows where the series equals the value
def match_value(series: pd.Series, value) -> pd.Series:
    return series.isna() if pd.isna(value) else (series == value)

#%% Create copy of data df to make manual species ID fixes in if applicable (if no fixes necessary, then data_speciesfix df used in all subsequent code is just exact copy of data df)
data_speciesfix = data.copy()

#‧ [WARNING] message for rows with INVALID or MISSING SPECIES code ('species' ≠ "h", "m", or "s")
#%% Create dictionary of valid species codes
valid_species = {"h", "m", "s"}

# Create boolean mask (True = 'species' col value missing OR not in {"h","m","s"})
bad_species_mask = data_speciesfix["species"].isna() | (~data_speciesfix["species"].isin(valid_species))

# Create subset of 'data_speciesfix' df for rows that fail species validity check
bad_species_rows = data_speciesfix.loc[
    # only keep rows with missing or invalid species code (bad_species_mask = True)
    bad_species_mask,
    # include data from selected cols in printed warning message
    ["wav_file", "species", "call_type", "source_selection_table"]
].copy()

# Print warning for any rows in df where 'species' col value is missing or invalid (if NO rows with missing/invalid species code found, print success message)
if bad_species_rows.empty:
    print("\n✅ All rows have a valid species code (h, m, or s)")
# if any rows have missing/invalid species code found, print count all 'bad' rows and data from selected cols (+ original row index number) for each row
else:
    print(f"\n⚠️ [WARNING] Rows with missing/invalid species codes: {len(bad_species_rows)}\n")
    print(bad_species_rows.to_string(index=True))

#⋆ ------------------------------------------------------------------------------------------------------------------------------------------------------------
#⋆ INVALID/MISSING *SPECIES* CORRECTIONS - MUST RE-REVIEW SPECTROGRAMS AND MANUALLY ENTER CORRECTED SPECIES FOR EACH ROW
#%% Dictionary of manual fixes (*included "species" in row matching conditions so that if there are 2 rows from same spectrogram with same call type BUT different species (ex: 1 row for minke and 1 row missing species), ONLY row missing species will be corrected and row for minke will not be changed)
# ("wav_file", "species", call_type, "source_selection_table"): fixed "species"
#𖠜 CHANGE FIXES TO APPLY TO WARNING MESSAGE PRINT-OUT FOR CURRENT MISSION
species_fixes = {
    ("UVI2_Around_STX_005_LF_20250308_060943.wav", "w", pd.NA, "LF_UVI2_AroundSTX_start0308T020943_stop0308T113443.csv"): "s",
    ("UVI2_Around_STX_008_LF_20250309_065043.wav", pd.NA, pd.NA, "LF_UVI2_AroundSTX_start0309T065043_stop0309T172743.csv"): "h",
    ("UVI2_Around_STX_019_LF_20250312_165443.wav", ",", pd.NA, "LF_UVI2_AroundSTX_start0310T180943_stop0312T225143.csv"): "m",
    ("UVI2_Around_STX_022_LF_20250313_203643.wav", "s'", pd.NA, "LF_UVI2_AroundSTX_start0312T225243_stop0314T000043.txt"): "s",
    ("UVI2_Around_STX_028_LF_20250315_211943.wav", pd.NA, pd.NA, "LF_UVI2_AroundSTX_start0315T002143_stop0317T053043.txt"): "s",
    ("UVI2_Around_STX_035_LF_20250318_063843.wav", "4", pd.NA, "LF_UVI2_AroundSTX_start0317T053143_stop0318T174743.txt"): "h"
}

#%% Loop through each line in 'species_fixes' dictionary and apply species fixes to 'data_speciesfix' df
for (wav, spc, ct, src), new_species in species_fixes.items():
    # build match mask for species column (*if spc is missing (pd.NA/np.nan/None) then match rows where species is missing; otherwise, match rows where species equals spc exactly)
    spc_match = match_value(data_speciesfix["species"], spc)
    # build match mask for call_type column (same missing value handling as spc line above)
    ct_match  = match_value(data_speciesfix["call_type"], ct)
    # combine all conditions into single boolean Series mask (*row is selected ONLY if it matches: 1) the wav filename, 2) the species condition (including "missing species" cases), 3) the call_type condition (including "missing" cases), AND 4) the source_selection_table filename)
    mask = (
        (data_speciesfix["wav_file"] == wav)                    # match exact wav_file string
        & spc_match                                             # match species (or species is missing)
        & ct_match                                              # match call_type (or it is missing)
        & (data_speciesfix["source_selection_table"] == src)    # match exact source table string
    ).fillna(False)                                             # if any part produced pd.NA in the mask, treat it as False (NOT a match)
    # count how many rows in df match conditions for current line in 'species_fixes' dictionary (True counts as 1, False as 0)
    n = int(mask.sum())
    # if no rows in df match conditions for current line in 'species_fixes' dictionary (no fixes can be made), print warning message (no edits possible)
    if n == 0:
        print(
            "⚠️ SPECIES FIX NOT APPLIED (row not found): "
            f"wav_file = {wav}, species = {spc}, call_type = {ct}, source_selection_table = {src}"
        )
        continue
    # if matching row is successfully found, print success summary message and APPLY edits (*it is ok if fix applies to more than one row since duplicates have NOT been removed yet)
    else:
        print(
            "✅ SPECIES FIX SUCCESSFULLY APPLIED: "
            f"wav_file = {wav}, species = {spc}, call_type = {ct}, source_selection_table = {src} "
            f"→ new_species={new_species}"
        )
    data_speciesfix.loc[mask, "species"] = new_species
#⋆ ------------------------------------------------------------------------------------------------------------------------------------------------------------



#· ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
#· HUMPBACK WHALES (MEGAPTERA NOVAEANGLIAE) ----------------------------------------------------------------------------------------------------------------------
#· ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
#%% Create new df filtered to only rows with species humpback (species == "h")
humpback = data_speciesfix.loc[data_speciesfix["species"] == "h"].copy()

# optional: reset row number index (so it’s clean/continuous)
humpback = humpback.reset_index(drop=True)

#%% Create new 'clean' df and remove cols 'wav_file', 'species' (with "h" abbreviation), and 'source_selection_table'
humpback_clean = humpback.drop(columns=["wav_file", "species", "source_selection_table"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
humpback_clean["family"] = "Balaenopteridae"
humpback_clean["genus"] = "Megaptera"
humpback_clean["species"] = "novaeangliae"
humpback_clean["common_name"] = "humpback whale"

#%% Reorder columns
humpback_clean = humpback_clean[
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
        "call_type"
    ]
]

#%% Create copy of humpback_clean df to make manual duplicate row fixes in if applicable (if no fixes necessary, then humpback_nodup df used in all subsequent code is just exact copy of humpback_clean df)
humpback_nodup = humpback_clean.copy()

#%% IF duplicate rows have exact same values in ALL THREE COLUMNS (start_datetime_UTC, call_type) then only keep 1 row of each duplicate group
hb_true_dup_mask = humpback_nodup.duplicated(
    subset=["start_datetime_UTC", "call_type"],
    keep="first"
)
hb_n_true_dups = int(hb_true_dup_mask.sum())

# Drop extra copies of duplicate rows
humpback_nodup = humpback_nodup.loc[~hb_true_dup_mask].copy()
print(
    f"✅ Removed {hb_n_true_dups} exact duplicate row(s) (same start_datetime_UTC + call_type)"
    f"\nRows: {len(humpback_clean)} → {len(humpback_nodup)}"
)

#‧ [WARNING] message for DUPLICATE rows in humpback_nodup (SAME start_datetime_UTC but DIFFERENT call_type)
#%% Create boolean mask (True for ANY row whose start_datetime_UTC value appears more than once)
hb_dup_mask = humpback_nodup["start_datetime_UTC"].duplicated(keep=False)

# Use boolean mask to create df of ONLY duplicate rows (.copy() so edits to hb_dup_rows do NOT affect humpback_nodup)
hb_dup_rows = humpback_nodup.loc[hb_dup_mask].copy()

# Print warning message of duplicate rows if present
if hb_dup_rows.empty:
    print("\n✅ No duplicate rows found!")
else:
    # sort so duplicates print together in time order (stable sort keeps original order within ties)
    h_dup_rows = hb_dup_rows.sort_values(["start_datetime_UTC"], kind="mergesort")
    # print count per duplicated timestamp
    h_dup_counts = (
        h_dup_rows["start_datetime_UTC"]
        .value_counts()
        .sort_index()
    )
    print(f"\n⚠️ [WARNING] Duplicate rows found: {len(h_dup_rows)} rows share duplicated start_datetime_UTC values.\n")
    print("Duplicate start_datetime_UTC counts:")
    print(h_dup_counts.to_string())
    # only print these 3 columns for duplicate rows list
    cols_to_print = ["start_datetime_UTC", "call_type"]
    print("\nDuplicate rows (all rows with duplicated start_datetime_UTC):")
    print(h_dup_rows.loc[:, cols_to_print].to_string(index=True))

#⋆ ------------------------------------------------------------------------------------------------------------------------------------------------------------
#⋆ HUMPBACK DUPLICATE ROW CORRECTIONS - MANUALLY SELECT WHICH ROWS TO DROP
#%% Dictionary of rows to ****REMOVE*****
# (pd.Timestamp("YYYY-MM-DD hh:mm:ss+00:00"), call_type) *DO NOT FORGET TO INCLUDE +00:00 in "YYYY-MM-DD hh:mm:ss+00:00"
#𖠜 CHANGE FIXES TO APPLY TO WARNING MESSAGE PRINT-OUT FOR CURRENT MISSION
#ㅱ these rows will be !!!REMOVED!!!
hb_drop_dup_rows = {
    (pd.Timestamp("2025-03-08 00:41:43+00:00"), 12), # keep 380 	2025-03-08 00:41:43+00:00      5
    (pd.Timestamp("2025-03-08 01:17:43+00:00"), 2),  # keep 388 	2025-03-08 01:17:43+00:00      12
    (pd.Timestamp("2025-03-08 01:27:43+00:00"), 5),  # keep 391 	2025-03-08 01:27:43+00:00      2
    (pd.Timestamp("2025-03-09 03:14:43+00:00"), 4),  # keep 586 	2025-03-09 03:14:43+00:00      5
    (pd.Timestamp("2025-03-09 03:15:43+00:00"), 5),  # keep 576 	2025-03-09 03:15:43+00:00      4
    (pd.Timestamp("2025-03-09 03:47:43+00:00"), 1),  # keep 591 	2025-03-09 03:47:43+00:00      5
    (pd.Timestamp("2025-03-09 03:50:43+00:00"), 5),  # keep 581 	2025-03-09 03:50:43+00:00      14
    (pd.Timestamp("2025-03-09 07:20:43+00:00"), 1),  # keep 620 	2025-03-09 07:20:43+00:00      5
    (pd.Timestamp("2025-03-09 17:23:43+00:00"), 12)  # keep 684 	2025-03-09 17:23:43+00:00      14
}

#%% Loop through each line in 'hb_drop_dup_rows' dictionary and drop matching row(s) from 'humpback_nodup' df (hbd = humpback Duplicates; sdt = start_datetime_UTC, ct = call_type)
for hbd_sdt, hbd_ct in hb_drop_dup_rows:
    # normalized_sdt to tz-aware UTC (so it matches datetime64[ns, UTC] in the df)
    hbd_sdt = pd.Timestamp(hbd_sdt)
    if hbd_sdt.tz is None:
        hbd_sdt = hbd_sdt.tz_localize("UTC")
    else:
        hbd_sdt = hbd_sdt.tz_convert("UTC")
    # build match mask for call_type column (*if hbd_ct is missing (pd.NA/np.nan/None) then match rows where call_type is missing; otherwise, match rows where call_type equals hbd_ct exactly)
    hbd_ct_match = match_value(humpback_nodup["call_type"], hbd_ct)
    # combine all conditions into single boolean Series mask (*row is selected ONLY if it matches: 1) the start_datetime_UTC AND 2) the call_type condition (including "missing" cases))
    mask = (
        (humpback_nodup["start_datetime_UTC"] == hbd_sdt)   # match exact start_datetime_UTC value
        & hbd_ct_match                                      # match call_type (or it is missing)
    ).fillna(False)                                         # if any part produced pd.NA in the mask, treat it as False (NOT a match)
    # count how many rows match this drop key
    n = int(mask.sum())
    # if no rows match, print warning message (no edits possible)
    if n == 0:
        print(
            "⚠️ DROP ROW NOT FOUND (not removed): "
            f"start_datetime_UTC = {hbd_sdt}, call_type = {hbd_ct}"
        )
        continue
    # if more than one row matches, print warning message (BUT STILL APPLY edits)
    if n > 1:
        print(
            f"⚠️ SINGLE DROP KEY MATCHED MULTIPLE ROWS (n = {n}) — **ALL WILL BE REMOVED!**: "
            f"start_datetime_UTC = {hbd_sdt}, call_type = {hbd_ct}"
        )
    # drop matching row(s)
    humpback_nodup = humpback_nodup.loc[~mask].copy()
    # print summary message
    print(
        f"✅ ROW(S) REMOVED (n = {n}): "
        f"start_datetime_UTC = {hbd_sdt}, call_type = {hbd_ct}"
    )
#⋆ ------------------------------------------------------------------------------------------------------------------------------------------------------------

#%% Create copy of humpback_nodup df to make manual call type fixes in if applicable (if no fixes necessary, then humpback_calltypefix df used in all subsequent code is just exact copy of humpback_nodup df)
humpback_calltypefix = humpback_nodup.copy()

#‧ [WARNING] message for rows with INVALID or MISSING CALL TYPE code ('call_type' ≠ 1, 2, 3, 4, 5, 12, 13, 14, 23, 24, or 34)
#%% Function to extract and print list of rows where call_type ≠ 1, 2, 3, 4, 5, 12, 13, 14, 23, 24, or 34 ("-> None" means function only prints, does not return df)
def print_call_type_notvalid(df: pd.DataFrame) -> None:
    # select 'call_type' column
    cd = df["call_type"]
    # value invalid if NaN or ≠ 1/2/3/4/5/12/13/14/23/24/34
    invalid_mask = cd.isna() | (~cd.isin([1, 2, 3, 4, 5, 12, 13, 14, 23, 24, 34]))
    # create new df 'hits' that contains ONLY rows where call_type ≠ 1/2/3/4/5/12/13/14/23/24/34 (".loc[...]" filters rows by boolean condition (True/False) for each row)
    hits = df.loc[invalid_mask].copy()
    # if all rows have VALID call_type value, print message and exit
    if hits.empty:
        print("\nALL rows call_type valid (= 1, 2, 3, 4, 5, 12, 13, 14, 23, 24, or 34)")
        return
    # print count of rows that matched INVALID condition call_type ≠ 1/2/3/4/5/12/13/14/23/24/34
    print(f"\n⚠️ Rows with INVALID/MISSING call_type (≠ 1, 2, 3, 4, 5, 12, 13, 14, 23, 24, or 34): {len(hits)}")
    # define cols (in order) to include in print message
    cols_to_show = ["start_datetime_UTC", "call_type"]
    # print data from selected cols + df row index number for all rows with invalid/missing 'call_type' value
    print(hits[cols_to_show].to_string(index=True))

# Call function for 'humpback_calltypefix' df
print_call_type_notvalid(humpback_calltypefix)

#⋆ ------------------------------------------------------------------------------------------------------------------------------------------------------------
#⋆ HUMPBACK INVALID/MISSING *CALL TYPE* CORRECTIONS - RE-REVIEW SPECTROGRAMS AND MANUALLY ENTER CORRECTED CALL TYPE FOR EACH ROW
#%% Dictionary of manual fixes 
# (pd.Timestamp("YYYY-MM-DD hh:mm:ss+00:00"), call_type): fixed call_type (*DO NOT FORGET TO INCLUDE +00:00 in "YYYY-MM-DD hh:mm:ss+00:00")
#𖠜 CHANGE FIXES TO APPLY TO WARNING MESSAGE PRINT-OUT FOR CURRENT MISSION
hb_call_type_fixes = {
    (pd.Timestamp("2025-03-06 21:09:43+00:00"), pd.NA): 5,
    (pd.Timestamp("2025-03-06 22:39:43+00:00"), pd.NA): 1,
    (pd.Timestamp("2025-03-07 00:36:43+00:00"), pd.NA): 5,
    (pd.Timestamp("2025-03-07 05:29:43+00:00"), pd.NA): 5,
    (pd.Timestamp("2025-03-07 20:03:43+00:00"), pd.NA): 5,
    (pd.Timestamp("2025-03-07 21:35:43+00:00"), pd.NA): 12,
    (pd.Timestamp("2025-03-07 21:50:43+00:00"), pd.NA): 12,
    (pd.Timestamp("2025-03-07 21:51:43+00:00"), pd.NA): 12,
    (pd.Timestamp("2025-03-09 06:50:43+00:00"), pd.NA): 1,
    (pd.Timestamp("2025-03-09 08:43:43+00:00"), pd.NA): 1,
    (pd.Timestamp("2025-03-18 06:38:43+00:00"), pd.NA): 4
}

#%% Loop through each line in 'hb_call_type_fixes' dictionary and apply call type fixes to 'humpback_calltypefix' df (hbc = humpback Call type; sdt = start_datetime_UTC, ct = call_type)
for (hbc_sdt, hbc_ct), new_calltype in hb_call_type_fixes.items():
    # normalize hbc_sdt to tz-aware UTC (so it matches datetime64[ns, UTC] in df)
    hbc_sdt = pd.Timestamp(hbc_sdt)
    if hbc_sdt.tz is None:
        hbc_sdt = hbc_sdt.tz_localize("UTC")
    else:
        hbc_sdt = hbc_sdt.tz_convert("UTC")
    # build match mask for call_type column (*if hbc_ct is missing (pd.NA/np.nan/None) then match rows where call_type is missing; otherwise, match rows where call_type equals hbc_ct exactly)
    hbc_ct_match  = match_value(humpback_calltypefix["call_type"], hbc_ct)
    # combine all conditions into single boolean Series mask (*row is selected ONLY if it matches: 1) the start_datetime_UTC AND 2) the call_type condition (including "missing" cases))
    mask = (
        (humpback_calltypefix["start_datetime_UTC"] == hbc_sdt)  # match exact start_datetime_UTC value
        & hbc_ct_match                                           # match call_type (or it is missing)
    ).fillna(False)                                              # if any part produced pd.NA in the mask, treat it as False (NOT a match)
    # count how many rows in df match conditions for current line in 'hb_call_type_fixes' dictionary (True counts as 1, False as 0)
    n = int(mask.sum())
    # if no rows in df match conditions for current line in 'hb_call_type_fixes' dictionary (no fixes can be made), print warning message (no edits possible)
    if n == 0:
        print(
            "⚠️ CALL TYPE FIX NOT APPLIED (row not found): "
            f"start_datetime_UTC = {hbc_sdt}, call_type = {hbc_ct}"
        )
        continue
    # if a single fix key matches 2+ rows, print warning message and do NOT apply edits
    if n > 1:
        print(
            f"⚠️ SINGLE CALL TYPE FIX APPLIED TO MULTIPLE ROWS (n = {n}): "
            f"start_datetime_UTC = {hbc_sdt}, call_type = {hbc_ct}"
        )
    # if matching row is successfully found, print success summary message and APPLY edits
    if n == 1:
        print(
            "✅ CALL TYPE FIX SUCCESSFULLY APPLIED (1 fix per 1 row): "
            f"start_datetime_UTC = {hbc_sdt}, call_type = {hbc_ct} "
            f"→ new_calltype = {new_calltype}"
        )
    humpback_calltypefix.loc[mask, "call_type"] = new_calltype
#⋆ ------------------------------------------------------------------------------------------------------------------------------------------------------------

#%% Create copy of humpback_calltypefix df to use for final output CSV
humpback_final = humpback_calltypefix.copy()

#%% Create map of call type key (numeric call_type codes -> descriptive strings)
call_type_map = {
    1:  "upsweep",
    2:  "downsweep",
    3:  "'U' shape",
    4:  "inverted 'U' shape",
    5:  "song",
    12: "upsweep, downsweep",
    13: "upsweep, 'U' shape",
    14: "upsweep, inverted 'U' shape",
    23: "downsweep, 'U' shape",
    24: "downsweep, inverted 'U' shape",
    34: "'U' shape, inverted 'U' shape"
}

#%% Add NEW column with call type descriptions, while keeping original numeric 'call_type' column unchanged
humpback_final["call_type_description"] = (
    humpback_final["call_type"]
    .map(call_type_map)
    .astype("string")
)

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
humpback_final = humpback_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Export final humpback df as CSV (output to 'LF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
hb_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/humpback_analyzed_UVI2_Around_STX_20250306.csv")
humpback_final.to_csv(hb_output_csv_path, index=False)
print(f"Saved humpback CSV to: {hb_output_csv_path}")



#· ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
#· MINKE WHALES (BALAENOPTERA ACUTOROSTRATA) ---------------------------------------------------------------------------------------------------------------------
#· ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
#%% Create new df filtered to only rows with species minke (species == "m")
minke = data_speciesfix.loc[data_speciesfix["species"] == "m"].copy()

# optional: reset row number index (so it’s clean/continuous)
minke = minke.reset_index(drop=True)

#%% Create new 'clean' df and remove cols 'wav_file', 'species' (with "m" abbreviation), 'call_type' (not applicable for minkes), and 'source_selection_table'
minke_clean = minke.drop(columns=["wav_file", "species", "call_type", "source_selection_table"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
minke_clean["family"] = "Balaenopteridae"
minke_clean["genus"] = "Balaenoptera"
minke_clean["species"] = "acutorostrata"
minke_clean["common_name"] = "minke whale"

#%% Reorder columns
minke_clean = minke_clean[
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
        "av_datetime_UTC"
    ]
]

#%% Create copy of minke_clean df to make manual duplicate row fixes in if applicable (if no fixes necessary, then minke_nodup df used in all subsequent code is just exact copy of minke_clean df)
minke_nodup = minke_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC column, then only keep 1 row of each duplicate group
mk_true_dup_mask = minke_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
mk_n_true_dups = int(mk_true_dup_mask.sum())

# Drop extra copies of duplicate rows
minke_nodup = minke_nodup.loc[~mk_true_dup_mask].copy()
print(
    f"✅ Removed {mk_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(minke_clean)} → {len(minke_nodup)}"
)

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
minke_nodup = minke_nodup.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Export final minke df as CSV (output to 'LF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
mk_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/minke_analyzed_UVI2_Around_STX_20250306.csv")
minke_nodup.to_csv(mk_output_csv_path, index=False)
print(f"Saved minke CSV to: {mk_output_csv_path}")



#· ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
#· SURFACING EVENTS ----------------------------------------------------------------------------------------------------------------------------------------------
#· ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌
#%% Create new df filtered to only rows with surfacing mins (species == "s")
surfacings = data_speciesfix.loc[data_speciesfix["species"] == "s"].copy()

# optional: reset row number index (so it’s clean/continuous)
surfacings = surfacings.reset_index(drop=True)

#%% Create new 'surfacings_clean' df and remove unnecessary cols
surfacings_clean = surfacings.drop(columns=["n_channels", "sample_rate_kHz", "bit_depth", "spectrogram_range_kHz", "wav_file", "species", "call_type", "source_selection_table"], errors="ignore").copy()

#%% Create copy of sufacings_clean df to make manual duplicate row fixes in if applicable (if no fixes necessary, then surfacings_nodup df used in all subsequent code is just exact copy of surfacings_clean df)
surfacings_nodup = surfacings_clean.copy()

#%% IF duplicate rows for same exact minute period then only keep 1 row of each duplicate group
sf_true_dup_mask = surfacings_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
sf_n_true_dups = int(sf_true_dup_mask.sum())

# Drop extra copies of duplicate rows
surfacings_nodup = surfacings_nodup.loc[~sf_true_dup_mask].copy()
print(
    f"✅ Removed {sf_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(surfacings_clean)} → {len(surfacings_nodup)}"
)

#%% Reorder columns
surfacings_nodup = surfacings_nodup[
    [
        "mission_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
surfacings_nodup = surfacings_nodup.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Export final surfacings df as CSV (output to 'LF_analyzed' folder in mission repo); this CSV will be used to remove mins where detections are NOT possible
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
surf_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/surfacing_mins_UVI2_Around_STX_20250306.csv")
surfacings_nodup.to_csv(surf_output_csv_path, index=False)
print(f"Saved surfacings CSV to: {surf_output_csv_path}")
