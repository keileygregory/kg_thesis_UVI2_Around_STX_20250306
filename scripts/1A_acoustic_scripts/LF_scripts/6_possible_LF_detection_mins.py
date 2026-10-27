'''
This script outputs a .csv file containing each minute when low-frequency detections were POSSIBLE by creating a list of all mins when LF audio was recorded (from filenames of .wav files in a directory) and subtracting mins during surfacings (aka too much noise in min spectrogram to see any detections)

Input .wav filenames directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/process_wav2/done; input surfacings .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/3_data_analyzed/acoustic_analyzed/LF_analyzed
Output .csv directory: Same as input surfacings .csv directory

𖠺 Created by Keiley Gregory on January 19, 2026
Last updated on March 2, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd
import numpy as np
import re

#❥ GET LIST OF ALL MINUTES WHEN LOW-FREQUENCY AUDIO WAS RECORDED --------------------------------------
#%% Path to folder containing all low-frequency 60-second .wav files
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
WAV_DIR = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav2/done")

#%% Read all .wav filenames in WAV_DIR and add to 'wav_filenames' list
wav_filenames = sorted([
    p.name
    for p in WAV_DIR.iterdir()
    if p.is_file() and p.suffix == ".wav"
])

#%% Create pandas DataFrame where each .wav filename is a single row
df_wav_files = pd.DataFrame({"wav_file": wav_filenames})

# print confirmation message of count of total filenames added to df
print(f"\nTotal .wav files found: {len(df_wav_files)}")

#❋ Extract start datetime of each .wav file from filename and calculate av and end datetime of .wav file
#%% Regex to extract datetime from .wav filename (naming convention: {glider}_{mission}_###_LF_{YYYYMMDD}_{hhmmss}.wav)
dt_regex = re.compile(r"_(\d{8})_(\d{6})\.wav$", re.IGNORECASE)

#%% Function to extract start datetime from each .wav filename (if no .wav filename matching regex pattern is found, return NaN and print warning message)
def parse_start_datetime_utc(wav_name: str) -> pd.Timestamp:
    if pd.isna(wav_name):
        return pd.NaT
    m = dt_regex.search(str(wav_name))
    if not m:
        print(f"WARNING: no datetime match for wav file: {wav_name}")
        return pd.NaT
    yyyymmdd, hhmmss = m.group(1), m.group(2)
    # format extracted values as pandas datetime object
    ts = pd.to_datetime(f"{yyyymmdd}{hhmmss}", format="%Y%m%d%H%M%S", utc=True, errors="coerce")
    return ts

# Call function for dataframe
df_wav_files["start_datetime_UTC"] = df_wav_files["wav_file"].apply(parse_start_datetime_utc)

#%% Calculate end datetime and average datetime from extracted start datetime (.to_timedelta = change in time (Δt) from value in 'start_datetime_UTC')
df_wav_files["end_datetime_UTC"] = df_wav_files["start_datetime_UTC"] + pd.to_timedelta(60, unit="s")
df_wav_files["av_datetime_UTC"]  = df_wav_files["start_datetime_UTC"] + pd.to_timedelta(30, unit="s")

#%% Remove unnecessary columns and save as new dataframe
all_mins = df_wav_files[
    [
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
].copy()

#%% Add mission name column (same value for every row), set dt as pandas string dtype
#𖠜 CHANGE MISSION NAME FOR CURRENT MISSION
all_mins["mission_name"] = pd.Series("UVI2_Around_STX_20250306", index=all_mins.index, dtype="string")

#%% Reorder columns
all_mins = all_mins[
    [
        "mission_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
all_mins = all_mins.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols (one per line)
for col, dt in all_mins.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export df as CSV (output to 'LF_analyzed' folder in mission repo) for record-keeping
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
all_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/LF_all_mins_UVI2_Around_STX_20250306.csv")
all_mins.to_csv(all_output_csv_path, index=False)
print(f"Saved all mins CSV to: {all_output_csv_path}")

#%% 
#❋ Create set of start and end datetime pairs (start, end) to use for matching below
ALL_start_end_pairs = list(zip(all_mins["start_datetime_UTC"], all_mins["end_datetime_UTC"]))


#❥ IMPORT CSV OF MINUTES MARKED AS SURFACINGS IN LF AUDIO ---------------------------------------------
#%% Import CSV of surfacing mins in low-frequency spectrograms
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
surfacings_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/LF_surfacing_mins_UVI2_Around_STX_20250306.csv")
surfacings = pd.read_csv(surfacings_csv_path)

#%% Convert datetime columns to timezone-aware UTC datetimes (datetime64[ns, UTC])
dt_cols = ["start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]

for c in dt_cols:
    surfacings[c] = pd.to_datetime(surfacings[c], errors="coerce", utc=True)

#%% Check data type of all cols (one per line)
for col, dt in surfacings.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: object (*doesn't matter in this case)
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% 
#❋ Create set of start and end datetime pairs (start, end) to use for matching below
SURFACING_start_end_pairs = list(zip(surfacings["start_datetime_UTC"], surfacings["end_datetime_UTC"]))


#❥ REFINE LIST TO MINUTES WHEN DETECTIONS WERE POSSIBLE (REMOVE MINS MARKED AS SURFACINGS) ------------
#%% Create new df of rows from 'all_mins' df with rows from 'surfacings' df removed
possible_mins = all_mins.loc[
    ~pd.Series(ALL_start_end_pairs).isin(SURFACING_start_end_pairs)
].copy()

# print summary message
print(
        f"Rows in 'surfacings' df = {len(surfacings)};"
        f"\nRows removed from 'all_mins' df = {len(all_mins) - len(possible_mins)};"
        f"\nRows remaining in 'possible_mins' df = {len(possible_mins)}"
    )

#%% Set mission_name col to string data type
string_cols = ["mission_name"]
possible_mins[string_cols] = possible_mins[string_cols].astype("string")

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
possible_mins = possible_mins.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols (one per line)
for col, dt in possible_mins.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export df as CSV (output to 'LF_analyzed' folder in mission repo) for use in stats/arcgis mapping!!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
pos_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/LF_analyzed/LF_possible_mins_UVI2_Around_STX_20250306.csv")
possible_mins.to_csv(pos_output_csv_path, index=False)
print(f"Saved detections possible mins CSV to: {pos_output_csv_path}")