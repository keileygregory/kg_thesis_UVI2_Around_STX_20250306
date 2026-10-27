'''
This script uses the raw HF click event data contained in the 'Click_Detector_OfflineEvents' table downloaded from the Pamguard_UVI2_Around_STX_20250306.sqlite3 database via SQLite Studio app to create two CSV file outputs: 1 that is a tidied version of the input raw data while still maintaining the overall structure and informational content of the original PAMGuard SQLite database export, and 1 that has been refined to prioritize the data and variable naming systems that will be used in the downstream analyses of my thesis (splitting CSVs by species, mapping, etc.).

Input .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/2_data_processed/acoustic_processed/HF_processed (input file: rawexport_pamguard_sqlite_click_detector_offlineevents_*missionname*.csv)
Output .csv files directory: Same as input (output file: tidy_pamguard_sqlite_clickevents_*missionname*.csv, all_HF_clickevents_*missionname*.csv)

𖠺 Created by Keiley Gregory on July 8, 2026
Last updated on July 15, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd
import numpy as np
import re

#%% Load raw exported data from 'Click_Detector_OfflineEvents' table (downloaded from Pamguard_UVI2_Around_STX_20250306.sqlite3 database via SQLite Studio app)
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
raw_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/HF_processed/rawexport_pamguard_sqlite_click_detector_offlineevents_UVI2_Around_STX_20250306.csv")
raw_data = pd.read_csv(raw_path)

#%% Create working copy of raw_data df (leave original df unedited)
data = raw_data.copy()


#❥ ############################################################################################################
#❥ PART 1 - TIDY AND EXPORT RAW CLICK EVENTS DATA FROM PAMGUARD SQLITE DATABASE                                
#❥ ############################################################################################################

#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ CHECK DATA FOR ERRORS/ODDITIES - RE-REVIEW ANY CLICK EVENTS WITH FLAGGED ISSUES IN PAMGUARD
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#✦ Inspect raw NA-like values before standardizing (determine what string values look like "empty" across object columns)
#%% Get all columns stored as text (object dtype; these are where stray NA strings hide)
obj_cols = data.select_dtypes(include="object").columns

# create empty dictionary to store each column name as key and NA-token count as value
suspects = {}
for col in obj_cols:
    # drop real NaNs, force to string, strip surrounding whitespace
    vals = data[col].dropna().astype(str).str.strip()
    # keep only values that match a known NA-like token (case-insensitive)
    hits = vals[vals.str.lower().isin(["", "na", "n/a", "nan", "null", "none", "-", "<na>", "nat"])]
    # record counts per column
    if not hits.empty:
        suspects[col] = hits.value_counts()

# print each flagged col + breakdown of its NA-like tokens
for col, vc in suspects.items():
    print(f"\n{col}:")
    print(vc)

# show columns that already contain true NaN as loaded, with counts
print("\nExisting NaN counts:")
print(data.isna().sum()[data.isna().sum() > 0])

    #˓ the following print-out indicates NO cells have stray NA strings ("na", "-", etc.) so ALL empty cells are already true NaN; if any cols had cells with stray NA strings, it will print the col name with the types of stay NA strings present in that col and the counts of cells with each type of stay NA string; cols NOT listed have NO rows with missing values
    #˓ Existing NaN counts:                 
    #˓ SequenceBitmap                   1482
    #˓ minNumber                        1482
    #˓ bestNumber                       1482
    #˓ maxNumber                        1482
    #˓ comment                          1391
    #˓ TMModelName1                     1482
    #˓ TMLatitude1                      1482
    #˓ ...                                  
    #˓ TMComment2                       1482
    #˓ dtype: int64                         

#✦ Check for duplicate or missing values in "UID" column
#%% Subset rows where UID is NaN/missing -or- rows where UID appears more than once (keep=False flags all copies) excluding missing values
missing_uid = data[data["UID"].isna()]
dup_uid = data[data["UID"].duplicated(keep=False) & data["UID"].notna()]

# only print warning if at least one missing UID was found
if not missing_uid.empty:
    # report how many rows are missing UID
    print(f"⚠️ [WARNING]: {len(missing_uid)} row(s) with MISSING UID values.")
    # list the DataFrame row indices of those rows
    print(f"  Row indices: {missing_uid.index.tolist()}")
# only print warning if at least one duplicated UID was found
if not dup_uid.empty:
    # report total duplicate rows and how many distinct UIDs are duplicated
    print(f"⚠️ [WARNING]: {len(dup_uid)} row(s) with DUPLICATE UID values ({dup_uid['UID'].nunique()} unique UID(s) affected).")
    # group duplicate rows by their shared UID value and list which row indices share that UID
    for uid, grp in dup_uid.groupby("UID"):
        print(f"  UID {uid}: row indices {grp.index.tolist()}")

# if NO missing or duplicate UIDs were found, print success message
if missing_uid.empty and dup_uid.empty:
    print("✅ UID check passed: no missing or duplicate values") 

        #𓇬 UID check passed: no missing or duplicate values

#✦ Check for duplicate or missing values in "Id" column
#%% Subset rows where ID is NaN/missing -or- rows where ID appears more than once (keep=False flags all copies) excluding missing values
missing_id = data[data["Id"].isna()]
dup_id = data[data["Id"].duplicated(keep=False) & data["Id"].notna()]

# only print warning if at least one missing ID was found
if not missing_id.empty:
    # report how many rows are missing ID
    print(f"⚠️ [WARNING]: {len(missing_id)} row(s) with MISSING ID values.")
    # list the DataFrame row indices of those rows
    print(f"  Row indices: {missing_id.index.tolist()}")
# only print warning if at least one duplicated ID was found
if not dup_id.empty:
    # report total duplicate rows and how many distinct IDs are duplicated
    print(f"⚠️ [WARNING]: {len(dup_id)} row(s) with DUPLICATE ID values ({dup_id['ID'].nunique()} unique ID(s) affected).")
    # group duplicate rows by their shared ID value and list which row indices share that ID
    for id, grp in dup_id.groupby("Id"):
        print(f"  ID {id}: row indices {grp.index.tolist()}")

# if NO missing or duplicate IDs were found, print success message
if missing_id.empty and dup_id.empty:
    print("✅ ID check passed: no missing or duplicate values") 

        #𓇬 ID check passed: no missing or duplicate values

#✦ Check for duplicate or missing values in "UTC" column
#%% Subset rows where UTC is NaN/missing -or- rows where UTC appears more than once (keep=False flags all copies) excluding missing values
missing_utc = data[data["UTC"].isna()]
dup_utc = data[data["UTC"].duplicated(keep=False) & data["UTC"].notna()]

# only print warning if at least one missing UTC was found
if not missing_utc.empty:
    # report how many rows are missing UTC
    print(f"⚠️ [WARNING]: {len(missing_utc)} row(s) with MISSING UTC values.")
    # list the DataFrame row indices of those rows
    print(f"  Row indices: {missing_utc.index.tolist()}")
# only print warning if at least one duplicated UTC was found
if not dup_utc.empty:
    # report total duplicate rows and how many distinct UTCs are duplicated
    print(f"⚠️ [WARNING]: {len(dup_utc)} row(s) with DUPLICATE UTC values ({dup_utc['UTC'].nunique()} unique UTC(s) affected).")
    # group duplicate rows by their shared UTC value and list which row indices share that UTC
    for utc, grp in dup_utc.groupby("UTC"):
        print(f"  UTC {utc}: row indices {grp.index.tolist()}")

# if NO missing or duplicate UTCs were found, print success message
if missing_utc.empty and dup_utc.empty:
    print("✅ UTC check passed: no missing or duplicate values") 

        #𓇬 UTC check passed: no missing or duplicate values

#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ REFINE FOR RELEVANT COLS + TIDY DATAFRAME                                                  
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#%% Create copy of raw df and select relevant columns to retain
tidy_data = data[
    [
        "Id",
        "UID",
        "UTC",
        "EventEnd",
        "PCLocalTime",
        "PCTime",
        "channels",
        "ChannelBitmap",
        "eventType",
        "colour",
        "nClicks",
        "comment"
    ]
].copy()

#%% Rename columns
tidy_data = tidy_data.rename(
    columns={
        "Id":               "ID",
        "UTC":              "event_start_UTC",
        "EventEnd":         "event_end_UTC",
        "PCLocalTime":      "event_start_AST",
        "PCTime":           "event_marked_by_analyst_AST",
        "ChannelBitmap":    "channel_bitmap",
        "eventType":        "event_classification",
        "colour":           "color_code",
        "nClicks":          "n_clicks"
    }
)

#%% Check data type of all cols
for col, dt in tidy_data.dtypes.items():
    print(f"{col}: {dt}")

    #˓ ID: int64 ꪜ  
    #˓ UID: int64 ꪜ  
    #˓ event_start_UTC: object ╳ 
    #˓ event_end_UTC: object ╳ 
    #˓ event_start_AST: object ╳ 
    #˓ event_marked_by_analyst_AST: object ╳ 
    #˓ channels: int64 ꪜ  
    #˓ channel_bitmap: int64 ꪜ  
    #˓ event_classification: object ╳ 
    #˓ color_code: int64 ꪜ  
    #˓ n_clicks: int64 ꪜ  
    #˓ comment: object ╳ 

#✦ Fix data types in datetime and string cols
#%% Convert datetime cols (UTC and AST timezones)
utc_cols = ["event_start_UTC", "event_end_UTC"]
ast_cols = ["event_start_AST", "event_marked_by_analyst_AST"]

# for UTC cols, parse and localize to UTC
for col in utc_cols:
    tidy_data[col] = pd.to_datetime(tidy_data[col], utc=True)

# for AST cols, parse and localize to AST (UTC-4) keeping tz-aware in AST
for col in ast_cols:
    tidy_data[col] = pd.to_datetime(tidy_data[col]).dt.tz_localize("Etc/GMT+4")

#%% Convert event_classification and comment cols to string dt with whitespace stripped
for col in ["event_classification", "comment"]:
    tidy_data[col] = tidy_data[col].str.strip().astype("string")

#%% Check data type fixes worked properly
for col, dt in tidy_data.dtypes.items():
    print(f"{col}: {dt}")

    #⋄ PRINT OUT SHOULD MATCH THIS:
    #⋄ ID: int64 *
    #⋄ UID: int64 *
    #⋄ event_start_UTC: datetime64[ns, UTC] *
    #⋄ event_end_UTC: datetime64[ns, UTC] *
    #⋄ event_start_AST: datetime64[ns, Etc/GMT+4] *
    #⋄ event_marked_by_analyst_AST: datetime64[ns, Etc/GMT+4] *
    #⋄ channels: int64
    #⋄ channel_bitmap: int64
    #⋄ event_classification: string *
    #⋄ color_code: int64 *
    #⋄ n_clicks: int64
    #⋄ comment: string

#%% Export tidy version of raw exported data from 'Click_Detector_OfflineEvents' table (downloaded from Pamguard_UVI2_Around_STX_20250306.sqlite3 database via SQLite Studio app)
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
tidy_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/HF_processed/tidy_pamguard_sqlite_clickevents_UVI2_Around_STX_20250306.csv")
tidy_data.to_csv(tidy_path, index=False)
print(f"Saved tidy pamguard sqlite click events CSV to: {tidy_path}")


#❥ ############################################################################################################
#❥ PART 2 - MATCH CLICK EVENT START DATETIMES TO TRUE 1-MIN SPECTROGRAM START DATETIMES + EXPORT FINAL CSV FOR SPECIES SEPARATION
#❥ ############################################################################################################
#✦ Import and format CSV of all HF recorded audio minutes
#%% Import CSV of all HF recorded audio minutes (derived from .wav filenames in script 3_all_HF_mins_from_filenames.py)
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
all_mins_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_all_mins_UVI2_Around_STX_20250306.csv")
all_mins = pd.read_csv(all_mins_path)

#%% Check data type of all cols in imported 'all_mins' df
for col, dt in all_mins.dtypes.items():
    print(f"{col}: {dt}")

    #˓ mission_name: object ╳ 
    #˓ start_datetime_UTC: object ╳ 
    #˓ end_datetime_UTC: object ╳ 
    #˓ av_datetime_UTC: object ╳ 

#%% Convert mission_name col to string
all_mins["mission_name"] = all_mins["mission_name"].str.strip().astype("string")

#%% Convert all 3 datetime cols to datetime64[ns, UTC] (parsed and localized to UTC)
for col in ["start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]:
    all_mins[col] = pd.to_datetime(all_mins[col], utc=True)

#%% Check data type fixes worked properly
for col, dt in all_mins.dtypes.items():
    print(f"{col}: {dt}")

    #⋄ PRINT OUT SHOULD MATCH THIS:
    #⋄ mission_name: string
    #⋄ start_datetime_UTC: datetime64[ns, UTC] *
    #⋄ end_datetime_UTC: datetime64[ns, UTC] *
    #⋄ av_datetime_UTC: datetime64[ns, UTC] *

#✦ Create copy of tidy_data df and edit for final CSV used for species separations
#%% Create copy of tidy_data df to be used for species separations and select only desired cols
my_data = tidy_data[
    [
        "ID",
        "UID",
        "event_start_UTC",
        "channels",
        "event_classification",
        "color_code",
        "n_clicks",
        "comment"
    ]
].copy()

#%% Rename columns
my_data = my_data.rename(
    columns={
        "event_start_UTC":      "pamguard_event_start_UTC",
        "channels":             "n_channels",
        "event_classification": "species_id",
        "n_clicks":             "event_n_clicks"
    }
)

#%% Check data type of all cols
for col, dt in my_data.dtypes.items():
    print(f"{col}: {dt}")

    #⋄ PRINT OUT SHOULD MATCH THIS:
    #⋄ ID: int64 *
    #⋄ UID: int64 *
    #⋄ pamguard_event_start_UTC: datetime64[ns, UTC] *
    #⋄ n_channels: int64
    #⋄ species_id: string *
    #⋄ color_code: int64 *
    #⋄ event_n_clicks: int64
    #⋄ comment: string

#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ DETERMINE *TRUE* SPECTROGRAM START/END/AV DATETIMES FOR EACH CLICK EVENT                   
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#%% Create copy of my_data df for adding true spectrogram datetime cols
match_data = my_data.copy()

#%% Created sorted versions of both keys (dataframes) in ascending order (requirement of 'merge_asof' used below)
match_data_sorted = match_data.sort_values("pamguard_event_start_UTC").reset_index(drop=True)
all_mins_sorted = all_mins.sort_values("av_datetime_UTC").reset_index(drop=True)

#%% Match pamguard_event_start_UTC value in 'match_data' df to NEAREST av_datetime_UTC value in 'all_mins' df + create new av_datetime_UTC col in 'match_data' df with matched spectrogram av datetime (*nearest-neighbor match - for each pamguard_event_start_UTC value in 'match_data_sorted' df, find closest av_datetime_UTC value in 'all_mins_sorted' df (direction="nearest"))
#༚ NOTE: using av_datetime_UTC col instead of start_datetime_UTC col in 'all_mins' df because pamguard_event_start_UTC value in 'match_data' df (aka the time of the first click selected when creating the click event) is more likely to be closer to the middle of the spectrogram window than the very beginning of it)
match_data_sorted = pd.merge_asof(
    match_data_sorted,
    all_mins_sorted[["av_datetime_UTC"]],
    left_on="pamguard_event_start_UTC",
    right_on="av_datetime_UTC",
    direction="nearest"
)

# print warning of any rows where the nearest av_datetime_UTC found in 'all_mins_sorted' is ≥2 mins DIFFERENT from pamguard_event_start_UTC in 'match_data_sorted' df
time_diff = (match_data_sorted["av_datetime_UTC"] - match_data_sorted["pamguard_event_start_UTC"]).abs()
flagged = match_data_sorted[time_diff >= pd.Timedelta(minutes=2)]
if not flagged.empty:
    # report how many events matched to a spectrogram window ≥2 min away
    print(f"⚠️ [WARNING]: {len(flagged)} event(s) matched to av_datetime_UTC ≥2 min from pamguard_event_start_UTC.")
    # list the UID and actual time gap for each flagged event
    for idx, row in flagged.iterrows():
        gap = (row["av_datetime_UTC"] - row["pamguard_event_start_UTC"]).total_seconds() / 60
        print(f"  UID {row['UID']}: {gap:+.2f} min gap")
else:
    print("✅ Match check passed: all events matched within 2 min of a spectrogram av_datetime")

    #𓇬 ✅ Match check passed: all events matched within 2 min of a spectrogram av_datetime

#%% Add start_datetime_UTC and end_datetime_UTC cols to 'match_data_sorted' df with values calculated from the new av_datetime_UTC col in that df (±30 sec around av_datetime_UTC)
match_data_sorted["start_datetime_UTC"] = match_data_sorted["av_datetime_UTC"] - pd.Timedelta(seconds=30)
match_data_sorted["end_datetime_UTC"]   = match_data_sorted["av_datetime_UTC"] + pd.Timedelta(seconds=30)

#%% Format all datetime cols in 'match_data_sorted' df (pamguard_event_start_UTC, start_datetime_UTC, end_datetime_UTC, av_datetime_UTC) as datetime64[ns, UTC] data type
for col in ["pamguard_event_start_UTC", "start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]:
    match_data_sorted[col] = pd.to_datetime(match_data_sorted[col], utc=True)

#%% Create copy of match_data_sorted df for final export as CSV to be used for species separations
final_HF_data = match_data_sorted.copy()

#%% Reorder cols
final_HF_data = final_HF_data[
    [
        "n_channels",
        "ID",
        "UID",
        "pamguard_event_start_UTC",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC",
        "species_id",
        "color_code",
        "event_n_clicks",
        "comment"
    ]
]

#%% Sort rows in ascending order by start_datetime_UTC col (earliest detections -> latest)
final_HF_data = final_HF_data.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Double check data type of each col before export
for col, dt in final_HF_data.dtypes.items():
    print(f"{col}: {dt}")

    #⋄ PRINT OUT SHOULD MATCH THIS:
    #⋄ n_channels: int64
    #⋄ ID: int64 *
    #⋄ UID: int64 *
    #⋄ pamguard_event_start_UTC: datetime64[ns, UTC] *
    #⋄ start_datetime_UTC: datetime64[ns, UTC] *
    #⋄ end_datetime_UTC: datetime64[ns, UTC] *
    #⋄ av_datetime_UTC: datetime64[ns, UTC] *
    #⋄ species_id: string *
    #⋄ color_code: int64 *
    #⋄ event_n_clicks: int64
    #⋄ comment: string

#%% Export final HF click events CSV for species separations
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
final_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/HF_processed/all_HF_clickevents_UVI2_Around_STX_20250306.csv")
final_HF_data.to_csv(final_path, index=False)
print(f"Saved final HF click events CSV to: {final_path}")