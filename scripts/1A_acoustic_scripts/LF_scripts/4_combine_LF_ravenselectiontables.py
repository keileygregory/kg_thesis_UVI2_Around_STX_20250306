'''
This script combines multiple low-frequency selection table .txt (or .csv) files output by Raven Pro for a single mission into one dataframe exported as a CSV. 

Input .txt/.csv files (Raven Pro selection tables) directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/2_data_processed/acoustic_processed/LF_processed
Output combined .csv file directory: Same as input directory

𖠺 Created by Keiley Gregory on January 19, 2026
Last updated on March 8, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
from typing import Union, Sequence, Optional
import pandas as pd
import numpy as np
import re

#❥ IMPORT EACH INDIVIDUAL RAVENPRO SELECTION TABLE, LOAD DATA INTO INDIVIDUAL DATAFRAMES, AND TIDY EACH DATAFRAME
#%% Set path to each Raven Pro selection table .txt (or .csv) file for mission (each file = one round of analysis in Raven Pro)
#𖠜 CHANGE PATHS FOR CURRENT MISSION, ENSURE IN CORRECT ORDER
file_path_1 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0_stop0308T020843.csv")
file_path_2 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0308T020943_stop0308T113443.csv")
file_path_3 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0308T113543_stop0309T035043.csv")
file_path_4 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0309T035143_stop0309T064943.csv")
file_path_5 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0309T065043_stop0309T172743.csv")
file_path_6 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0309T172843_stop0310T023643.csv")
file_path_7 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0310T023743_stop0310T180843.csv")
file_path_8 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0310T180943_stop0312T225143.csv")
file_path_9 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0312T225243_stop0314T000043.csv")
file_path_10 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0314T000143_stop0315T002043.csv")
file_path_11 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0315T002143_stop0317T053043.csv")
file_path_12 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0317T053143_stop0318T174743.csv")
file_path_13 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0318T174843_stop0319T104543.csv")
file_path_14 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0319T104743_stop0319T112343.csv")
file_path_15 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0319T112443_stop0319T144243.csv")
file_path_16 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0319T144343_stop0321T101943.txt")
file_path_17 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0321T102043_stop0322T211643.txt")
file_path_18 = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_start0322T211743_stop0324T083543.txt")

#%% 
#༚ Function to import data in each file as an individual pandas DataFrame (*auto-detect .csv file vs tab-separated .txt file)
def read_file_df(file_path: Union[str, Path]) -> pd.DataFrame:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    suffix = file_path.suffix.lower()
    # .csv file
    if suffix == ".csv":
        return pd.read_csv(file_path)
    # tab-separated .txt file
    elif suffix == ".txt":
        return pd.read_csv(file_path, sep="\t")
    # warning message if file is not .csv or .txt file type
    else:
        raise ValueError(
            f"Unsupported file extension '{file_path.suffix}' for: {file_path.name}\n"
            "Expected .csv or .txt"
        )

# Import data (call above function)
#𖠜 UPDATE for all input file_path_* objects created above to be imported
raw_data_1 = read_file_df(file_path_1)
raw_data_2 = read_file_df(file_path_2)
raw_data_3 = read_file_df(file_path_3)
raw_data_4 = read_file_df(file_path_4)
raw_data_5 = read_file_df(file_path_5)
raw_data_6 = read_file_df(file_path_6)
raw_data_7 = read_file_df(file_path_7)
raw_data_8 = read_file_df(file_path_8)
raw_data_9 = read_file_df(file_path_9)
raw_data_10 = read_file_df(file_path_10)
raw_data_11 = read_file_df(file_path_11)
raw_data_12 = read_file_df(file_path_12)
raw_data_13 = read_file_df(file_path_13)
raw_data_14 = read_file_df(file_path_14)
raw_data_15 = read_file_df(file_path_15)
raw_data_16 = read_file_df(file_path_16)
raw_data_17 = read_file_df(file_path_17)
raw_data_18 = read_file_df(file_path_18)

#%% 
#༚ Function to tidy each raw_data_* df, add 'source_selection_table' column with values populated from source filename of selection table output by Raven Pro, and reorder columns (so all raw_data_*_tidy dfs have same column order for combining)
def tidy_and_tag(df: pd.DataFrame, file_path: Union[str, Path], column_order: Optional[Sequence[str]] = None) -> pd.DataFrame:
    df = df.copy()
    # strip trailing/leading whitespace from column names (NOT spaces between words in string)
    df.columns = [c.strip() for c in df.columns]
    # loop through each column in df
    for c in df.columns:
        df[c] = (
            df[c]
            # convert all data to string (so we can safely use .str methods)
            .astype(str)
            # strip trailing/leading whitespace from all cells in col (NOT spaces between words in string)
            .str.strip()
            # set empty cell values as NaN
            .replace({"nan": np.nan, "": np.nan})
        )
    # convert file_path to a Path object (works whether it was passed in as string or if already Path object)
    file_path = Path(file_path)
    # add new 'source_selection_table' column where EVERY row contains source filename
    df["source_selection_table"] = file_path.name
    # print warning message if any of the raw_data_* dfs are MISSING any cols in 'raw_cols_ordered' list
    if column_order is not None:
        missing = [col for col in column_order if col not in df.columns]
        if missing:
            print(
                "\n⚠️ WARNING: MISSING COLUMNS in selection table\n"
                f"  file: {file_path.name}\n"
                f"  MISSING: {missing}\n"
                f"  available columns: {list(df.columns)}"
            )
        # reorder columns (ensure same col order when combining dfs)
        ordered_existing = [col for col in column_order if col in df.columns]
        remaining = [col for col in df.columns if col not in ordered_existing]
        df = df[ordered_existing + remaining]
    return df

# Set column order
raw_cols_ordered = [
    "Selection",
    "View",
    "Channel",
    "Begin Time (s)",
    "End Time (s)",
    "Low Freq (Hz)",
    "High Freq (Hz)",
    "Begin File",
    "species",
    "source_selection_table"
]

# Tidy raw dfs and tag with source filename in added 'source_selection_table' column
#𖠜 UPDATE for all input raw_data_* dataframes
raw_data_1_tidy = tidy_and_tag(raw_data_1, file_path_1, column_order=raw_cols_ordered)
raw_data_2_tidy = tidy_and_tag(raw_data_2, file_path_2, column_order=raw_cols_ordered)
raw_data_3_tidy = tidy_and_tag(raw_data_3, file_path_3, column_order=raw_cols_ordered)
raw_data_4_tidy = tidy_and_tag(raw_data_4, file_path_4, column_order=raw_cols_ordered)
raw_data_5_tidy = tidy_and_tag(raw_data_5, file_path_5, column_order=raw_cols_ordered)
raw_data_6_tidy = tidy_and_tag(raw_data_6, file_path_6, column_order=raw_cols_ordered)
raw_data_7_tidy = tidy_and_tag(raw_data_7, file_path_7, column_order=raw_cols_ordered)
raw_data_8_tidy = tidy_and_tag(raw_data_8, file_path_8, column_order=raw_cols_ordered)
raw_data_9_tidy = tidy_and_tag(raw_data_9, file_path_9, column_order=raw_cols_ordered)
raw_data_10_tidy = tidy_and_tag(raw_data_10, file_path_10, column_order=raw_cols_ordered)
raw_data_11_tidy = tidy_and_tag(raw_data_11, file_path_11, column_order=raw_cols_ordered)
raw_data_12_tidy = tidy_and_tag(raw_data_12, file_path_12, column_order=raw_cols_ordered)
raw_data_13_tidy = tidy_and_tag(raw_data_13, file_path_13, column_order=raw_cols_ordered)
raw_data_14_tidy = tidy_and_tag(raw_data_14, file_path_14, column_order=raw_cols_ordered)
raw_data_15_tidy = tidy_and_tag(raw_data_15, file_path_15, column_order=raw_cols_ordered)
raw_data_16_tidy = tidy_and_tag(raw_data_16, file_path_16, column_order=raw_cols_ordered)
raw_data_17_tidy = tidy_and_tag(raw_data_17, file_path_17, column_order=raw_cols_ordered)
raw_data_18_tidy = tidy_and_tag(raw_data_18, file_path_18, column_order=raw_cols_ordered)


#❥ COMBINE SELECTION TABLE DATA FROM EACH ROUND OF RAVEN PRO ANALYSIS INTO SINGLE DATAFRAME IN ORDER OF NUMBER IN RAW_DATA_*_TIDY DF NAME
#%% Create empty list to store raw_data_*_tidy sequential numbers -x- actual dataframes
tidy_dfs = []

#%% 
#༚ FOR loop to extract sequential number from raw_data_*_tidy dataframe names
for var_name, obj in list(globals().items()):
    # regex pattern for raw_data_<number>_tidy df names (captures <number> part of df name)
    m = re.fullmatch(r"raw_data_(\d+)_tidy", var_name)
    # check if regex pattern matches and if variable value is actually pandas df
    if m and isinstance(obj, pd.DataFrame):
        # if criteria in above line passes, append 'tidy_dfs' list with tuple (extracted <number> as integer, actual df)
        tidy_dfs.append((int(m.group(1)), obj))

#%% Sort 'tidy_dfs' list by extracted <number> integers
tidy_dfs.sort(key=lambda x: x[0])

#%% Concatenate dfs in order (all rows from raw_data_1_tidy, THEN all rows from raw_data_2_tidy, THEN all rows from raw_data_3_tidy, etc...)
combined_tidy = pd.concat([df for _, df in tidy_dfs], ignore_index=True, sort=False)

# print confirmation
print(f"Combined {len(tidy_dfs)} dataframes -> {len(combined_tidy)} total rows")

#%% Export combined CSV
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/LF_processed/LF_UVI2_AroundSTX_COMBINED.csv")
combined_tidy.to_csv(output_csv_path, index=False)