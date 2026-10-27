'''
This script separates data in 'tidy_odontocetes_points_p26920' CSV by individual taxa exports separated data as 4 individual CSV files: 'tidy_goose_points_p26920', 'tidy_kogia_points_p26920', 'tidy_gervais_points_p26920', and 'tidy_uo_points_p26920'.

Input .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/missionname/data/5_data_gis/HF_gis_data
Output (tidy) .csv file directory: Same as input

𖠺 Created by Keiley Gregory on October 5, 2026
Last updated on October 5, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


#%%
from pathlib import Path
import pandas as pd

#%% Load CSV with all Odontocetes detections combined
#𖠜 UPDATE FILE PATH FOR MISSION
input_csv = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/tidy_odontocetes_points_p26920.csv")
df = pd.read_csv(input_csv)   


#❥ Separate data by individual species/taxa
#%% Strip stray whitespace from genus so matches are exact (should already be stripped in previous script, but just to be safe)
genus = df["genus"].str.strip()

#%% Separate by species/taxa
kogia_df = df[genus == "Kogia"]          # rows where 'genus' col = "Kogia"
goose_df = df[genus == "Ziphius"]        # rows where 'genus' col = "Ziphius"
gervais_df = df[genus == "Mesoplodon"]   # rows where 'genus' col = "Mesoplodon"
uo_df = df[genus.isna() | (genus == "")] # rows where 'genus' col = blank (empty cells or whitespace only)


#❥ Tidy and check separated data
#༚ Check counts of each df after separation
#%% Print row counts of input CSV + counts of each separated dataframe
print(f"Input CSV: {len(df)} rows")
print(f"\n -------------------------- \n")
print(f"Kogia:     {len(kogia_df)} rows")
print(f"Goose:     {len(goose_df)} rows")
print(f"Gervais:   {len(gervais_df)} rows")
print(f"UO:        {len(uo_df)} rows")
print(f"\n -------------------------- \n")
print(f"Total:     {len(goose_df) + len(kogia_df) + len(gervais_df) + len(uo_df)} rows")

    #~ Input CSV: 590 rows
    #~ -------------------------- 
    #~ Kogia:     3 rows
    #~ Goose:     9 rows
    #~ Gervais:   4 rows
    #~ UO:        574 rows
    #~ -------------------------- 
    #~ Total:     590 rows

#༚ Check and remove empty taxonomic classification calls from UO df
#%% Count non-blank cells in each column to be dropped (should all print 0; whitespace-only cells count as blank)
print(uo_df[["family", "genus", "species", "common_name"]].apply(lambda c: (c.str.strip().fillna("") != "").sum()))

#%% If above check returns 0, remove columns 'family', 'genus', 'species', and 'common_name' from UO df (all rows are blank for these columns in UO)
uo_df = uo_df.drop(columns=["family", "genus", "species", "common_name"])

#༚ Set and check data types of columns before export
#%% Set cols to string data type: mission_name, glider_nc_file, glider_profile_id, ID, UID, suborder, family, genus, species, common_name, nearest_shoreline_name
str_cols = ["mission_name", "glider_nc_file", "glider_profile_id", "ID", "UID", "suborder", "family", "genus", "species", "common_name", "nearest_shoreline_name"]

kogia_df = kogia_df.astype({c: "string" for c in str_cols})
goose_df = goose_df.astype({c: "string" for c in str_cols})
gervais_df = gervais_df.astype({c: "string" for c in str_cols})
# uo no longer has family/genus/species/common_name, so only convert the columns it still has
uo_df = uo_df.astype({c: "string" for c in str_cols if c in uo_df.columns})

#%% Set cols to datetime64[ns, UTC] data type: start_datetime_UTC, end_datetime_UTC, av_datetime_UTC
dt_cols = ["start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]

# parse as UTC, then force nanosecond units (pandas 3 otherwise defaults to microseconds, datetime64[us, UTC])
kogia_df = kogia_df.assign(**{c: pd.to_datetime(kogia_df[c], utc=True).dt.as_unit("ns") for c in dt_cols})
goose_df = goose_df.assign(**{c: pd.to_datetime(goose_df[c], utc=True).dt.as_unit("ns") for c in dt_cols})
gervais_df = gervais_df.assign(**{c: pd.to_datetime(gervais_df[c], utc=True).dt.as_unit("ns") for c in dt_cols})
uo_df = uo_df.assign(**{c: pd.to_datetime(uo_df[c], utc=True).dt.as_unit("ns") for c in dt_cols})

#%% Check data type of each column
for col, dt in kogia_df.dtypes.items():
    print(f"{col}: {dt}")
print(f"\n -------------------------- \n")
for col, dt in goose_df.dtypes.items():
    print(f"{col}: {dt}")
print(f"\n -------------------------- \n")
for col, dt in gervais_df.dtypes.items():
    print(f"{col}: {dt}")

    #~ PRINT OUT SHOULD MATCH THIS FOR GOOSE/KOGIA/GERVAIS:
    #~ mission_name: string
    #~ glider_nc_file: string
    #~ glider_profile_id: string
    #~ n_channels: int64
    #~ sample_rate_kHz: int64
    #~ bit_depth: int64
    #~ ID: string
    #~ UID: string
    #~ suborder: string
    #~ family: string
    #~ genus: string
    #~ species: string
    #~ common_name: string
    #~ start_datetime_UTC: datetime64[ns, UTC]
    #~ end_datetime_UTC: datetime64[ns, UTC]
    #~ av_datetime_UTC: datetime64[ns, UTC]
    #~ start_latitude_DD: float64
    #~ start_longitude_DD: float64
    #~ end_latitude_DD: float64
    #~ end_longitude_DD: float64
    #~ av_latitude_DD: float64
    #~ av_longitude_DD: float64
    #~ glider_depth_m: float64
    #~ water_temperature_C: float64
    #~ sea_surface_water_temperature_C: float64
    #~ salinity_PSU: float64
    #~ sea_surface_salinity_PSU: float64
    #~ oxygen_concentration_μmol_L: float64
    #~ sea_surface_oxygen_concentration_μmol_L: float64
    #~ bathymetric_depth_m: float64
    #~ bathymetric_slope_deg: float64
    #~ native_raster_resolution_m: int64
    #~ distance_to_shore_m: float64
    #~ nearest_shoreline_name: string
    #~ nearest_shoreline_fid: int64
    #~ nearest_shoreline_x_coordinate_DD: float64
    #~ nearest_shoreline_y_coordinate_DD: float64

#%% Check data type of each column before exporting
for col, dt in uo_df.dtypes.items():
    print(f"{col}: {dt}")

    #~ PRINT OUT SHOULD MATCH THIS FOR UO:
    #~ mission_name: string
    #~ glider_nc_file: string
    #~ glider_profile_id: string
    #~ n_channels: int64
    #~ sample_rate_kHz: int64
    #~ bit_depth: int64
    #~ ID: string
    #~ UID: string
    #~ suborder: string
    #~ start_datetime_UTC: datetime64[ns, UTC]
    #~ end_datetime_UTC: datetime64[ns, UTC]
    #~ av_datetime_UTC: datetime64[ns, UTC]
    #~ start_latitude_DD: float64
    #~ start_longitude_DD: float64
    #~ end_latitude_DD: float64
    #~ end_longitude_DD: float64
    #~ av_latitude_DD: float64
    #~ av_longitude_DD: float64
    #~ glider_depth_m: float64
    #~ water_temperature_C: float64
    #~ sea_surface_water_temperature_C: float64
    #~ salinity_PSU: float64
    #~ sea_surface_salinity_PSU: float64
    #~ oxygen_concentration_μmol_L: float64
    #~ sea_surface_oxygen_concentration_μmol_L: float64
    #~ bathymetric_depth_m: float64
    #~ bathymetric_slope_deg: float64
    #~ native_raster_resolution_m: int64
    #~ distance_to_shore_m: float64
    #~ nearest_shoreline_name: string
    #~ nearest_shoreline_fid: int64
    #~ nearest_shoreline_x_coordinate_DD: float64
    #~ nearest_shoreline_y_coordinate_DD: float64


#❥ Export separated data
#%% Export separated goose/kogia/gervais/uo dfs as CSVs
#𖠜 UPDATE FILE PATH FOR MISSION
output_kogia = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/tidy_kogia_points_p26920.csv")
kogia_df.to_csv(output_kogia, index=False)

output_goose = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/tidy_goose_points_p26920.csv")
goose_df.to_csv(output_goose, index=False)

output_gervais = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/tidy_gervais_points_p26920.csv")
gervais_df.to_csv(output_gervais, index=False)

output_uo = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/HF_gis_data/tidy_uo_points_p26920.csv")
uo_df.to_csv(output_uo, index=False)