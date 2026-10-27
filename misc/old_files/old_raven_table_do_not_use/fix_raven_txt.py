#%%
import csv
from pathlib import Path
import pandas as pd
import numpy as np
import re

#%% Import CSV of combined low-frequency selection table data
csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_processed/acoustic_processed/LF_processed/old_do_not_use/LF_UVI2_AroundSTX_combined.csv")
combined_raw_data = pd.read_csv(csv_path)

#%% Remove 'source_selection_table' column that is NOT in original Raven Pro output .txt files + 'call_type' column since getting call type values from imported collapsed CSV
combined_data = combined_raw_data[
    [   
        "Selection",
        "View",
        "Channel",
        "Begin Time (s)",
        "End Time (s)",
        "Low Freq (Hz)",
        "High Freq (Hz)",
        "Begin File",
        "species"
    ]
].copy()

#%% Add new columns 'call_density_ranking' and 'call_type' and fill with NaN placeholder
new_cols = ["call_density_rank", "call_type"]
combined_data[new_cols] = np.nan

#%% Reorder cols
combined_data = combined_data[
    [   
        "Selection",
        "View",
        "Channel",
        "Begin Time (s)",
        "End Time (s)",
        "Low Freq (Hz)",
        "High Freq (Hz)",
        "Begin File",
        "species",
        "call_density_rank",
        "call_type"
    ]
]

#%% Rename columns (will change back later - need to remove spaces between words in col names for collapse code to work)
combined_data = combined_data.rename(
    columns={
        "Begin Time (s)": "Begin_Time_s", 
        "End Time (s)": "End_Time_s",
        "Low Freq (Hz)": "Low_Freq_Hz",
        "High Freq (Hz)": "High_Freq_Hz",        
        "Begin File": "Begin_File"}
)

#######################################################################

#%% Create new df for collapsing rows
combined_collapsed = combined_data.copy()

#%% Ensure join keys are clean strings
combined_collapsed["Begin_File"] = combined_collapsed["Begin_File"].astype(str).str.strip()
combined_collapsed["species"] = combined_collapsed["species"].astype(str).str.strip()

#%% Set columns to match rows by
match_cols = ["Begin_File", "species"]

#%% COLLAPSE rows - since ONLY care about values in cols 'Channel', 'Begin File', and 'species' which all have SAME value in all rows for single spectrogram and species (aka rows going into single collapsed row), just use value in first row of collapsed row input rows ("first")
combined_collapsed = (
    combined_data
    # group rows by 'match_cols' list of columns previously defined
    .groupby(match_cols, dropna=False, as_index=False)
    .agg(
        # keep value from first row
        Selection=("Selection", "first"),
        View=("View", "first"),
        Channel=("Channel", "first"),
        Begin_Time_s=("Begin_Time_s", "first"),
        End_Time_s=("End_Time_s", "first"),
        Low_Freq_Hz=("Low_Freq_Hz", "first"),
        High_Freq_Hz=("High_Freq_Hz", "first"),
        Begin_File=("Begin_File", "first"),
        species=("species", "first"),
        call_density_rank=("call_density_rank", "first"),
        call_type=("call_type", "first")
    )
)

########################################################

#%% Create new df for combining dfs
MASTER_DF = combined_collapsed.copy()

#%% Import CSV of collapsed df
csv_path_2 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_processed/acoustic_processed/LF_processed/old_do_not_use/LF_UVI2_AroundSTX_collapsed.csv")
collapsed_raw_data = pd.read_csv(csv_path_2)

#%% Ensure join keys are clean strings
MASTER_DF["Begin_File"] = MASTER_DF["Begin_File"].astype(str).str.strip()
MASTER_DF["species"] = MASTER_DF["species"].astype(str).str.strip()
collapsed_raw_data["wav_file"] = collapsed_raw_data["wav_file"].astype(str).str.strip()
collapsed_raw_data["species"] = collapsed_raw_data["species"].astype(str).str.strip()

#%% Merge dfs using BOTH conditions: (1) the string value in ‘wav_file’ column of ‘collapsed_raw_data’ dataframe EXACTLY MATCHES string value in ‘Begin_File’ column of ‘MASTER_DF’ dataframe (2) the string value in ‘species’ column of ‘collapsed_raw_data’ dataframe EXACTLY MATCHES string value in ‘species’ column of ‘MASTER_DF’ dataframe
MASTER_DF = MASTER_DF.merge(
    collapsed_raw_data[["wav_file", "species", "call_density_ranking", "call_type"]],
    how="left",
    left_on=["Begin_File", "species"],
    right_on=["wav_file", "species"],
    suffixes=("", "_src")
)

#%% Populate target columns
MASTER_DF["call_density_rank"] = MASTER_DF["call_density_ranking"]
MASTER_DF["call_type"] = MASTER_DF["call_type_src"]

#%% Drop helper columns
MASTER_DF = MASTER_DF.drop(
    columns=["wav_file", "call_density_ranking", "call_type_src"],
    errors="ignore"
)

############################################################

#%% Create new df for cleaning/fixing final MASTER_DF
MASTER_DF_clean = MASTER_DF.copy()

#%% Fix incorrect 'call_density_rank' values (=4 and =5) --> make all incorrect rows 'call_density_rank' = 3
# cap call_density_rank at 3 (safely handles NaN / non-numeric)
MASTER_DF_clean["call_density_rank"] = pd.to_numeric(
    MASTER_DF_clean["call_density_rank"],
    errors="coerce"
).clip(upper=3)

#%% Set call_density_rank to NaN for all rows where species == "s"
MASTER_DF_clean.loc[MASTER_DF_clean["species"] == "s", "call_density_rank"] = np.nan

#%% Print all unique values in call_type (including NaN)
#𖠜 VALID CALL TYPE CODES: 1, 2, 3, 4, 5, 12, 13, 14, 23, 24, 34
unique_call_types = MASTER_DF_clean["call_type"].drop_duplicates()
print(unique_call_types.to_string(index=False)) # all codes in df are valid

#%% Create dictionary of valid values for 'species' col
allowed_species = {"h", "m", "s"}

#%% Print rows where species is missing (NaN) or NOT exactly equal to one of the allowed species codes ("h", "m", or "s")
bad_species_mask = (
    MASTER_DF_clean["species"].isna() |
    (~MASTER_DF_clean["species"].astype(str).str.strip().isin(allowed_species))
)

bad_species_rows = MASTER_DF_clean.loc[
    bad_species_mask,
    ["Selection", "Begin_File", "call_density_rank", "species"]
].copy()

if bad_species_rows.empty:
    print("\nALL rows have valid species codes (h/m/s) and none are missing.")
else:
    print(f"\n⚠️ [WARNING] Rows with missing/invalid species codes: {len(bad_species_rows)}\n")
    print(bad_species_rows.to_string(index=True))

#%% Delete rows where 'species' is missing (NaN / None / blank / "None")
missing_species_mask = (
    MASTER_DF_clean["species"].isna() |
    (MASTER_DF_clean["species"].astype(str).str.strip() == "") |
    (MASTER_DF_clean["species"].astype(str).str.strip().str.lower() == "none")
)

# Drop those rows
MASTER_DF_clean = MASTER_DF_clean.loc[~missing_species_mask].copy()

# Optional: print confirmation
print(f"Rows remaining after dropping missing species rows: {len(MASTER_DF_clean)}")

#%% Check data type of 'call_density_rank' and 'call_type' cols
print(MASTER_DF_clean["call_density_rank"].dtype)
print(MASTER_DF_clean["call_type"].dtype)

#%% Convert float64 formatted numbers in 'call_density_rank' and 'call_type' cols (ex: 12.0, etc) to integers (NO decimal points (ex: 12, etc))
# convert call_density_rank to nullable integer (Int64 is pandas "nullable integer" data type = *keeps NaN)
MASTER_DF_clean["call_density_rank"] = pd.to_numeric(
    MASTER_DF_clean["call_density_rank"],
    errors="coerce"
).astype("Int64")

# convert call_type to nullable integer (Int64 keeps NaN)
MASTER_DF_clean["call_type"] = pd.to_numeric(
    MASTER_DF_clean["call_type"],
    errors="coerce"
).astype("Int64")

############################################################################################

#%% Rename cols back to Raven Pro output .txt file format (with spaces between words in col names)
MASTER_DF_clean = MASTER_DF_clean.rename(
    columns={
        "Begin_Time_s": "Begin Time (s)",
        "End_Time_s": "End Time (s)",
        "Low_Freq_Hz": "Low Freq (Hz)",
        "High_Freq_Hz": "High Freq (Hz)",        
        "Begin_File": "Begin File"}
)

#%% Create list of columns to sort row order by
sort_cols = ["Begin File", "species"]

#%% Sort rows in 'MASTER_DF_clean' ascending order by 'Begin File' col, then by 'species' col
MASTER_DF_clean = (
    MASTER_DF_clean
    .sort_values(
        by=sort_cols,
        kind="mergesort",
        key=lambda s: s.astype(str).str.strip()
    )
    .reset_index(drop=True)
)

#%% Export to CSV for safekeeping/just in case .txt file gets messed up
output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_processed/acoustic_processed/LF_processed/old_do_not_use/FIXED_MASTER_TXTTABLE_start0_stop0308T001243.csv")
MASTER_DF_clean.to_csv(output_csv_path, index=False)

# ---------------------------------------

#%% Create new df for exporting as tab-separated .txt file
MASTER_DF_txtfile = MASTER_DF_clean.copy()

#%% Sort rows in 'MASTER_DF_clean' ascending order by 'Begin File' col, then by 'species' col
MASTER_DF_txtfile = (
    MASTER_DF_txtfile
    .sort_values(
        by=sort_cols,
        kind="mergesort",
        key=lambda s: s.astype(str).str.strip()
    )
    .reset_index(drop=True)
)

#%% Check data type of all cols (one per line)
for col, dt in MASTER_DF_txtfile.dtypes.items():
    print(f"{col}: {dt}")
        # Selection: int64 (example value: 510)
        # View: object (example value: Spectrogram 1)
        # Channel: int64 (example value: 1)
        # Begin Time (s): float64 (example value: 29.61758758)
        # End Time (s): float64 (example value: 29.61758758)
        # Low Freq (Hz): float64 (example value: 453.333)
        # High Freq (Hz): float64 (example value: 453.333)
        # Begin File: object (example value: UVI2_Around_STX_001_LF_20250306_185746.wav)
        # species: object (example value: h)
        # call_density_rank: Int64 (example value: 2)
        # call_type: Int64 (example value: 13)

#%% Column-specific formatter functions to match Raven formatting exactly for these fields when exporting to tab-separated .txt file
# Helper function to check for missing values
def _is_missing(x) -> bool:
    return pd.isna(x) or str(x).strip().lower() in {"nan", "none"}

# Function to format Begin/End Time cols (Raven .txt output shows Begin/End Time values with 9 decimals)
def fmt_time_9(x) -> str:
    # if cell value missing (NaN/None/"nan"/"none"/blank), export as empty string (*keeps field blank in tab-separated .txt instead of writing "nan"*)
    if _is_missing(x):
        return ""
    # if cell value exists, format as float with 9 decimal places
    return f"{float(x):.9f}"

# Function to format Low/High Freq cols (Raven .txt output shows Low/High Freq values with 3 decimals)
def fmt_freq_3(x) -> str:
    # if cell value missing (NaN/None/"nan"/"none"/blank), export as empty string (*keeps field blank in tab-separated .txt instead of writing "nan"*)
    if _is_missing(x):
        return ""
    # if cell value exists, format as float with 3 decimal places
    return f"{float(x):.3f}"

# Generic format function for everything else (keep missing values truly blank, otherwise write the value as a plain string (NO extra quotes added)
def fmt_default(x) -> str:
    # if cell value missing (NaN/None/"nan"/"none"/blank), export as empty string (*keeps field blank in tab-separated .txt instead of writing "nan"*)
    if _is_missing(x):
        return ""
    # if cell value exists, convert to string exactly as-is (best-effort)
    return str(x)

#%% Build formatter map (only applies to Begin/End Times and Low/High Freq columns)
formatters = {
    "Begin Time (s)": fmt_time_9,
    "End Time (s)": fmt_time_9,
    "Low Freq (Hz)": fmt_freq_3,
    "High Freq (Hz)": fmt_freq_3,
}

#%% Path for output .txt file
output_txt_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0_stop0308T001243.txt")

#%% Create list of cols to export to txt file
cols_out = list(MASTER_DF_txtfile.columns)

#%% WRITE true tab-separated .txt file (no quoting; blanks preserved)
with output_txt_path.open("w", encoding="utf-8", newline="") as f:
    # create 'writer' object with defined settings for writing output rows
    writer = csv.writer(
        f,
        # TAB-separated format for .txt file (same as Raven Pro output)
        delimiter="\t",
        # set Unix newline character for line break between rows (same line ending used in output Raven Pro tab-separated .txt files)
        lineterminator="\n",
        # do NOT add quotations around values in any cells (except in cases where qoutations are absolutely necessary to keep file parseable - NOT applicable for this df (ex: cell value = {abc\tdef} requires added "" to prevent {abc} and {def} from being separated into 2 different columns))
        quoting=csv.QUOTE_MINIMAL,
        quotechar='"',     # (NOT applicable for this df) if added quotations are required use "" (instead of '')
        escapechar="\\",   # (NOT applicable for this df) if special characters found in cell, control representation to avoid breaking file (ex: if double quote in cell value = 'He said "hi"' -> "He said \"hi\"")
    )
    # write header row for all columns in 'cols_output' list
    writer.writerow(cols_out)
    # loop through each row in 'MASTER_DF_txtfile' df and return row index + actual row data (as Series)
    for _, row in MASTER_DF_txtfile.iterrows():
        # create empty list to store data for current row in loop that will be added to output to .txt file
        out_row = []
        # loops through cols (in header order from 'cols_out')
        for c in cols_out:
            # stores cell value from df for column ('c') as 'x'
            x = row[c]
            # if col exists in 'formatters' dictionary created above, use special formatter functions ('fmt_time_9' for Begin/End Time cols, 'fmt_freq_3' for Low/High Freq cols)
            # if col does NOT exist in 'formatters' dictionary, use default stringify function ('fmt_default')
            fmt = formatters.get(c, fmt_default)
            # format cell value ('x') accordingly and add to output list for current row in loop
            out_row.append(fmt(x))
        # write completed 'out_row' output list as one line (= one row) in .txt file
        writer.writerow(out_row)