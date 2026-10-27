# This script creates a .csv file from the data contained in the .RData click events file exported by PAMGuard

# Input click events .RData file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname/data/2_data_processed/acoustic_processed/HF_processed/pamguard_exported_rdata
# Output .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/2_data_processed/acoustic_processed/HF_processed

# 𖠺 Created by Keiley Gregory on April 9, 2026
# Last updated on July 8, 2026

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


library(dplyr)

################################################################################
# PAMGUARD DATA                                                                 
################################################################################
# Import and read RData file exported from PAMGuard
#𖠜 CHANGE FILE PATH FOR MISSION
load("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/HF_processed/pamguard_exported_rdata/PAM_2025_03_06_140243_Tracked_Events.RData")
#𖠜 CHANGE NAME OF OBJECT BASED ON NAME IN IMPORTED FILE
events_obj <- det_20250306_140243_226_super_detection

# Create 1 row per each click event
event_to_row <- function(e) {
  fields <- lapply(names(e), function(nm) {
    val <- e[[nm]]
    if (is.list(val)) return(NA_character_)                # nested list -> NA
    if (length(val) == 0) return(NA_character_)            # empty -> NA
    if (length(val) > 1) return(paste(val, collapse=";"))  # vector -> joined
    as.character(val)
  })
  names(fields) <- names(e)
  as.data.frame(fields, stringsAsFactors=FALSE)
}

# Convert to dataframe and print summary details
df <- bind_rows(lapply(events_obj, event_to_row))
cat("Rows:", nrow(df), "\n")
cat("Columns:", paste(names(df), collapse=", "), "\n")

# Create start_datetime_UTC column that calculates UTC datetime (YYYY-MM-DD hh:mm:ss) from epoch date col
df$date_UTC <- format(
  as.POSIXct(as.numeric(df$date), origin = "1970-01-01", tz = "UTC"),
  "%Y-%m-%d %H:%M:%S"
)


################################################################################
# CORRECT START_DATETIME_UTC VALUES USING .WAV FILENAMES + CALCULATE END AND AV DATETIMES FROM START DATETIME
################################################################################
# Import CSV of all recorded high-frequency audio minutes (derived from .wav filenames in script 3_all_HF_mins_from_filenames.py)
#𖠜 CHANGE FILE PATH FOR MISSION
all_mins <- read.csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_all_mins_UVI2_Around_STX_20250306.csv")

# Parse datetimes in both dataframes to POSIXct
df$date_UTC_posix <- as.POSIXct(df$date_UTC, format = "%Y-%m-%d %H:%M:%S", tz = "UTC")
all_mins$av_datetime_UTC_posix <- as.POSIXct(
  sub("\\+00:00$", "", all_mins$av_datetime_UTC),
  format = "%Y-%m-%d %H:%M:%S", tz = "UTC"
)

# Match date_UTC col value in 'df' to NEAREST av_datetime_UTC value in 'all_mins' and create new av_datetime_UTC col in 'df' with matched value from 'all_mins'
match_idx <- sapply(df$date_UTC_posix, function(t) {
  which.min(abs(difftime(all_mins$av_datetime_UTC_posix, t, units = "secs")))
})
df$av_datetime_UTC <- all_mins$av_datetime_UTC_posix[match_idx]

# print warning of any rows where the nearest av_datetime_UTC found in 'all_mins' is ≥2 mins DIFFERENT from date_UTC in 'df'
diffs <- abs(difftime(df$av_datetime_UTC, df$date_UTC_posix, units = "secs"))
warn_rows <- which(diffs >= 120)
if (length(warn_rows) > 0) {
  warning(sprintf(
    "%d row(s) matched with difference ≥2 min:\n%s",
    length(warn_rows),
    paste(sprintf("  Row %d: date_UTC=%s, matched av_datetime_UTC=%s (diff=%.0f sec)",
                  warn_rows,
                  format(df$date_UTC_posix[warn_rows]),
                  format(df$av_datetime_UTC[warn_rows]),
                  as.numeric(diffs[warn_rows])), collapse = "\n")
  ))
}

# Add cols start_datetime_UTC and end_datetime_UTC with values calculated from av_datetime_UTC col (±30 sec around av_datetime_UTC) and format as YYYY-MM-DD hh:mm:ss+00:00
df$start_datetime_UTC <- format(df$av_datetime_UTC - 30, "%Y-%m-%d %H:%M:%S+00:00")
df$end_datetime_UTC   <- format(df$av_datetime_UTC + 30, "%Y-%m-%d %H:%M:%S+00:00")

# format av_datetime_UTC col as YYYY-MM-DD hh:mm:ss+00:00
df$av_datetime_UTC <- format(df$av_datetime_UTC, "%Y-%m-%d %H:%M:%S+00:00")

# Create new dataframe from 'df' with selected cols in specified order
click_events <- df[, c("channelMap", "UID", "event_type", "event_id", "nsubdet", "date", "date_UTC", "start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC", "comment")]

# rename cols
click_events <- click_events %>%
  rename(
    n_channels     = channelMap,
    color_code     = event_id,
    species_id     = event_type,
    event_n_clicks = nsubdet,
    pg_date_epoch  = date,
    pg_date_UTC    = date_UTC
  )

# Export as CSV
out_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/HF_processed/pamguard_HF_click_events_UVI2_Around_STX_20250306.csv"
write.csv(click_events, out_path, row.names=FALSE)
