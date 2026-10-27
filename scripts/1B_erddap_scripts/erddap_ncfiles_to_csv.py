'''
This script reads .nc files (containing the ERDDAP glider flight and science data for mission) located in a directory and output the data as a .csv file.

Input .nc files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/1_data_raw/erddap_raw
Output .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/2_data_processed/erddap_processed

𖠺 Created by Keiley Gregory and Travis Hamlin on August 13, 2025
Last updated on March 11, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
import os
import glob
import pandas as pd
import xarray as xr

#%% Path to the folder containing all erddap .nc files for mission
#𖠜 CHANGE FOLDER PATH FOR CURRENT MISSION
nc_folder = "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/1_data_raw/erddap_raw"

# print list of all .nc files in the specified folder in alphabetical (chronological) order
nc_files = sorted(glob.glob(os.path.join(nc_folder, "*.nc")))
print(f"Found {len(nc_files)} files in {nc_folder}")
for f in nc_files:
    print(os.path.basename(f))

#%% Create empty lists to store variables present in each .nc file and append lists with variable names
file_vars = {}
all_vars = set()

for file in nc_files:
    ds = xr.open_dataset(file)
    vars_in_file = set(ds.variables.keys())
    file_vars[os.path.basename(file)] = vars_in_file
    all_vars.update(vars_in_file)
    ds.close()

#%% Print master list of all variables found in ALL .nc files (variables in print message sorted alphabetically, NOT in order of actual cols in .nc files)
print("\n" + "#" * 50)
print("ALL VARIABLES FOUND ACROSS ALL FILES")
print("#" * 50)
for var in sorted(all_vars):
    print(var)

#%% Print list of files that do NOT have all variables and the variables MISSING in each of those files
print("\n" + "#" * 50)
print("FILES WITH MISSING VARIABLES")
print("#" * 50)
for fname, vars_in_file in file_vars.items():
    missing = sorted(all_vars - vars_in_file)
    if missing:
        print(f"\n{fname} is missing these variables:")
        for var in missing:
            print(f"  {var}")

#❋ Select applicable variables for thesis
#%% List variables required to be present in each .nc file (aka the variables I need in output CSV)
required_vars = ['profile_id', 'time', 'profile_time', 'latitude', 'longitude', 'profile_lat', 'profile_lon', 'depth', 'temperature', 'salinity', 'oxygen_concentration']

#%% Mapping (aka renaming) variable names to match names used in subsequent interpolation script(s)
rename_map = {
    'profile_id': 'glider_profile_id',
    'time': 'datetime_UTC',
    'profile_time': 'profile_datetime_UTC',
    'latitude': 'latitude_DD',
    'longitude': 'longitude_DD',
    'profile_lat': 'profile_latitude_DD',
    'profile_lon': 'profile_longitude_DD',
    'depth': 'glider_depth_m',
    'temperature': 'water_temperature_C',
    'salinity': 'salinity_PSU',
    'oxygen_concentration': 'oxygen_concentration_μmol_L',
}

#%% Function to check if a variable or coordinate exists in dataset
def present_in_ds(ds, name):
    # return True if name is present as a variable or a coordinate
    return (name in ds.variables) or (name in ds.coords)


#❥ READ EACH .NC FILE AND EXTRACT DESIRED DATA INTO DATAFRAME (1 DF PER .NC FILE)
#%% Create list to store dataframes from each .nc file
dfs_list = []

#%% QC print message counters
expected_rows_total = 0
n_open_failed = 0
# store short error strings for end summary
error_msgs = []

#%% 
#✦ Loop through every .nc file, read and clean it, and add it to results
for nc_file in nc_files:
    # keep default decode for all variables (will convert datetime later)
    try:
        ds = xr.open_dataset(nc_file)

    # if opening fails, capture exception as 'e' and create one-row df placeholder so failure is recorded
    except Exception as e:
        # append QC print message counter and print warning message if any .nc files fail to open
        n_open_failed += 1
        msg = f"FAILED to open: {os.path.basename(nc_file)} | {type(e).__name__}: {e}"
        print(msg)
        error_msgs.append(msg)
        # still include a placeholder if .nc file cannot be opened
        placeholder = pd.DataFrame(
            {
                'glider_profile_id': [pd.NA],
                'glider_nc_file': [os.path.basename(nc_file)],
                'datetime_UTC': [pd.NaT],
                'profile_datetime_UTC': [pd.NaT],
                'latitude_DD': [pd.NA],
                'longitude_DD': [pd.NA],
                'profile_latitude_DD': [pd.NA], 
                'profile_longitude_DD': [pd.NA],
                'glider_depth_m': [pd.NA],
                'water_temperature_C': [pd.NA],
                'salinity_PSU': [pd.NA],
                'oxygen_concentration_μmol_L': [pd.NA],
                'error': [str(e)]
            }
        )
        dfs_list.append(placeholder)
        # track expected rows (placeholder counts as 1 in dfs_list)
        expected_rows_total += len(placeholder)
        continue

    # variables that exist in this file
    existing_vars = [var for var in required_vars if present_in_ds(ds, var)]

    # subset dataset to only vars that exist in ds
    ds_subset = ds[existing_vars]
    df = ds_subset.to_dataframe().reset_index()
    # rename columns (using renaming map created above)
    df = df.rename(columns=rename_map)
    # fill in any missing required columns (included in renaming map) with NA
    for var in rename_map.values():
        if var not in df.columns:
            df[var] = pd.NA
    
    # build datetime_UTC column (tz-aware UTC)
    if "datetime_UTC" in df.columns:
        df["datetime_UTC"] = pd.to_datetime(df["datetime_UTC"], errors="coerce", utc=True)
    # if somehow still have 'time' but not datetime_UTC (aka renaming map above didn't work correctly), create datetime_UTC from 'time'
    else:
        if "time" in df.columns:
            df["datetime_UTC"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
            df = df.drop(columns=["time"], errors="ignore")
        else:
            df["datetime_UTC"] = pd.NaT

    # build profile_datetime_UTC column (tz-aware UTC)
    if "profile_datetime_UTC" in df.columns:
        df["profile_datetime_UTC"] = pd.to_datetime(df["profile_datetime_UTC"], errors="coerce", utc=True)
    # if somehow still have 'profile_time' but not profile_datetime_UTC (aka renaming map above didn't work correctly), create profile_datetime_UTC from 'profile_time'
    else:
        if "profile_time" in df.columns:
            df["profile_datetime_UTC"] = pd.to_datetime(df["profile_time"], errors="coerce", utc=True)
            df = df.drop(columns=["profile_time"], errors="ignore")
        else:
            df["profile_datetime_UTC"] = pd.NaT
    
    # if any variables are missing, print warning message
    missing = [v for v in required_vars if not present_in_ds(ds, v)]
    if missing:
        print(f"⚠️ Missing thesis vars in {os.path.basename(nc_file)}: {missing}")

    # add source .nc filename for traceability
    df['glider_nc_file'] = os.path.basename(nc_file)
    # store df once
    dfs_list.append(df)
    expected_rows_total += len(df)
    # close dataset once
    ds.close()


#❥ CONCATENATE ALL NON-EMPTY DATAFRAMES (≥1 ROW HAS ≥1 VALID (NON-NA) VALUE) INTO SINGLE DATAFRAME, TIDY, AND EXPORT AS CSV
#%% Create empty list to store cleaned dfs
clean_dfs = []

#%% Loop through each item in original dfs_list [] (each item should be a dataframe)
for d in dfs_list:
    # if item is NOT a dataframe OR it has 0 rows, skip it and move on to next item in loop
    if not isinstance(d, pd.DataFrame) or d.empty:
        continue
    # keep df ONLY if there is at least one row with any non-NA value (drop rows that are entirely NA; if nothing is left (aka “all missing”), skip this df because contains no real data (only NA rows))
    if d.dropna(how="all").empty:
        continue
    clean_dfs.append(d)

#✦ Combine all dataframes into single dataframe
#%% If clean_dfs [] list is empty, print warning message (CANNOT write output .csv file)
if not clean_dfs:
    print("No valid files found — CSV not written.")
# if at least one valid df found, concatenate all valid dfs into one
else:
    # split into: (1) real data dfs and (2) placeholder/error dfs
    data_dfs = []
    error_dfs = []
    
    # if df has an error column with at least one non-missing value, treat it as an error/placeholder df; otherwise, treat it as a normal data df
    for d in clean_dfs:
        if "error" in d.columns and d["error"].notna().any():
            error_dfs.append(d)
        else:
            data_dfs.append(d)
    # build df_errors for inspection (even if empty)
    df_errors = pd.concat(error_dfs, ignore_index=True) if error_dfs else pd.DataFrame()
    # print summary of open failures (instead of saving errors CSV)
    if error_dfs:
        print(f"\n⚠️ {len(error_dfs)} file(s) failed to open (placeholders created).")
        for msg in error_msgs[:10]:
            print("  - " + msg)
        if len(error_msgs) > 10:
            print(f"  ... plus {len(error_msgs) - 10} more.")
    # if there is no real data, stop (but still keep df_errors available)
    if not data_dfs:
        print("No valid data rows found — CSV not written.")
        if not df_errors.empty:
            print(f"Error files captured: {len(df_errors)}")

    # concatenate ONLY real data (no error placeholders included)
    else:
        # remove per-file columns that are entirely NA (prevents FutureWarning about dtype inference)
        data_dfs_sanitized = []
        for d in data_dfs:
            # drop columns that are all-NA in this particular df
            d2 = d.dropna(axis=1, how="all")
            # if df is empty (has 0 rows), skip it
            if len(d2) == 0:
                continue
            data_dfs_sanitized.append(d2)
        data_dfs = data_dfs_sanitized
        df = pd.concat(data_dfs, ignore_index=True)

        # add 'mission_name' column with fixed value for every row (safety col for record-keeping)
        #𖠜 CHANGE MISSION NAME FOR CURRENT MISSION
        df['mission_name'] = 'UVI2_Around_STX_20250306'
        
        # fix glider depth (replace negative values with 0.000 to represent glider at surface)
        if "glider_depth_m" in df.columns:
            mask = pd.to_numeric(df["glider_depth_m"], errors="coerce") < 0
            df.loc[mask, "glider_depth_m"] = 0.000

        # enforce pandas datetime data type for datetime_UTC col (tz-aware UTC)
        df["datetime_UTC"] = pd.to_datetime(df["datetime_UTC"], errors="coerce", utc=True)
        # enforce pandas datetime data type for profile_datetime_UTC col (tz-aware UTC)
        df["profile_datetime_UTC"] = pd.to_datetime(df["profile_datetime_UTC"], errors="coerce", utc=True)

        # sort rows by datetime_UTC in ascending order
        df = df.sort_values(by="datetime_UTC", kind="mergesort")
        
        # QC print message for row-conservation check (exclude open-failure placeholders since not included in df)
        expected_real_rows = expected_rows_total - n_open_failed
        actual_rows = len(df)
        print(f"\nExpected real-data rows (sum of per-file dfs, excluding {n_open_failed} failed opens): {expected_real_rows}")
        print(f"Actual combined rows (after concat of real data only): {actual_rows}")
        if actual_rows != expected_real_rows:
            print(f"⚠️ ROW MISMATCH (expected - actual) = {expected_real_rows - actual_rows}")
        else:
            print("✅ Row conservation check passed.")
        # print (rows, columns) to confirm size of combined df
        print(f"Combined DataFrame shape: {df.shape}")

        # reorder columns
        df = df[
            [
                "mission_name",
                "glider_nc_file",
                "glider_profile_id",
                "datetime_UTC",
                "profile_datetime_UTC",
                "latitude_DD",
                "longitude_DD",
                "profile_latitude_DD",
                "profile_longitude_DD",
                "glider_depth_m",
                "water_temperature_C",
                "salinity_PSU",
                "oxygen_concentration_μmol_L"
            ]
        ]

        # export final df as CSV file
        #𖠜 CHANGE FILE PATH FOR CURRENT MISSION
        output_csv = "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/erddap_processed/erddap_UVI2_Around_STX_20250306.csv"
        df.to_csv(output_csv, index=False)
        print(f"CSV exported to: {output_csv}")


################################################################################
# ALL VARIABLES FOUND ACROSS ALL FILES
# ##################################################
# conductivity
# crs
# density
# depth
# glider_altitude
# instrument_dmon
# instrument_optode
# instrument_rbrctd
# latitude
# longitude
# m_pitch
# m_roll
# m_science_clothesline_lag
# optode_water_temperature
# oxy4_timestamp
# oxygen_concentration
# oxygen_saturation
# platform
# potential_temperature
# pressure
# profile_id
# profile_lat
# profile_lon
# profile_time
# salinity
# sci_m_present_time
# sci_oxy4_c1rph
# sci_oxy4_c2amp
# sci_oxy4_c2rph
# sci_oxy4_calphase
# sci_oxy4_is_installed
# sci_oxy4_rawtemp
# sci_oxy4_tcphase
# sci_software_ver
# sound_speed
# source_file
# temperature
# time
# trajectory
# water_depth

# ##################################################
# FILES WITH MISSING VARIABLES
# ##################################################
# missing these variables:

#   conductivity
#   optode_water_temperature
#   oxy4_timestamp
#   oxygen_concentration
#   oxygen_saturation
#   pressure
#   sci_oxy4_c1rph
#   sci_oxy4_c2amp
#   sci_oxy4_c2rph
#   sci_oxy4_calphase
#   sci_oxy4_is_installed
#   sci_oxy4_rawtemp
#   sci_oxy4_tcphase
#   sci_software_ver
#   temperature

# files missing variables:

# uvi_02_20250311T214809Z_dbd.nc
# uvi_02_20250311T223614Z_dbd.nc
# uvi_02_20250311T232324Z_dbd.nc
# uvi_02_20250312T001200Z_dbd.nc
# uvi_02_20250317T163947Z_dbd.nc
# uvi_02_20250317T171016Z_dbd.nc
# uvi_02_20250317T174014Z_dbd.nc
# uvi_02_20250317T181019Z_dbd.nc
# uvi_02_20250317T184129Z_dbd.nc
# uvi_02_20250317T191310Z_dbd.nc
# uvi_02_20250324T082449Z_dbd.nc
# uvi_02_20250324T083338Z_dbd.nc
################################################################################

################################################################################
# Expected real-data rows (sum of per-file dfs, excluding 0 failed opens): 1711713
# Actual combined rows (after concat of real data only): 1711713
# ✅ Row conservation check passed.
# Combined DataFrame shape: (1711713, 13)
#################################################################################