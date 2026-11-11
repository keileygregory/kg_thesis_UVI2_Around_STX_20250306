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
# Create empty list to store (parent file ID, renamed filename) of every exact 60-sec WAV written to output dir (used for per-parent-file clip counts in summary)
written_files = []

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
        # record parent file ID (ex: "UVI2_Around_STX_001_HF") for exact 60-sec WAVs written to main output dir (files sent to "to_clip" are reported separately)
        if n_frames == framerate * MIN_SEC:
            written_files.append((f"{glider}_{mission}_{parentfile}_{freq}", new_name))
    # if any files that failed regex add to list for reporting
    except Exception:
        failed_duration.append(name)

#❥ PRINT SUMMARY OF OUTPUT WAV FILES
#%%
#༚  Count n output renamed 60-sec WAVs written per parent HF .wav file number
per_parent_counts = {}
for parent_id, _ in written_files:
    per_parent_counts[parent_id] = per_parent_counts.get(parent_id, 0) + 1

#%%
#༚ Calculate totals for each outcome category (successfully written renamed 60-sec wav files, long files >60 sec written renamed but upclipped to 'to_clip' subfolder, partial <60 sec files not written, files that failed regex or duration extraction)
n_written = len(written_files)
n_long = len(long_files)
n_short = len(skipped_short)
n_failed_regex = len(failed_regex)
n_failed_duration = len(failed_duration)
# total "_HF_" .wav files found in input dir (sum of every outcome category)
total_inputs = n_written + n_long + n_short + n_failed_regex + n_failed_duration

#%%
#༚ Print summary of directory of counts of WAV files
lines = []
lines.append("───────────────────── 🎤︎︎ HF WAV RENAME + 1-MIN BIN SUMMARY 🎤︎︎ ─────────────────────")
# Background info (input and output directories, min WAV file length setting)
lines.append(f"Input folder: {input_directory}")
lines.append(f"Output folder: {output_directory}")
lines.append(f"Clip length = {MIN_SEC} sec")
lines.append("──────────────────────────────────────── 🎤︎︎ ────────────────────────────────────────")
# Counts of files in each category (input, output, partial, long, failed)
lines.append(f"📁 Input HF WAV files found in '{input_directory}' 🟰 {total_inputs}")
lines.append(f"✅ Output {MIN_SEC}-sec renamed WAV files written to '{output_directory}' 🟰 {n_written}")
lines.append(f"🚫 Skipped partial (<{MIN_SEC} sec) WAV files NOT written 🟰 {n_short}")
lines.append(f"⏰ Long (>{MIN_SEC} sec) renamed but NOT clipped WAV files written to '{to_clip_directory}' 🟰 {n_long}")
lines.append(f"❌ Failed regex 🟰 {n_failed_regex}")
lines.append(f"❌ Failed header read/copy 🟰 {n_failed_duration}")
lines.append("──────────────────────────────────────── 🎤︎︎ ────────────────────────────────────────")
#༚ Print filenames (+ durations) of partial (skipped) and long (written to 'to_clip') WAV files
if skipped_short:
    lines.append(f"🚫 PARTIAL (<{MIN_SEC} sec) WAV FILES SKIPPED:")
    for f, dur in sorted(skipped_short):
        lines.append(f"   𐃘🎙️ {f} ⏳ {dur:.6f} sec")
if long_files:
    lines.append("")
    lines.append(f"⏰ LONG (>{MIN_SEC} sec) WAV FILES WRITTEN TO 'TO_CLIP' SUBFOLDER (ㅱRENAMED ㅱUNCLIPPED):")
    for f, dur in sorted(long_files):
        lines.append(f"   𐃘🎙️ {f} ⏳ {dur:.6f} sec")
#༚ Print warning for any failed files regex or duration check (or success message if no failures)
if failed_regex:
    lines.append("")
    lines.append(f"❌ REGEX FAILURE WAV FILES SKIPPED:")
    for f in sorted(failed_regex):
        lines.append(f"   𐃘🎙️ {f}")
if failed_duration:
    lines.append("")
    lines.append(f"❌ DURATION CHECK FAILURE (WAV HEADER READ/COPY ERROR):")
    for f in sorted(failed_duration):
        lines.append(f"   𐃘🎙️ {f}")
if not failed_regex and not failed_duration:
    lines.append("")
    lines.append("✔️ No regex or duration check failures")
lines.append("──────────────────────────────────────── 🎤︎︎ ────────────────────────────────────────")
#༚ Number of output renamed 60-sec WAV files written from each SET of input parent WAV files that share a raw parent dtg file (i.e., count of 'process_wav3' files written from ALL un-concatenated HF wav files originating from UVI2_Around_STX_001.dtg combined)
# count input HF wav files in 'sav_file_output' per parent file ID (uses same regex + "AroundSTX" -> "Around_STX" fix as above so IDs match the output counts)
per_parent_input_counts = {}
for name in os.listdir(input_directory):
    # only count .wav files with "_HF_" in filename (same filter as main loop)
    if not name.endswith(".wav") or "_HF_" not in name:
        continue
    # split filename with regex (skip files that fail regex since already reported in failed_regex list)
    match = PATTERN.match(name)
    if not match:
        continue
    # fix mission name so parent ID matches output naming
    mission = match.group("mission")
    if mission == "AroundSTX":
        mission = "Around_STX"
    # build parent file ID (ex: "UVI2_Around_STX_001_HF") and add 1 to its input count
    parent_id = f"{match.group('glider')}_{mission}_{match.group('parentfile')}"
    per_parent_input_counts[parent_id] = per_parent_input_counts.get(parent_id, 0) + 1
#⋄ Print parent ID# (from dtg) -> n input wavs in 'sav_file_output' with that parent ID# -> n renamed 60s wavs written to 'process_wav3' with that parent ID#
lines.append("source dtg file number  ─𓉘𑂘ᥲ꣗ 𑂘ɕ𐑾ꪱթȶ𓉝─▷  sav_file_output  ─𓉘ȶᏂι̊꯱ թꪗ𓉝─▷  process_wav3 (renamed, 60 sec)")
for parent_id in sorted(per_parent_input_counts):
    lines.append(f" 𑑛 {parent_id}     ───────▶     {per_parent_input_counts[parent_id]} wav files     ───────▶     {per_parent_counts.get(f'{parent_id}_HF', 0)} wav files")
lines.append("────────────────────────────────────────────────────────────────────────────────────")

#%% Print message and start each new "lines.append(f"...")" print message as a separate line
print("\n".join(lines))




# ───────────────────── 🎤︎︎ HF WAV RENAME + 1-MIN BIN SUMMARY 🎤︎︎ ─────────────────────
# Input folder: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/sav_file_output
# Output folder: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav3
# Clip length = 60 sec
# ──────────────────────────────────────── 🎤︎︎ ────────────────────────────────────────
# 📁 Input HF WAV files found in '/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/sav_file_output' 🟰 5439
# ✅ Output 60-sec renamed WAV files written to '/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav3' 🟰 5437
# 🚫 Skipped partial (<60 sec) WAV files NOT written 🟰 2
# ⏰ Long (>60 sec) renamed but NOT clipped WAV files written to '/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav3/to_clip' 🟰 0
# ❌ Failed regex 🟰 0
# ❌ Failed header read/copy 🟰 0
# ──────────────────────────────────────── 🎤︎︎ ────────────────────────────────────────
# 🚫 PARTIAL (<60 sec) WAV FILES SKIPPED:
#    𐃘🎙️ UVI2_AroundSTX_20250306_001_HF_20250306192744_004000.wav ⏳ 59.995833 sec
#    𐃘🎙️ UVI2_AroundSTX_20250306_058_HF_20250325161244_000000.wav ⏳ 40.067100 sec

# ✔️ No regex or duration check failures
# ──────────────────────────────────────── 🎤︎︎ ────────────────────────────────────────
# source dtg file number  ─𓉘𑂘ᥲ꣗ 𑂘ɕ𐑾ꪱթȶ𓉝─▷  sav_file_output  ─𓉘ȶᏂι̊꯱ թꪗ𓉝─▷  process_wav3 (renamed, 60 sec)
#  𑑛 UVI2_Around_STX_001     ───────▶     92 wav files     ───────▶     91 wav files
#  𑑛 UVI2_Around_STX_002     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_003     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_004     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_005     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_006     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_007     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_008     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_009     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_010     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_011     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_012     ───────▶     92 wav files     ───────▶     92 wav files
#  𑑛 UVI2_Around_STX_013     ───────▶     93 wav files     ───────▶     93 wav files
#  𑑛 UVI2_Around_STX_014     ───────▶     91 wav files     ───────▶     91 wav files
#  𑑛 UVI2_Around_STX_015     ───────▶     93 wav files     ───────▶     93 wav files
#  𑑛 UVI2_Around_STX_016     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_017     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_018     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_019     ───────▶     100 wav files    ───────▶     100 wav files
#  𑑛 UVI2_Around_STX_020     ───────▶     99 wav files     ───────▶     99 wav files
#  𑑛 UVI2_Around_STX_021     ───────▶     99 wav files     ───────▶     99 wav files
#  𑑛 UVI2_Around_STX_022     ───────▶     101 wav files    ───────▶     101 wav files
#  𑑛 UVI2_Around_STX_023     ───────▶     92 wav files     ───────▶     92 wav files
#  𑑛 UVI2_Around_STX_024     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_025     ───────▶     93 wav files     ───────▶     93 wav files
#  𑑛 UVI2_Around_STX_026     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_027     ───────▶     97 wav files     ───────▶     97 wav files
#  𑑛 UVI2_Around_STX_028     ───────▶     99 wav files     ───────▶     99 wav files
#  𑑛 UVI2_Around_STX_029     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_030     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_031     ───────▶     88 wav files     ───────▶     88 wav files
#  𑑛 UVI2_Around_STX_032     ───────▶     93 wav files     ───────▶     93 wav files
#  𑑛 UVI2_Around_STX_033     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_034     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_035     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_036     ───────▶     98 wav files     ───────▶     98 wav files
#  𑑛 UVI2_Around_STX_037     ───────▶     97 wav files     ───────▶     97 wav files
#  𑑛 UVI2_Around_STX_038     ───────▶     99 wav files     ───────▶     99 wav files
#  𑑛 UVI2_Around_STX_039     ───────▶     98 wav files     ───────▶     98 wav files
#  𑑛 UVI2_Around_STX_040     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_041     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_042     ───────▶     96 wav files     ───────▶     96 wav files
#  𑑛 UVI2_Around_STX_043     ───────▶     95 wav files     ───────▶     95 wav files
#  𑑛 UVI2_Around_STX_044     ───────▶     93 wav files     ───────▶     93 wav files
#  𑑛 UVI2_Around_STX_045     ───────▶     93 wav files     ───────▶     93 wav files
#  𑑛 UVI2_Around_STX_046     ───────▶     92 wav files     ───────▶     92 wav files
#  𑑛 UVI2_Around_STX_047     ───────▶     91 wav files     ───────▶     91 wav files
#  𑑛 UVI2_Around_STX_048     ───────▶     94 wav files     ───────▶     94 wav files
#  𑑛 UVI2_Around_STX_049     ───────▶     88 wav files     ───────▶     88 wav files
#  𑑛 UVI2_Around_STX_050     ───────▶     87 wav files     ───────▶     87 wav files
#  𑑛 UVI2_Around_STX_051     ───────▶     87 wav files     ───────▶     87 wav files
#  𑑛 UVI2_Around_STX_052     ───────▶     89 wav files     ───────▶     89 wav files
#  𑑛 UVI2_Around_STX_053     ───────▶     88 wav files     ───────▶     88 wav files
#  𑑛 UVI2_Around_STX_054     ───────▶     91 wav files     ───────▶     91 wav files
#  𑑛 UVI2_Around_STX_055     ───────▶     85 wav files     ───────▶     85 wav files
#  𑑛 UVI2_Around_STX_056     ───────▶     74 wav files     ───────▶     74 wav files
#  𑑛 UVI2_Around_STX_057     ───────▶     114 wav files    ───────▶     114 wav files
#  𑑛 UVI2_Around_STX_058     ───────▶     79 wav files     ───────▶     78 wav files
# ────────────────────────────────────────────────────────────────────────────────────