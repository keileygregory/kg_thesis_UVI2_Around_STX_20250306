'''
This script renames high-frequency .wav files from naming convention "missionname_yyyymmdd_###_HF_yyyymmddhhmmss_microseconds.wav" to "missionname_###_HF_yyyymmdd_hhmmss.wav" (ex: UVI2_AroundSTX_20250306_001_HF_20250306190243_999000.wav -> UVI2_Around_STX_001_HF_20250306_190243.wav).

#ㅱ For ONLY this mission (UVI2_Around_STX_202050306), all acoustic files (wav2, wav3, log, xml, dtg) were accidentally named with mission name "AroundSTX" instead of "Around_STX" - this accident is corrected in the output renamed files

Input .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/sav_file_output
Output renamed .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/process_wav3

𖠺 Created by Keiley Gregory on March 17, 2026
Last updated on July 7, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
import os
import re
import shutil

#%% Set path to input and output folders
#𖠜 CHANGE FILE PATHS FOR CURRENT MISSION
input_directory = r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/sav_file_output"
output_directory = r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav3"

#%% Create empty list to store filenames of any files that failed renaming process (in order to print warning message at end of script)
failed = []

#%% 
#❥ Create regex defining each component of .wav file naming convention
PATTERN = re.compile(
    r"^(?P<glider>[^_]+)_"        # "UVI2" glider name
    r"(?P<mission>.+?)_"          # "AroundSTX" mission name (mission name accidentally missing underscore between Around and STX in input filenames)
    r"(?P<deployed>\d{8})_"       # "20250306" deployment date
    r"(?P<parentfile>\d{3})_"     # "001" sequential parent HF .wav file number
    r"(?P<freq>HF)_"              # "HF" high-frequency audio
    r"(?P<startdt>\d{14})_"       # "20250306190243" start datetime stamp of individual processed .wav file (*IMPORTANT! USED FOR DATETIMES OF DETECTIONS*)
    r"(?P<microsec>\d+)"          # "999000" microseconds for start datetime stamp
    r"\.wav$"                     # ".wav" file extension
)

#%%
#❥ FOR LOOP TO COPY + RENAME ONLY "_HF_" .WAV FILES FROM INPUT DIR TO OUTPUT DIR (input files left untouched)
for name in os.listdir(input_directory):

    # only process .wav files
    if not name.endswith(".wav"):
        continue
    # only process files with "_HF_" in the filename
    if "_HF_" not in name:
        continue

    #⋄ use regex pattern (defined above) to split .wav filenames into segments for renaming; if any files fail regex add to list for reporting
    match = PATTERN.match(name)
    if not match:
        failed.append(name)
        continue

    try:
        #⋄ select only desired segments
        glider     = match.group("glider")       # "UVI2"
        mission    = match.group("mission")      # "AroundSTX"
        parentfile = match.group("parentfile")   # "001"
        freq       = match.group("freq")         # "HF"
        startdt    = match.group("startdt")      # "20250306190243"
        #ㅱ input files use "AroundSTX" (no underscore); fix to "Around_STX" for output (see note at top for more info)
        if mission == "AroundSTX":
            mission = "Around_STX"
        # reformat startdt to split date and time with underscore (yyyymmddhhmmss -> yyyymmdd_hhmmss)
        startd_t = f"{startdt[:8]}_{startdt[8:]}"

        #⋄ build new naming convention
        new_name = f"{glider}_{mission}_{parentfile}_{freq}_{startd_t}.wav"
        # build full path to source file (input dir, untouched)
        old_path = os.path.join(input_directory, name)
        # build full path to renamed copy (output dir)
        new_path = os.path.join(output_directory, new_name)
        # copy file to output dir with NEW filename (input file is not modified or removed)
        shutil.copy2(old_path, new_path)

    # if any files that failed regex add to list for reporting
    except Exception:
        failed.append(name)

# Print list of any failed files (or success message if no failures)
if failed:
    print("Files NOT renamed:")
    for f in failed:
        print(f)
else:
    print("All files successfully renamed.")

###############################################################
# All files successfully renamed.
###############################################################