'''
This script 
RENAMES high-frequency WAV files from naming convention "missionname_yyyymmdd_###_HF_yyyymmddhhmmss_milliseconds.wav" to "missionname_###_HF_yyyymmdd_hhmmss.wav" (ex: UVI2_AroundSTX_20250306_001_HF_20250306190243_999000.wav -> UVI2_Around_STX_001_HF_20250306_190243.wav) 
-- and --
SKIPS WRIITNG PARTIAL WAVs (<60 sec) data to renamed output WAVs (all final HF WAV files analyzed are exact 1-minute bins = differences in WAV duration do NOT affect probability of detection cetacean (shorter WAV duration = less data present in bin = lower probability of cetacean detections; i.e., less likely to see cetacean in 10-sec WAV than in full 60-sec WAV)
* All input files remain unchaged, all changes are written to new output WAV files

#ㅱ For ONLY this mission (UVI2_Around_STX_202050306), all acoustic files (wav2, wav3, log, xml, dtg) were accidentally named with mission name "AroundSTX" instead of "Around_STX" - this accident is corrected in the output renamed files

Input .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/sav_file_output
Output renamed .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/process_wav3

𖠺 Created by Keiley Gregory on March 17, 2026
Last updated on November 6, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
import os
import re
import shutil
import wave

#%% Set path to input and output folders
#𖠜 CHANGE FILE PATHS FOR CURRENT MISSION
input_directory = r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/sav_file_output"
output_directory = r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav3"
#⟡ safety catch (unlikely scenario): set path to "to_clip" subfolder inside output dir, where renamed files LONGER than MIN_SEC duration threshold are written instead of the normal output dir (folder is only created if any such files are found)
to_clip_directory = os.path.join(output_directory, "to_clip")

#%%
#༚ Set minimum duration (sec) a .wav file must have to be copied to output dir (files shorter than this are skipped)
MIN_SEC = 60

#%% Create 2 empty lists to store filenames of any files that failed regex renaming process or duration check (WAV header read)
failed_regex = []
failed_duration = []
# Create empty list to store filenames + durations of any files skipped for being shorter than MIN_SEC
skipped_short = []
# Create empty list to store filenames + durations of any files LONGER than MIN_SEC (still copied, but flagged with a warning because they need to be clipped)
long_files = []

#%% 
#❥ Create regex defining each component of .wav file naming convention
PATTERN = re.compile(
    r"^(?P<glider>[^_]+)_"        # "UVI2" glider name
    r"(?P<mission>.+?)_"          # "AroundSTX" mission name (mission name accidentally missing underscore between Around and STX in input filenames)
    r"(?P<deployed>\d{8})_"       # "20250306" deployment date
    r"(?P<parentfile>\d{3})_"     # "001" sequential parent HF .wav file number
    r"(?P<freq>HF)_"              # "HF" high-frequency audio
    r"(?P<startdt>\d{14})_"       # "20250306190243" start datetime stamp of individual processed .wav file (*IMPORTANT! USED FOR DATETIMES OF DETECTIONS*)
    r"(?P<microsec>\d+)"          # "999000" microiseconds for start datetime stamp
    r"\.wav$"                     # ".wav" file extension
)

#%%
#❥ RENAME OUTPUT WAV FILES + EXCLUDE INPUT WAVS <60 SEC FROM BEING WRITTEN TO OUTPUT WAV FILES
#❋ Copy + rename only "_HF_" WAV files from input dir to output dir (input files left untouched)
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
        failed_regex.append(name)
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

        #❋ EXTRACT INPUT WAV DURATION FROM HEADER METADATA -> ONLY WRITE DATA FROM FULL-DURATION (60 SEC) WAVs TO RENAMED OUTPUT WAVs = ALL OUTPUT WAVs IN FINAL DATASET ARE STANDARDIZED, EXACT 1-MINUTE BINS (in very unlikely scenario that input HF wav file has duration > 60 sec, output renamed *unclipped* wav to auto-created 'to_clip' subfolder inside 'process_wav3' - this avoids adding complex code required to split wav files into multiple 60-sec outputs like in LF clipping script since will almost never happen with HF)
        #༚ Open INPUT WAVs in READ-BINARY ('rb') mode + EXTRACT HEADER METADATA (digital audio data variables) using "wf.get...()" ('rb' mode = read-only, NO modification to source WAV files)
        with wave.open(old_path, "rb") as wf:
            # total n frames in source .wav file
            n_frames = wf.getnframes()
            # HF sample rate in Hz (samples/sec)
            framerate = wf.getframerate()
        #⋄ if input WAV file duration < set 'MIN_SEC' duration, SKIP WRITING to new renamed WAV file in 'output_directory' folder (no edits to or outputs created from the data in WAV files <60 sec) *compares whole frame counts instead of seconds to avoid decimal rounding issues
        if n_frames < framerate * MIN_SEC:
            # record filename + actual duration (sec) for reporting
            skipped_short.append((name, n_frames / framerate))
            continue
        #⋄ if input WAV file duration > set 'MIN_SEC' duration, write entire duration of input WAV file data into new renamed WAV file *UNCLIPPED* (treated exact same as input WAV files with duration exactly 60 sec, but renamed WAV files >60 sec long are written to NEW 'to_clip' SUBFOLDER created inside main 'process_wav3' output dir for renamed 60-sec WAV files)
        if n_frames > framerate * MIN_SEC:
            # record filename + actual duration (sec) for warning 
            long_files.append((name, n_frames / framerate))
            # create "to_clip" folder inside output dir if it doesn't already exist (does nothing if folder already exists)
            os.makedirs(to_clip_directory, exist_ok=True)
            # redirect renamed copy to "to_clip" folder instead of normal output dir
            new_path = os.path.join(to_clip_directory, new_name)

        #༚ copy/write data from input WAV file file to new renamed WAV file in output dir (input file remains unaltered, cannot be deleted/modified by this script)
        shutil.copy2(old_path, new_path)
    # if any files that failed regex add to list for reporting
    except Exception:
        failed_duration.append(name)

#❥ PRINT SUMMARY OF OUTPUT WAV FILES
#%% Print list of any files skipped for being shorter than MIN_SEC (with their durations)
if skipped_short:
    print(f"✘✘✘ SKIPPED ✘✘✘ PARTIAL <60s WAVs = {len(skipped_short)}")
    for f, dur in sorted(skipped_short):
        print(f"   ━▶🎙️ {f} ⏳ {dur:.3f} sec")

# Print warning for any files longer than MIN_SEC (with their durations) that were copied but need to be clipped
if long_files:
    print(f"\n⚠️ WARNING ⚠️ LONG >60s WAVs = {len(long_files)}")
    print(f"writes FULL AUDIO (UNCLIPPED) data --> new RENAMED WAV in 'to_clip' subfolder for further investigation/processing ")
    for f, dur in sorted(long_files):
        print(f"   ━▶🎙️ {f} ⏳ {dur:.3f} sec")

# Print warning for any failed files regex or duration check (or success message if no failures)
if failed_regex:
    print(f"\n🚨 REGEX FAILURE 🚨 FILENAME did NOT MATCH naming pattern, NO DATA written to RENAMED WAV = {len(failed_regex)}")
    for f in sorted(failed_regex):
        print(f"   ━▶✖️ {f}")

if failed_duration:
    print(f"\n🚨 DURATION CHECK FAILURE 🚨 WAV HEADER READ or COPY ERROR, NO DATA written to RENAMED WAV = {len(failed_duration)}")
    for f in sorted(failed_duration):
        print(f"   ━▶🔇 {f} ⏳ {dur:.3f} sec")

if not failed_regex and not failed_duration:
    print(f"\n✅ All FULL WAVs SUCCESSFULLY RENAMED")

#######################################################
# ✘✘✘ SKIPPED ✘✘✘ PARTIAL <60s WAVs = 2
#   ━▶🎙️ UVI2_AroundSTX_20250306_001_HF_20250306192744_004000.wav ⏳ 59.995 sec
#   ━▶🎙️ UVI2_AroundSTX_20250306_058_HF_20250325161244_000000.wav ⏳ 40.067 sec

# ✅ All FULL WAVs SUCCESSFULLY RENAMED
#######################################################