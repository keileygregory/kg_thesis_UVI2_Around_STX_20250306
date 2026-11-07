'''
This script takes low-frequency .wav files and splits them into exactly 60-second clips saved as new .wav files. Each new 60-sec .wav file has the start datetime of that specific audio clip in its filename.

Input .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/process_wav2/sav_LF_output_NOCLIP
Output clipped .wav files directory: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/*missionname*/process_wav2

𖠺 Created by Keiley Gregory on January 13, 2026
Last updated on January 19, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import wave
from datetime import datetime, timedelta

#%% Set paths to input and output directories
#𖠜 CHANGE FILE PATHS FOR CURRENT MISSION
INPUT_DIR  = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav2/sav_LF_output_NOCLIP")
OUTPUT_DIR = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav2")

#%%
#༚ Set duration of output audio clip .wav files
CLIP_SEC = 60                             

#%%
#𖠜 *TOGGLE SETTING* to include or exclude clips with duration < 60 sec (True = write partial clips)
WRITE_LAST_PARTIAL = False

#%% 
#༚ Get list of .wav files in input folder
parent_wavs = sorted([p for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".wav"])
# if no WAV files found, stop immediately and print warning
if not parent_wavs:
    raise SystemExit(f"No .wav files found in: {INPUT_DIR}")

#%% Create empty lists to store per-parent-file output summary + any potential failures
summary_rows = []     # list of tuples (parent_filename, n_clips_written)
failed_files = []     # list of tuples (parent_filename, error_message)


#%%
#❥ FOR LOOP to parse parent .wav filenames, read binary audio data from parent .wav files, and output 60-sec clips of LF audio data as new .wav files
for in_path in parent_wavs:
    try:

        #❋ PARSE PARENT .WAV FILENAME (expected pattern: "glider_mission_parentfile_freq_startdate_starttime.wav", ex: "UVI2_Around_STX_001_LF_20250306_195743.wav")
        # extract parent .wav filename without .wav file extension
        stem = in_path.stem
        # split into chunks separated by underscores (.split("_"))
        parts = stem.split("_")
        
        # ensure parent .wav filename matches expected pattern
        if len(parts) < 6:
            raise ValueError(f"Bad filename pattern: {in_path.name}")

        # define chunks of parent filename pattern
        glider = parts[0]                     # "UVI2_"
        mission = "_".join(parts[1:-4])       # "_Around_STX_"
        parentfile = parts[-4]                # "_001_"
        freq = parts[-3]                      # "LF"
        startdate = parts[-2]                 # "_20250306_" (YYYYMMDD)
        starttime = parts[-1]                 # "_195743" (hhmmss)

        # parse start datetime from filename (UTC so NO timezone conversion)
        parent_start_dt = datetime.strptime(startdate + starttime, "%Y%m%d%H%M%S")

        #❋ OPEN PARENT .WAV FILE in read-binary ('rb') mode and extract header metadata (digital audio data variables) using "wf.get...()"
        with wave.open(str(in_path), "rb") as wf:
            n_channels = wf.getnchannels()    # 1 (mono channel)
            sampwidth = wf.getsampwidth()     # BYTES (not bits) per sample (1 byte = 8 bits); sampwidth = 16-bit depth ÷ 8 = 2 bytes/sample
            framerate = wf.getframerate()     # LF sample rate in Hz (2000 Hz = 2000 samples/sec)
            n_frames = wf.getnframes()        # total n frames in parent .wav file (being read in current loop interation)
            comptype = wf.getcomptype()       # compression type of audio data ("NONE" = PCM)

            #✧ ensure audio is uncompressed PCM (required for python wave module to work safely)
            if comptype != "NONE":
                raise ValueError(f"Not PCM/uncompressed WAV (comptype={comptype}).")

            #✧ Set the number of frames for each output *60 SEC* clip .wav file to include (desired duration aka amount of data in each output clip)
            frames_per_clip = framerate * CLIP_SEC

            #✧ FRAMES in python are always ZERO-INDEXED (if first 60 sec clip in parent .wav file contains n_frames = 120000 then clip's start index is frame_cursor = 0 (since first clip in parent wav file) and end index end_frame = 119999 ⥤ the following clip in same parent .wav file has start index frame_cursor = 120000)
            # set frame index for clip to start reading from (frame_cursor) to 0 at start of each new parent .wav file
            frame_cursor = 0
            # count n clips written so far from current parent .wav file (NOT used in any calculations, just for recordkeeping)
            clip_count = 0

            #✧ SPLIT AUDIO INTO 60 SEC CLIPS by looping through each 60 sec clip in parent .wav file UNTIL frame_cursor ≥ n_frames, which occurs when there are NO more unread frames remaining in parent .wav file (frame_cursor = frame index to start reading data for clip at; n_frames = total n frames in parent .wav file (from .getnframes())
            while frame_cursor < n_frames:
                # n unread frames remaining in parent .wav file
                remaining = n_frames - frame_cursor
                # determine the number of frames to include in current output clip (frames_per_clip = n frames required for a full 60 sec clip; remaining = total unread frames left in parent .wav file); creates FULL 60 sec clip ONLY IF there are AT LEAST n = {frames_per_clip} unread frames remaining in parent file -or- creates PARTIAL (<60 sec) clip IF LESS than n = {frames_per_clip} unread frames remaining in parent file
                this_clip_frames = min(frames_per_clip, remaining)

                #⋄ ONLY keep FULL audio clips with duration ≥ 60 sec (toggle ON/OFF in line 19)
                if this_clip_frames < frames_per_clip and not WRITE_LAST_PARTIAL:
                    break

                # clip start OFFSET (sec) from start datetime of parent .wav file (for all clips in file AFTER first clip, which has same start datetime as parent)
                clip_offset_sec = frame_cursor / framerate
                # calculate true clip start datetime from parent start datetime + offset (sec)
                clip_start_dt = parent_start_dt + timedelta(seconds=clip_offset_sec)

                # format clip datetime back into strings for filename parts
                clip_startdate = clip_start_dt.strftime("%Y%m%d")
                clip_starttime = clip_start_dt.strftime("%H%M%S")

                # build filename for output clip .wav file
                out_name = f"{glider}_{mission}_{parentfile}_{freq}_{clip_startdate}_{clip_starttime}.wav"
                out_path = OUTPUT_DIR / out_name

                #⋄ READ ACTUAL AUDIO FRAMES for output clip (from parent .wav file) and return raw bytes object (essentially a blob of raw PCM) that countains ALL AUDIO DATA (NOT just header metadata or frame counts) for every frame included in output clip file
                # set frame index (within parent .wav file) where audio data for current clip should start being read at; set as the value of 'frame_cursor' (= total n frames in all previous clips already read in parent file)
                wf.setpos(frame_cursor)
                # .readframes() reads actual audio data (not just header metadata) from parent .wav file and returns RAW BYTES OBJECT representing the cumulative size of all frames read for current individual clip
                audio_bytes = wf.readframes(this_clip_frames)

                #⋄ WRITE OUTPUT CLIP (using write-binary ('wb') mode) as new .wav file (set header metadata for output clip using values from parent .wav file header, write actual audio data for clip using subset of audio data read from parent .wav file and stored as a raw bytes object)
                with wave.open(str(out_path), "wb") as out_wf:
                    out_wf.setnchannels(n_channels)           # set equal to parent .wav file
                    out_wf.setsampwidth(sampwidth)            # set equal to parent .wav file
                    out_wf.setframerate(framerate)            # set equal to parent .wav file
                    out_wf.writeframes(audio_bytes)           # write audio from data stored as raw bytes object

                # advance frame_cursor index and increment clip counter in preparation for reading the following clip from parent .wav file in next iteration of loop
                frame_cursor += this_clip_frames
                clip_count += 1

        # append empty summary/failure lists with the results of the FOR loop output for the individual parent .wav file
        summary_rows.append((in_path.name, clip_count)) # loop suceeded for parent wav file
    except Exception as e:
        failed_files.append((in_path.name, str(e)))     # loop failed for parent wav file


#%% 
#༚ Detailed print message of code output
total_parents = len(parent_wavs)
n_success = len(summary_rows)
n_failed = len(failed_files)
total_clips = sum(n for _, n in summary_rows)

lines = []

lines.append("===================== 𖠺 WAV SPLIT SUMMARY 𖠺 =====================")
lines.append(f"Input folder : {INPUT_DIR}")
lines.append(f"Output folder: {OUTPUT_DIR}")
lines.append(f"Clip length  : {CLIP_SEC} sec")
lines.append(f"Write partial last clip (<{CLIP_SEC}s): {WRITE_LAST_PARTIAL}")
lines.append("")
lines.append(f"Parent WAV files found : {total_parents}")
lines.append(f"Successfully processed : {n_success}")
lines.append(f"Failed                : {n_failed}")
lines.append(f"Total clips written   : {total_clips}")
lines.append("")
lines.append("Per-file clip counts:")
for fname, n in summary_rows:
    lines.append(f"  - {fname} -> {n} clips")
if failed_files:
    lines.append("")
    lines.append("Failures:")
    for fname, err in failed_files:
        lines.append(f"  - {fname}: {err}")
lines.append("========================== 𐃍 ==========================")

print("\n".join(lines))


##########################################################################################################
# ===================== 𖠺 WAV SPLIT SUMMARY 𖠺 =====================
# Input folder : /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav2/sav_LF_output_NOCLIP
# Output folder: /Users/keileygregory/THESIS_REPOSITORIES/AUDIO_PROCESSING/UVI2_Around_STX_20250306/process_wav2
# Clip length  : 60 sec
# Write partial last clip (<60s): False

# Parent WAV files found : 454
# Successfully processed : 454
# Failed                : 0
# Total clips written   : 27194

# Per-file clip counts:
#   - UVI2_Around_STX_001_LF_20250306_185746.wav -> 59 clips
#   - UVI2_Around_STX_001_LF_20250306_195743.wav -> 60 clips
#   - UVI2_Around_STX_001_LF_20250306_205743.wav -> 60 clips
#   - UVI2_Around_STX_001_LF_20250306_215743.wav -> 60 clips
#   - UVI2_Around_STX_001_LF_20250306_225743.wav -> 60 clips
#   - UVI2_Around_STX_001_LF_20250306_235743.wav -> 60 clips
#   - UVI2_Around_STX_001_LF_20250307_005743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_015743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_025743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_035743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_045743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_055743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_065743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_075743.wav -> 60 clips
#   - UVI2_Around_STX_002_LF_20250307_085743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_095743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_105743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_115743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_125743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_135743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_145743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_155743.wav -> 60 clips
#   - UVI2_Around_STX_003_LF_20250307_165743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_175743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_185743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_195743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_205743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_215743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_225743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250307_235743.wav -> 60 clips
#   - UVI2_Around_STX_004_LF_20250308_005743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_015743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_025743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_035743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_045743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_055743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_065743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_075743.wav -> 60 clips
#   - UVI2_Around_STX_005_LF_20250308_085743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_095743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_105743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_115743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_125743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_135743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_145743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_155743.wav -> 60 clips
#   - UVI2_Around_STX_006_LF_20250308_165743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_175743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_185743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_195743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_205743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_215743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_225743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250308_235743.wav -> 60 clips
#   - UVI2_Around_STX_007_LF_20250309_005743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_015743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_025743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_035743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_045743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_055743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_065743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_075743.wav -> 60 clips
#   - UVI2_Around_STX_008_LF_20250309_085743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_095743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_105743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_115743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_125743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_135743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_145743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_155743.wav -> 60 clips
#   - UVI2_Around_STX_009_LF_20250309_165743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_175743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_185743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_195743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_205743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_215743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_225743.wav -> 60 clips
#   - UVI2_Around_STX_010_LF_20250309_235743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_005743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_015743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_025743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_035743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_045743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_055743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_065743.wav -> 60 clips
#   - UVI2_Around_STX_011_LF_20250310_075743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_085743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_095743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_105743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_115743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_125743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_135743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_145743.wav -> 60 clips
#   - UVI2_Around_STX_012_LF_20250310_155743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_165743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_175743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_185743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_195743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_205743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_215743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_225743.wav -> 60 clips
#   - UVI2_Around_STX_013_LF_20250310_235743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_005743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_015743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_025743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_035743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_045743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_055743.wav -> 60 clips
#   - UVI2_Around_STX_014_LF_20250311_065743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_075743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_085743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_095743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_105743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_115743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_125743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_135743.wav -> 60 clips
#   - UVI2_Around_STX_015_LF_20250311_145743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_155743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_165743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_175743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_185743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_195743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_205743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_215743.wav -> 60 clips
#   - UVI2_Around_STX_016_LF_20250311_225743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250311_235743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_005743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_015743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_025743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_035743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_045743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_055743.wav -> 60 clips
#   - UVI2_Around_STX_017_LF_20250312_065743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_075743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_085743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_095743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_105743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_115743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_125743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_135743.wav -> 60 clips
#   - UVI2_Around_STX_018_LF_20250312_145743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_155743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_165743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_175743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_185743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_195743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_205743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_215743.wav -> 60 clips
#   - UVI2_Around_STX_019_LF_20250312_225743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250312_235743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_005743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_015743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_025743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_035743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_045743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_055743.wav -> 60 clips
#   - UVI2_Around_STX_020_LF_20250313_065743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_075743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_085743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_095743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_105743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_115743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_125743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_135743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_145743.wav -> 60 clips
#   - UVI2_Around_STX_021_LF_20250313_155743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_165743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_175743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_185743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_195743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_205743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_215743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_225743.wav -> 60 clips
#   - UVI2_Around_STX_022_LF_20250313_235743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_005743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_015743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_025743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_035743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_045743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_055743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_065743.wav -> 60 clips
#   - UVI2_Around_STX_023_LF_20250314_075743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_085743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_095743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_105743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_115743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_125743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_135743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_145743.wav -> 60 clips
#   - UVI2_Around_STX_024_LF_20250314_155743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_165743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_175743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_185743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_195743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_205743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_215743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_225743.wav -> 60 clips
#   - UVI2_Around_STX_025_LF_20250314_235743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_005743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_015743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_025743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_035743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_045743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_055743.wav -> 60 clips
#   - UVI2_Around_STX_026_LF_20250315_065743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_075743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_085743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_095743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_105743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_115743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_125743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_135743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_145743.wav -> 60 clips
#   - UVI2_Around_STX_027_LF_20250315_155743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_165743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_175743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_185743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_195743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_205743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_215743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_225743.wav -> 60 clips
#   - UVI2_Around_STX_028_LF_20250315_235743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_005743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_015743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_025743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_035743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_045743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_055743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_065743.wav -> 60 clips
#   - UVI2_Around_STX_029_LF_20250316_075743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_085743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_095743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_105743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_115743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_125743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_135743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_145743.wav -> 60 clips
#   - UVI2_Around_STX_030_LF_20250316_155743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_165743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_175743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_185743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_195743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_205743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_215743.wav -> 60 clips
#   - UVI2_Around_STX_031_LF_20250316_225743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250316_235743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_005743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_015743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_025743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_035743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_045743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_055743.wav -> 60 clips
#   - UVI2_Around_STX_032_LF_20250317_065743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_075743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_085743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_095743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_105743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_115743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_125743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_135743.wav -> 60 clips
#   - UVI2_Around_STX_033_LF_20250317_145743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_155743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_165743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_175743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_185743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_195743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_205743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_215743.wav -> 60 clips
#   - UVI2_Around_STX_034_LF_20250317_225743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250317_235743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_005743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_015743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_025743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_035743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_045743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_055743.wav -> 60 clips
#   - UVI2_Around_STX_035_LF_20250318_065743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_075743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_085743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_095743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_105743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_115743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_125743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_135743.wav -> 60 clips
#   - UVI2_Around_STX_036_LF_20250318_145743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_155743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_165743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_175743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_185743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_195743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_205743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_215743.wav -> 60 clips
#   - UVI2_Around_STX_037_LF_20250318_225743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250318_235743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_005743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_015743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_025743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_035743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_045743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_055743.wav -> 60 clips
#   - UVI2_Around_STX_038_LF_20250319_065743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_075743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_085743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_095743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_105743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_115743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_125743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_135743.wav -> 60 clips
#   - UVI2_Around_STX_039_LF_20250319_145743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_155743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_165743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_175743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_185743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_195743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_205743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_215743.wav -> 60 clips
#   - UVI2_Around_STX_040_LF_20250319_225743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250319_235743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_005743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_015743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_025743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_035743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_045743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_055743.wav -> 60 clips
#   - UVI2_Around_STX_041_LF_20250320_065743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_075743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_085743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_095743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_105743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_115743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_125743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_135743.wav -> 60 clips
#   - UVI2_Around_STX_042_LF_20250320_145743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_155743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_165743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_175743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_185743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_195743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_205743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_215743.wav -> 60 clips
#   - UVI2_Around_STX_043_LF_20250320_225743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250320_235743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_005743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_015743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_025743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_035743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_045743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_055743.wav -> 60 clips
#   - UVI2_Around_STX_044_LF_20250321_065743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_075743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_085743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_095743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_105743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_115743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_125743.wav -> 60 clips
#   - UVI2_Around_STX_045_LF_20250321_135743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_145743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_155743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_165743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_175743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_185743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_195743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_205743.wav -> 60 clips
#   - UVI2_Around_STX_046_LF_20250321_215743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250321_225743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250321_235743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250322_005743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250322_015743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250322_025743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250322_035743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250322_045743.wav -> 60 clips
#   - UVI2_Around_STX_047_LF_20250322_055743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_065743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_075743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_085743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_095743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_105743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_115743.wav -> 60 clips
#   - UVI2_Around_STX_048_LF_20250322_125743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_135743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_145743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_155743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_165743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_175743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_185743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_195743.wav -> 60 clips
#   - UVI2_Around_STX_049_LF_20250322_205743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250322_215743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250322_225743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250322_235743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250323_005743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250323_015743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250323_025743.wav -> 60 clips
#   - UVI2_Around_STX_050_LF_20250323_035743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_045743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_055743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_065743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_075743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_085743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_095743.wav -> 60 clips
#   - UVI2_Around_STX_051_LF_20250323_105743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_115743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_125743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_135743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_145743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_155743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_165743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_175743.wav -> 60 clips
#   - UVI2_Around_STX_052_LF_20250323_185743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250323_195743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250323_205743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250323_215743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250323_225743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250323_235743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250324_005743.wav -> 60 clips
#   - UVI2_Around_STX_053_LF_20250324_015743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_025743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_035743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_045743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_055743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_065743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_075743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_085743.wav -> 60 clips
#   - UVI2_Around_STX_054_LF_20250324_095743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_105743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_115743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_125743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_135743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_145743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_155743.wav -> 60 clips
#   - UVI2_Around_STX_055_LF_20250324_165743.wav -> 60 clips
#   - UVI2_Around_STX_056_LF_20250324_175743.wav -> 60 clips
#   - UVI2_Around_STX_056_LF_20250324_185743.wav -> 60 clips
#   - UVI2_Around_STX_056_LF_20250324_195743.wav -> 60 clips
#   - UVI2_Around_STX_056_LF_20250324_205743.wav -> 60 clips
#   - UVI2_Around_STX_056_LF_20250324_215743.wav -> 60 clips
#   - UVI2_Around_STX_056_LF_20250324_225743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250324_235743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_005743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_015743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_025743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_035743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_045743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_055743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_065743.wav -> 60 clips
#   - UVI2_Around_STX_057_LF_20250325_075743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_085743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_095743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_105743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_115743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_125743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_135743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_145743.wav -> 60 clips
#   - UVI2_Around_STX_058_LF_20250325_155743.wav -> 15 clips
# ========================== 𐃍 ==========================
##########################################################################################################