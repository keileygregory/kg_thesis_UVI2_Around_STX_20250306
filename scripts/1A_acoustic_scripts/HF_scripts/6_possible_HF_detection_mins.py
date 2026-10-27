'''
This script outputs a .csv file containing each minute when high-frequency detections were POSSIBLE by creating a list of all mins when HF audio was recorded (from filenames of .wav files in a directory) and subtracting mins during surfacings (aka too much noise in min spectrogram to see any detections)

Input all mins AND surfacing mins .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/3_data_analyzed/acoustic_analyzed/HF_analyzed
Output .csv directory: Same as input directory

𖠺 Created by Keiley Gregory on January 19, 2026
Last updated on July 15, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd
import numpy as np
import re

#❥ IMPORT CSV OF ALL MINS WHEN HIGH-FREQUENCY AUDIO WAS RECORDED --------------------------------------
#%% Import .csv of all mins when HF audio was recorded
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
all_mins_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_all_mins_UVI2_Around_STX_20250306.csv")
all_mins = pd.read_csv(all_mins_csv_path)

#%% Convert datetime columns to timezone-aware UTC datetimes (datetime64[ns, UTC])
dt_cols = ["start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]
for c in dt_cols:
    all_mins[c] = pd.to_datetime(all_mins[c], errors="coerce", utc=True)

#%% Warn on and drop rows where start/end failed to parse (NaT != NaT would let them survive the mask below)
n_bad_all = all_mins[["start_datetime_UTC", "end_datetime_UTC"]].isna().any(axis=1).sum()
if n_bad_all:
    print(f"⚠️ [WARNING]: dropped {n_bad_all} row(s) from 'all_mins' df with unparseable start/end datetimes")
all_mins = all_mins.dropna(subset=["start_datetime_UTC", "end_datetime_UTC"]).copy()

#%% Check data type of all cols (one per line)
for col, dt in all_mins.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: object (ㅱ does NOT matter in this specific instance)
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% 
#❋ Create set of start and end datetime pairs (start, end) to use for matching below
ALL_start_end_pairs = list(zip(all_mins["start_datetime_UTC"], all_mins["end_datetime_UTC"]))


#❥ IMPORT CSV OF MINUTES MARKED AS SURFACINGS IN HF AUDIO ---------------------------------------------
#%% Import .csv of surfacing mins in HF spectrograms
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
surfacings_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_surfacing_mins_UVI2_Around_STX_20250306.csv")
surfacings = pd.read_csv(surfacings_csv_path)

#%% Convert datetime columns to timezone-aware UTC datetimes (datetime64[ns, UTC])
for c in dt_cols:
    surfacings[c] = pd.to_datetime(surfacings[c], errors="coerce", utc=True)

#%% Warn on and drop rows where start/end failed to parse (NaT != NaT would let them survive the mask below)
n_bad_surf = surfacings[["start_datetime_UTC", "end_datetime_UTC"]].isna().any(axis=1).sum()
if n_bad_surf:
    print(f"⚠️ [WARNING]: dropped {n_bad_surf} row(s) from 'surfacings' df with unparseable start/end datetimes")
surfacings = surfacings.dropna(subset=["start_datetime_UTC", "end_datetime_UTC"]).copy()

#%% Check data type of all cols (one per line)
for col, dt in surfacings.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: object (ㅱ does NOT matter in this specific instance)
        #~ ID: int64
        #~ UID: int64
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% 
#❋ Create set of start and end datetime pairs (start, end) to use for matching below
SURFACING_start_end_pairs = list(zip(surfacings["start_datetime_UTC"], surfacings["end_datetime_UTC"]))


#❥ REFINE LIST TO MINUTES WHEN DETECTIONS WERE POSSIBLE (REMOVE MINS MARKED AS SURFACINGS) ------------
#%% Create new df of rows from 'all_mins' df with rows from 'surfacings' df removed
mask = np.array([pair not in SURFACING_start_end_pairs for pair in ALL_start_end_pairs])
possible_mins = all_mins.loc[mask].copy()

# Print summary message
print(
        f"Rows in 'surfacings' df = {len(surfacings)};"
        f"\nRows removed from 'all_mins' df = {len(all_mins) - len(possible_mins)};"
        f"\nRows remaining in 'possible_mins' df = {len(possible_mins)}"
    )

#ㅱ FOR UVI2_AROUND_STX_20250306 MISSION, PAMGUARD SHOWS NO HF AUDIO DATA EACH DAY DURING ENTIRE HOUR 12:00:00 (...11:57:44, GAP, 13:02:44...) --SO-- REMOVE all rows with start_datetime_UTC = 2025-03-** 12:**:**+**:** (ex: 2025-03-15 12:07:44+00:00) from csv of mins when HF detections were possible
#%% Create copy of df for removing daily 12:00:00 data gaps
possible_mins_nogap = possible_mins.copy()

# remove daily 12:00:00 gaps from df
possible_mins_nogap = possible_mins_nogap[
    possible_mins_nogap["start_datetime_UTC"].dt.hour != 12
].copy()
#ㅱ

#%% Set mission_name col to string data type
string_cols = ["mission_name"]
possible_mins_nogap[string_cols] = possible_mins_nogap[string_cols].astype("string")

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
possible_mins_nogap = possible_mins_nogap.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols (one per line)
for col, dt in possible_mins_nogap.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% Export df as CSV (output to 'LF_analyzed' folder in mission repo) for use in stats/arcgis mapping!!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
pos_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_possible_mins_UVI2_Around_STX_20250306.csv")
possible_mins_nogap.to_csv(pos_output_csv_path, index=False)
print(f"Saved detections possible mins CSV to: {pos_output_csv_path}")

###################################################################################
# Rows in 'surfacings' df = 533;
# Rows removed from 'all_mins' df = 533;
# Rows remaining in 'possible_mins' df = 4526
###################################################################################