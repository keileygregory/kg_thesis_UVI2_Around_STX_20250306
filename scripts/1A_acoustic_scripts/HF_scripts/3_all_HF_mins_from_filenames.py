'''
This script creates a .csv file with one row per each minute when high-frequency audio was recorded using datetime stamps derived from high-frequency .wav filenames.

Input .wav file(name)s directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/process_wav3
Output .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/3_data_analyzed/acoustic_analyzed/HF_analyzed

𖠺 Created by Keiley Gregory on April 9, 2026
Last updated on April 9, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd
import numpy as np
import re

#❥ GET LIST OF ALL MINUTES WHEN HIGH-FREQUENCY AUDIO WAS RECORDED                                                                     
#%% Path to folder containing all high-frequency 60-second .wav files
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
WAV_DIR = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav3")

#%% Read all .wav filenames in WAV_DIR and add to 'wav_filenames' list
wav_filenames = sorted([
    p.name
    for p in WAV_DIR.iterdir()
    if p.is_file() and p.suffix == ".wav"
])

#%% Create pandas DataFrame where each .wav filename is a single row
df_wav_files = pd.DataFrame({"wav_file": wav_filenames})

# Print confirmation message of count of total filenames added to df
print(f"\nTotal .wav files found: {len(df_wav_files)}")


#❥ EXTRACT START DATETIME OF EACH .WAV FILE FROM FILENAME AND CALCULATE AV AND END DATETIME OF .WAV FILE
#%% 
#༚ Regex to extract datetime from .wav filename (naming convention: {glider}_{mission}_###_HF_{YYYYMMDD}_{hhmmss}.wav)
dt_regex = re.compile(r"_(\d{8})_(\d{6})\.wav$", re.IGNORECASE)

#%% 
#༚ Function to extract start datetime from each .wav filename (if no .wav filename matching regex pattern is found, return NaN and print warning message)
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

#%% 
#༚ Calculate end datetime and average datetime from extracted start datetime (.to_timedelta = change in time (Δt) from value in 'start_datetime_UTC')
df_wav_files["end_datetime_UTC"] = df_wav_files["start_datetime_UTC"] + pd.to_timedelta(60, unit="s")
df_wav_files["av_datetime_UTC"]  = df_wav_files["start_datetime_UTC"] + pd.to_timedelta(30, unit="s")


#❥ TIDY AND EXPORT
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

#%% Check data type of all cols (one per line)
for col, dt in all_mins.dtypes.items():
    print(f"{col}: {dt}")

        #⋄ PRINT OUT SHOULD MATCH THIS:
        #⋄ mission_name: string
        #⋄ start_datetime_UTC: datetime64[ns, UTC] *
        #⋄ end_datetime_UTC: datetime64[ns, UTC] *
        #⋄ av_datetime_UTC: datetime64[ns, UTC] *

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
all_mins = all_mins.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Export df as CSV (output to 'HF_analyzed' folder in mission repo) for record-keeping
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
all_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_all_mins_UVI2_Around_STX_20250306.csv")
all_mins.to_csv(all_output_csv_path, index=False)
print(f"Saved all mins CSV to: {all_output_csv_path}")