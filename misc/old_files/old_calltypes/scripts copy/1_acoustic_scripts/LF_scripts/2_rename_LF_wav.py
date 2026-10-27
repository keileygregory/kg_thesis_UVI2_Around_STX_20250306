'''
This script renames low-frequency .wav files from naming convention "missionname_yyyymmdd_###_LF_yyyymmddhhmmss_microseconds.wav" to "missionname_###_LF_yyyymmdd_hhmmss.wav" (ex: UVI2_TS_South_20250211_001_LF_20250211185746_004000.wav -> UVI2_TS_South_001_LF_20250211_185746.wav).

Input .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/process_wav2/wav2_IDL_output_NOclip
Output renamed .wav files directory = Same as input directory (*files renamed in-place)

𖠺 Created by Keiley Gregory on January 13, 2026
Last updated on January 19, 2026
'''

#ㅱ NOTE: For mission UVI2_Around_STX_202050306, all acoustic files (wav2, wav3, log, xml, dtg) were accidentally named with "AroundSTX" as the mission name instead of "Around_STX". Therefore, line 44 has the commented-out code that was used to manually fix the name for this specific mission - this will NOT apply to most missions.

#%%
import os
import re

#%% Set path to folder containing low-frequency .wav files that have ALDREADY BEEN PROCESSED BY .SAV FILE
directory = r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/process_wav2/wav2_IDL_output_NOclip"

#%% Create empty list to store filenames of any files that failed renaming process (in order to print warning message at end of script)
failed = []

#%% FOR LOOP to rename .wav files
for name in os.listdir(directory):
    # only process .wav files
    if not name.endswith(".wav"):
        continue

    try:
        # remove ".wav" extension from filename (name[:-4] (removes last 4 characters)) and split filename into sections by underscores (.split("_"))
        parts = name[:-4].split("_")

        # define individual sections of naming convention (python is zero-indexed, so first section is section #0)
        glider = parts[0]                    # "UVI2_" glider used during mission
        deployed = parts[-5]                 # "_20250211_" deployment date of mission
        parentfile = parts[-4]               # "_001_" sequential number of parent .wav2 file (and corresponding .log, .xml, and .dtg files)
        freq = parts[-3]                     # "_LF_" low-frequency audio
        startdt = parts[-2]                  # "_20250211185746_" start datetime stamp of individual processed .wav file (*IMPORTANT! USE FOR DATETIMES OF DETECTIONS)
        microsec = parts[-1]                 # "_004000" microseconds for start datetime stamp
        
        #ㅱ  AROUND_STX MISSION ONLY manually fix mission name (see note at top for more info)
        mission = "Around_STX"

        # reformat startdt section from yymmddhhmmss to yymmdd_hhmmss (i.e., "20250211185746" to "20250211_185746")
        startd_t = f"{startdt[:8]}_{startdt[8:]}"
        
        # build new naming convention
        new_name = f"{glider}_{mission}_{parentfile}_{freq}_{startd_t}.wav"

        # build full path to files with "old" (aka current) filenames
        old_path = os.path.join(directory, name)
        # build full path to files with new filenames
        new_path = os.path.join(directory, new_name)

        # rename files
        os.rename(old_path, new_path)

    # if renaming process fails, store filename of failed file in 'failed' list
    except Exception:
        failed.append(name)

#%% Print list of any failed filenames (or success message if no failures)
if failed:
    print("Files NOT renamed:")
    for f in failed:
        print(f)
else:
    print("All files successfully renamed.")