'''
This script tidies and fixes errors (duplicates/invalid or missing values) in all low-frequency acoustic analysis data for the mission, separates the combined data by species (or surfacings), and outputs final .csv files for each species' acoustic analysis results.

Input combined .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/2_data_processed/acoustic_processed/LF_processed
Output species/surfacings .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/3_data_analyzed/acoustic_analyzed/LF_analyzed

𖠺 Created by Keiley Gregory on January 21, 2026
Last updated on June 23, 2026
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

#✦ TIDY DATAFRAME + EXTRACT START DATETIME FROM FILENAME + INSPECT SPECIES ID CODE DATA (IN PREPARATION TO SPLIT DF BY SPECIES)                                    
#%% Remove unnecessary columns output by Raven Pro and save as new dataframe
data = raw_data[
    [
        "Channel",
        "Begin File",
        "species",
        "source_selection_table"
    ]
].copy()

#%% Rename columns
data = data.rename(columns={"Channel": "n_channels", "Begin File": "wav_file"})

#%% Add new manually set cols + cols for subsequent calculations and fill with pandas NA placeholder
new_cols = [
    "sample_rate_kHz",
    "bit_depth",
    "start_datetime_UTC",
    "end_datetime_UTC",
    "av_datetime_UTC"
]
data[new_cols] = pd.NA

#%% Manually enter values in cols 'sample_rate_kHz', 'bit_depth', and 'mission_name' (same value for all rows in each col)
data["sample_rate_kHz"] = 2
data["bit_depth"] = 16
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
int_cols = ["n_channels", "sample_rate_kHz", "bit_depth"]
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
        "wav_file",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC",
        "species",
        "source_selection_table"
    ]
]

#✦ EXTRACT START DATETIME OF AUDIO CLIP FROM .WAV FILENAME (IN 'WAV_FILE' COL) + CALCULATE END AND MIDPOINT DATETIME COLS
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

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ wav_file: string
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *
        #~ species: string
        #~ source_selection_table: string

#✦ DEFINE MATCH VALUE FUNCTION FOR MANUAL CORRECTIONS
#%% Function for manual corrections: if the value is missing (pd.NA/np.nan/None), match rows where the series is missing; otherwise match rows where the series equals the value
def match_value(series: pd.Series, value) -> pd.Series:
    return series.isna() if pd.isna(value) else (series == value)

#%% Create copy of data df to make manual species ID fixes in if applicable (if no fixes necessary, then data_speciesfix df used in all subsequent code is just exact copy of data df)
data_speciesfix = data.copy()

#˚ INVALID/MISSING *SPECIES* CORRECTIONS - MUST RE-REVIEW SPECTROGRAMS AND MANUALLY ENTER CORRECTED SPECIES FOR EACH ROW
#%% Create dictionary of valid species codes
valid_species = {"h", "m", "s"}

# Create boolean mask (True = 'species' col value missing OR not in {"h","m","s"})
bad_species_mask = data_speciesfix["species"].isna() | (~data_speciesfix["species"].isin(valid_species))

# Create subset of 'data_speciesfix' df for rows that fail species validity check
bad_species_rows = data_speciesfix.loc[
    # only keep rows with missing or invalid species code (bad_species_mask = True)
    bad_species_mask,
    # include data from selected cols in printed warning message
    ["wav_file", "species", "source_selection_table"]
].copy()

# Print warning for any rows in df where 'species' col value is missing or invalid (if NO rows with missing/invalid species code found, print success message)
if bad_species_rows.empty:
    print("\n✅ All rows have a valid species code (h, m, or s)")
# if any rows have missing/invalid species code found, print count all 'bad' rows and data from selected cols (+ original row index number) for each row
else:
    print(f"\n⚠️ [WARNING] Rows with missing/invalid species codes: {len(bad_species_rows)}\n")
    print(bad_species_rows.to_string(index=True))

#%% Dictionary of manual fixes (*included "species" in row matching conditions
# ("wav_file", "species", "source_selection_table"): fixed "species"
#𖠜 CHANGE FIXES TO APPLY TO WARNING MESSAGE PRINT-OUT FOR CURRENT MISSION
species_fixes = {
    ("UVI2_Around_STX_005_LF_20250308_060943.wav", "w", "LF_UVI2_AroundSTX_start0308T020943_stop0308T113443.csv"): "s",
    ("UVI2_Around_STX_008_LF_20250309_065043.wav", pd.NA, "LF_UVI2_AroundSTX_start0309T065043_stop0309T172743.csv"): "h",
    ("UVI2_Around_STX_019_LF_20250312_165443.wav", ",", "LF_UVI2_AroundSTX_start0310T180943_stop0312T225143.csv"): "m",
    ("UVI2_Around_STX_022_LF_20250313_203643.wav", "s'", "LF_UVI2_AroundSTX_start0312T225243_stop0314T000043.csv"): "s",
    ("UVI2_Around_STX_028_LF_20250315_211943.wav", pd.NA, "LF_UVI2_AroundSTX_start0315T002143_stop0317T053043.csv"): "s",
    ("UVI2_Around_STX_035_LF_20250318_063843.wav", "4", "LF_UVI2_AroundSTX_start0317T053143_stop0318T174743.csv"): "h",
    ("UVI2_Around_STX_049_LF_20250322_190843.wav", pd.NA, "LF_UVI2_AroundSTX_start0321T102043_stop0322T211643.txt"): "h"
}

#%% Loop through each line in 'species_fixes' dictionary and apply species fixes to 'data_speciesfix' df
for (wav, spc, src), new_species in species_fixes.items():
    # build match mask for species column (*if spc is missing (pd.NA/np.nan/None) then match rows where species is missing; otherwise, match rows where species equals spc exactly)
    spc_match = match_value(data_speciesfix["species"], spc)
    # combine all conditions into single boolean Series mask (*row is selected ONLY if it matches: 1) the wav filename, 2) the species condition (including "missing species" cases), AND 4) the source_selection_table filename)
    mask = (
        (data_speciesfix["wav_file"] == wav)                    # match exact wav_file string
        & spc_match                                             # match species (or species is missing)
        & (data_speciesfix["source_selection_table"] == src)    # match exact source table string
    ).fillna(False)                                             # if any part produced pd.NA in the mask, treat it as False (NOT a match)
    # count how many rows in df match conditions for current line in 'species_fixes' dictionary (True counts as 1, False as 0)
    n = int(mask.sum())
    # if no rows in df match conditions for current line in 'species_fixes' dictionary (no fixes can be made), print warning message (no edits possible)
    if n == 0:
        print(
            "⚠️ SPECIES FIX NOT APPLIED (row not found): "
            f"wav_file = {wav}, species = {spc}, source_selection_table = {src}"
        )
        continue
    # if matching row is successfully found, print success summary message and APPLY edits (*it is ok if fix applies to more than one row since duplicates have NOT been removed yet)
    else:
        print(
            "✅ SPECIES FIX SUCCESSFULLY APPLIED: "
            f"wav_file = {wav}, species = {spc}, source_selection_table = {src} "
            f"→ new_species={new_species}"
        )
    data_speciesfix.loc[mask, "species"] = new_species


#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰
#❥ HUMPBACK WHALES ----------------------------------------------------------------------------------------------------------------
#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰
#%% Create new df filtered to only rows with species humpback (species == "h")
humpback = data_speciesfix.loc[data_speciesfix["species"] == "h"].copy()

#%% Create new 'clean' df and remove cols 'wav_file', 'species' (with "h" abbreviation), and 'source_selection_table'
humpback_clean = humpback.drop(columns=["wav_file", "species", "source_selection_table"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
humpback_clean["suborder"] = "Mysticeti"
humpback_clean["family"] = "Balaenopteridae"
humpback_clean["genus"] = "Megaptera"
humpback_clean["species"] = "novaeangliae"
humpback_clean["common_name"] = "humpback whale"

#%% Clean strings in classification cols (ensure string format, strip whitespace)
humpback_clean["suborder"] = humpback_clean["family"].astype("string").str.strip()
humpback_clean["family"] = humpback_clean["family"].astype("string").str.strip()
humpback_clean["genus"] = humpback_clean["genus"].astype("string").str.strip()
humpback_clean["species"] = humpback_clean["species"].astype("string").str.strip()
humpback_clean["common_name"] = humpback_clean["common_name"].astype("string").str.strip()

#%% Reorder columns
humpback_clean = humpback_clean[
    [
        "mission_name",
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
        "av_datetime_UTC"
    ]
]

#%% Create copy of humpback_clean df to make manual duplicate row fixes in if applicable (if no fixes necessary, then humpback_nodup df used in all subsequent code is just exact copy of humpback_clean df)
humpback_nodup = humpback_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
hb_true_dup_mask = humpback_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
hb_n_true_dups = int(hb_true_dup_mask.sum())

# Drop extra copies of duplicate rows
humpback_nodup = humpback_nodup.loc[~hb_true_dup_mask].copy()
print(
    f"✅ Removed {hb_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(humpback_clean)} → {len(humpback_nodup)}"
)
        #𓇬 ✅ Removed 31 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 2850 → 2819

#%% Create copy of humpback_nodup df to use for final output CSV
humpback_final = humpback_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
humpback_final = humpback_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in humpback_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% Export final humpback df as CSV (output to 'LF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
hb_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/humpback_analyzed_UVI2_Around_STX_20250306.csv")
humpback_final.to_csv(hb_output_csv_path, index=False)
print(f"Saved humpback CSV to: {hb_output_csv_path}")


#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰
#❥ MINKE WHALES -------------------------------------------------------------------------------------------------------------------
#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰
#%% Create new df filtered to only rows with species minke (species == "m")
minke = data_speciesfix.loc[data_speciesfix["species"] == "m"].copy()

#%% Create new 'clean' df and remove cols 'wav_file', 'species' (with "m" abbreviation), and 'source_selection_table'
minke_clean = minke.drop(columns=["wav_file", "species", "source_selection_table"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
minke_clean["suborder"] = "Mysticeti"
minke_clean["family"] = "Balaenopteridae"
minke_clean["genus"] = "Balaenoptera"
minke_clean["species"] = "acutorostrata"
minke_clean["common_name"] = "minke whale"

#%% Clean strings in classification cols (ensure string format, strip whitespace)
minke_clean["suborder"] = minke_clean["family"].astype("string").str.strip()
minke_clean["family"] = minke_clean["family"].astype("string").str.strip()
minke_clean["genus"] = minke_clean["genus"].astype("string").str.strip()
minke_clean["species"] = minke_clean["species"].astype("string").str.strip()
minke_clean["common_name"] = minke_clean["common_name"].astype("string").str.strip()

#%% Reorder columns
minke_clean = minke_clean[
    [
        "mission_name",
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
        #𓇬 ✅ Removed 34 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 819 → 785

#%% Create copy of minke_nodup df to use for final output CSV
minke_final = minke_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
minke_final = minke_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in minke_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% Export final minke df as CSV (output to 'LF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
mk_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/minke_analyzed_UVI2_Around_STX_20250306.csv")
minke_final.to_csv(mk_output_csv_path, index=False)
print(f"Saved minke CSV to: {mk_output_csv_path}")


#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱ 
#❥ SURFACING MINUTES ---------------------------------------------------------------------------------------------------------------------------------------------------
#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱ 
#%% Create new df filtered to only rows with surfacing mins (species == "s")
surfacings = data_speciesfix.loc[data_speciesfix["species"] == "s"].copy()

#%% Create new 'surfacings_clean' df and remove unnecessary cols
surfacings_clean = surfacings.drop(columns=["n_channels", "sample_rate_kHz", "bit_depth", "wav_file", "species", "source_selection_table"], errors="ignore").copy()

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

        #𓇬 ✅ Removed 33 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 2806 → 2773

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

#%% Check data type of all cols
for col, dt in surfacings_nodup.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% Export final surfacings df as CSV (output to 'LF_analyzed' folder in mission repo); this CSV will be used to remove mins where detections are NOT possible
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
surf_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/LF_surfacing_mins_UVI2_Around_STX_20250306.csv")
surfacings_nodup.to_csv(surf_output_csv_path, index=False)
print(f"Saved surfacings CSV to: {surf_output_csv_path}")