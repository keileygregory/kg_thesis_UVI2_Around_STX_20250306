'''
This script tidies (renames columns, fixes data type/numeric formats) the 'calc_sperm_points_p26920.csv' file output by ArcGIS Pro for sperm detections.

Input .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/missionname/data/5_data_gis/HF_gis_data
Output (tidy) .csv file directory: Same as input

𖠺 Created by Keiley Gregory on March 10, 2026
Last updated on September 29, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd

#%% Load raw ArcGIS output CSV file
#𖠜 UPDATE FILE PATH FOR MISSION
input_csv = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/calc_sperm_points_p26920.csv")
df = pd.read_csv(input_csv)   

#❥ SET ALL VALUES IN glider_profile_id TO WHOLE INTEGERS (NO DECIMALS)
#༚ numbers in this column are numeric ID codes - not actual numeric values - so were all originally whole numbers
#%% Create backup copy of unedited glider_profile_id col for safety/QC warning print out
orig_profile = df["glider_profile_id"].copy()

#%% Convert col to numeric (*anything non-numeric becomes NaN)
profile_numeric = pd.to_numeric(df["glider_profile_id"], errors="coerce")

# find cells that were not missing originally but failed numeric conversion
bad_profile_mask = orig_profile.notna() & profile_numeric.isna()

# print warning if any glider_profile_id values could NOT be converted to numbers
if bad_profile_mask.any():
    print("⚠️WARNING: Some 'glider_profile_id' values could not be converted to whole numbers.")
    print("These rows will become <NA> in the cleaned dataframe:")
    print(df.loc[bad_profile_mask, ["glider_profile_id"]])

# assign converted values back to dataframe as whole integers (Int64 allows <NA>; removes the ".0" from float values)
df["glider_profile_id"] = profile_numeric.round().astype("Int64")

#❥ CONVERT ALL DATETIME COLUMNS TO PROPER datetime64[ns, UTC] DATA TYPE
#%% Set list of datetime column names
dt_cols = ["start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]

#%% Convert datetime cols to datetime64[ns, UTC]
for col in dt_cols:
    # create backup copy of unedited datetime cols for safety/QC warning print out
    orig_dt = df[col].copy()
    # convert to UTC-aware datetime *anything unparseable becomes NaT (format="ISO8601" handles rows with and without fractional seconds (e.g., "13:38:43+00:00" and "13:38:43.000002+00:00"))
    converted_dt = pd.to_datetime(df[col], errors="coerce", utc=True, format="ISO8601")
    # find cells that were not missing originally but FAILED datetime conversion
    bad_dt_mask = orig_dt.notna() & converted_dt.isna()
    # print warning if any values in col (in current loop iteration) could NOT be converted
    if bad_dt_mask.any():
        print(f"⚠️WARNING: Some values in '{col}' could not be converted to datetime64[ns, UTC].")
        print("These rows will become NaT in the cleaned dataframe:")
        print(df.loc[bad_dt_mask, [col]])
    # assign cleaned datetime column back to dataframe (*force nanosecond-resolution UTC dtype = [ns, UTC] NOT [us, UTC]) + round to nearest second to remove ArcGIS float artifacts (e.g., "19:44:46.000002+00:00" → "19:44:46+00:00")
    df[col] = converted_dt.dt.round("s").astype("datetime64[ns, UTC]")

#❥ CONVERT GLIDERDEPTH VALUES FROM POSITIVE TO NEGATIVE
#༚ this way glider_depth_m and bathymetric_depth_m are both negative values
#%% Convert glider_depth_m to negative values (0 = surface)
df["glider_depth_m"] = -df["glider_depth_m"].abs()

#❥ SORT ROWS CHRONOLOGICALLY
#༚ sort by ascending datetime values in 'start_datetime_UTC' col
#%% Sort rows by ascending start_datetime_UTC (*extra safety: na_position="last" keeps any missing datetimes at the bottom)
df = df.sort_values(by="start_datetime_UTC", ascending=True, na_position="last").reset_index(drop=True)

#❥ EXPORT TIDIED CSV
#%% Set text columns to pandas string dtype
string_cols = ["mission_name", "glider_nc_file", "glider_profile_id", "ID", "UID", "suborder", "family", "genus", "species", "common_name", "nearest_shoreline_name"]
df[string_cols] = df[string_cols].astype("string")

# strip and normalize whitespace in all string columns (removes leading/trailing spaces and collapses internal runs of whitespace to a single space)
for col in string_cols:
    df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)

# convert empty strings left after stripping to <NA>
df[string_cols] = df[string_cols].replace("", pd.NA)

#%% Check data type of each column before exporting
for col, dt in df.dtypes.items():
    print(f"{col}: {dt}")

    #~ PRINT OUT SHOULD MATCH THIS:                                  
    #~ mission_name                                            string
    #~ glider_nc_file                                          string
    #~ glider_profile_id                                       string
    #~ n_channels                                               int64
    #~ sample_rate_kHz                                          int64
    #~ bit_depth                                                int64
    #~ ID                                                      string
    #~ UID                                                     string
    #~ suborder                                                string
    #~ family                                                  string
    #~ genus                                                   string
    #~ species                                                 string
    #~ common_name                                             string
    #~ start_datetime_UTC                         datetime64[ns, UTC]
    #~ end_datetime_UTC                           datetime64[ns, UTC]
    #~ av_datetime_UTC                            datetime64[ns, UTC]
    #~ start_latitude_DD                                      float64
    #~ start_longitude_DD                                     float64
    #~ end_latitude_DD                                        float64
    #~ end_longitude_DD                                       float64
    #~ av_latitude_DD                                         float64
    #~ av_longitude_DD                                        float64
    #~ glider_depth_m                                         float64
    #~ water_temperature_C                                    float64
    #~ sea_surface_water_temperature_C                        float64
    #~ salinity_PSU                                           float64
    #~ sea_surface_salinity_PSU                               float64
    #~ oxygen_concentration_μmol_L                            float64
    #~ sea_surface_oxygen_concentration_μmol_L                float64
    #~ bathymetric_depth_m                                    float64
    #~ bathymetric_slope_deg                                  float64
    #~ native_raster_resolution_m                               int64
    #~ distance_to_shore_m                                    float64
    #~ nearest_shoreline_name                                  string
    #~ nearest_shoreline_fid                                    int64
    #~ nearest_shoreline_x_coordinate_DD                      float64
    #~ nearest_shoreline_y_coordinate_DD                      float64

#%% Export tidy df as CSV
#𖠜 UPDATE FILE PATH FOR MISSION
output_csv = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/tidy_sperm_points_p26920.csv")
df.to_csv(output_csv, index=False)

# print confirmation
print("Cleaned CSV exported to:")
print(output_csv)