'''
This script tidies and fixes errors in high-frequency acoustic analysis data for the mission, separates the combined data by species (or surfacings), and outputs final .csv files for each species' acoustic analysis results.

Input .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/2_data_processed/acoustic_processed/HF_processed
Output species/surfacings .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/*missionname*/data/3_data_analyzed/acoustic_analyzed/HF_analyzed

𖠺 Created by Keiley Gregory on May 7, 2026
Last updated on July 15, 2026
'''

#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION
# USE GERVAIS SECTION AS TEMPLATE FOR OTHER SPECIES AS APPLICABLE!!!!!


#%%
from pathlib import Path
import pandas as pd
import numpy as np
import re

#%% Import CSV of combined high-frequency selection table data
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/acoustic_processed/HF_processed/all_HF_clickevents_UVI2_Around_STX_20250306.csv")
raw_data = pd.read_csv(csv_path)

#✦ TIDY DATAFRAME + EXTRACT START DATETIME FROM FILENAME + INSPECT SPECIES ID CODE DATA (IN PREPARATION TO SPLIT DF BY SPECIES)
#%% Create copy of raw_data df and drop pamguard_event_start_UTC + event_n_clicks + comment cols
data = raw_data[
    [
        "n_channels",
        "ID",
        "UID",
        "species_id",
        "color_code",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
].copy()

#%% Add new manually set acoustic parameters/color code description cols and fill with pandas NA placeholder
new_cols = [
    "mission_name",
    "sample_rate_kHz",
    "bit_depth",
    "classification_confidence"
]
data[new_cols] = pd.NA

#%% Manually enter values in cols 'sample_rate_kHz', 'bit_depth', and 'mission_name' (same value for all rows in each col)
data["sample_rate_kHz"] = 240
data["bit_depth"] = 16
#𖠜 CHANGE MISSION NAME FOR CURRENT MISSION
data["mission_name"] = "UVI2_Around_STX_20250306"

#%% Force any cells with "missing-like" tokens (NA/NaN/null/blank) to real missing values (pd.NA)
missing_tokens = {"na", "n/a", "nan", "none", "null", "<na>", "missing"}

def normalize_missing_series(s: pd.Series) -> pd.Series:
    # only operate on object/string-like columns safely
    if s.dtype == "object" or pd.api.types.is_string_dtype(s):
        # preserve missing values as <NA>
        s2 = s.astype("string")
        # remove leading/trailing whitespace
        s2 = s2.str.strip()
        # set cells with whitespace-only to <NA>
        s2 = s2.replace(r"^\s*$", pd.NA, regex=True)
        # token-based missing to <NA> (case-insensitive)
        s2 = s2.mask(s2.str.lower().isin(missing_tokens), pd.NA)
        return s2
    return s

for col in data.columns:
    data[col] = normalize_missing_series(data[col])

#%% Format datetime columns as pandas datetime64[ns, UTC]
dt_cols = ["start_datetime_UTC", "end_datetime_UTC", "av_datetime_UTC"]
for c in dt_cols:
    data[c] = pd.to_datetime(data[c], utc=True)

#%% Clean string columns (ensure string format, strip whitespace)
string_cols = ["mission_name", "species_id"]
for c in string_cols:
    data[c] = data[c].astype("string").str.strip()

# Convert all strings in 'species_id' col to lowercase just to be extra safe
data["species_id"] = data["species_id"].str.lower()

#%% Clean numeric columns (nullable integers, keep missing as <NA>)
int_cols = ["n_channels", "ID", "UID", "color_code", "sample_rate_kHz", "bit_depth"]
for c in int_cols:
    # convert to numeric data type (if non-numeric (aka invalid) set as NaN)
    num = pd.to_numeric(data[c], errors="coerce")
    # convert NaN to <NA> while keeping integer dtype ('Int64' is pandas "nullable integer" data type = allows missing values)
    data[c] = num.round(0).astype("Int64")

#%% Reorder columns and save as new dataframe
data_clean = data[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "species_id",
        "color_code",
        "classification_confidence",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
].copy()

#%% Check data type of all cols
for col, dt in data_clean.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64 *
        #~ UID: Int64 *
        #~ species_id: string *
        #~ color_code: Int64 *
        #~ classification_confidence: string *
        #~ start_datetime_UTC: datetime64[ns, UTC] *
        #~ end_datetime_UTC: datetime64[ns, UTC] *
        #~ av_datetime_UTC: datetime64[ns, UTC] *

#%% Print list of species_id unique string values
print(data_clean['species_id'].unique().tolist())

    #𓇬 ['surf', 'zc', 'uo', 'pm', 'kg', 'me']


#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰
#❥ SPERM WHALES -------------------------------------------------------------------------------------------------------------------
#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰
#%% Create new df filtered to only rows with species unidentified sperm (species == "pm")
sperm = data_clean.loc[data_clean["species_id"] == "pm"].copy()

#✦ Convert color codes to confidence descriptions
#%% Print list of all color codes present in df for this species
print(sperm['color_code'].unique().tolist())

    #𓇬 COLOR CODES FOR PM SPECIES *SHOULD* BE: [9, 5]

#%% Create map of color code numbers -to-> confidence descriptions and populate classification_confidence col accordingly
pm_confidence_map = {5: "high", 9: "moderate"}
sperm['classification_confidence'] = sperm['color_code'].map(pm_confidence_map)

#%% Create new tidy df and remove species_id col (since all same species in this df) and color code col
sperm_clean = sperm.drop(columns=["species_id", "color_code"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
sperm_clean["suborder"] = "Odontoceti"
sperm_clean["family"] = "Physeteridae"
sperm_clean["genus"] = "Physeter"
sperm_clean["species"] = "macrocephalus"
sperm_clean["common_name"] = "sperm whale"

#%% Clean strings in classification and classification_confidence cols (ensure string format, strip whitespace)
sperm_clean["suborder"] = sperm_clean["suborder"].astype("string").str.strip()
sperm_clean["family"] = sperm_clean["family"].astype("string").str.strip()
sperm_clean["genus"] = sperm_clean["genus"].astype("string").str.strip()
sperm_clean["species"] = sperm_clean["species"].astype("string").str.strip()
sperm_clean["common_name"] = sperm_clean["common_name"].astype("string").str.strip()
sperm_clean["classification_confidence"] = sperm_clean["classification_confidence"].astype("string").str.strip()

#%% Reorder columns
sperm_clean = sperm_clean[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "suborder",
        "family",
        "genus",
        "species",
        "common_name",
        "classification_confidence",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#✦ Remove any duplicate rows
#%% Create copy of sperm_clean for duplicate row removal
sperm_nodup = sperm_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
pm_true_dup_mask = sperm_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
pm_n_true_dups = int(pm_true_dup_mask.sum())

# Drop extra copies of duplicate rows
sperm_nodup = sperm_nodup.loc[~pm_true_dup_mask].copy()
print(
    f"✅ Removed {pm_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(sperm_clean)} → {len(sperm_nodup)}"
)
        #𓇬 ✅ Removed 0 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 358 → 358

#%% Create copy of sperm_nodup df to use for final output CSV
sperm_final = sperm_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
sperm_final = sperm_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in sperm_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64
        #~ UID: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ classification_confidence: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final sperm df as CSV (output to 'HF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
pm_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/sperm_analyzed_UVI2_Around_STX_20250306.csv")
sperm_final.to_csv(pm_output_csv_path, index=False)
print(f"Saved sperm CSV to: {pm_output_csv_path}")


#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ UNIDENTIFIED ODONTOCETES -----------------------------------------------------------------------------------------------
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#%% Create new df filtered to only rows with species unidentified odontocetes (species == "uo")
unid_odontocetes = data_clean.loc[data_clean["species_id"] == "uo"].copy()

#✦ Convert color codes to confidence descriptions
#%% Print list of all color codes present in df for this species
print(unid_odontocetes['color_code'].unique().tolist())

    #𓇬 COLOR CODES FOR UO SPECIES *SHOULD* BE: [4, 6]

#%% Create map of color code numbers -to-> confidence descriptions and populate classification_confidence col accordingly
uo_confidence_map = {4: "high", 6: "moderate"}
unid_odontocetes['classification_confidence'] = unid_odontocetes['color_code'].map(uo_confidence_map)

#%% Create new tidy df and remove species_id col (since all same species in this df) and color code col
unid_odontocetes_clean = unid_odontocetes.drop(columns=["species_id", "color_code"], errors="ignore").copy()

#%% Add clean species name column (same set string value same for every row)
unid_odontocetes_clean["suborder"] = "Odontoceti"

#%% Clean strings in suborder and classification_confidence col (ensure string format, strip whitespace)
unid_odontocetes_clean["suborder"] = unid_odontocetes_clean["suborder"].astype("string").str.strip()
unid_odontocetes_clean["classification_confidence"] = unid_odontocetes_clean["classification_confidence"].astype("string").str.strip()

#%% Reorder columns
unid_odontocetes_clean = unid_odontocetes_clean[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "suborder",
        "classification_confidence",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#✦ Remove any duplicate rows
#%% Create copy of odontocetes_clean for duplicate row removal
unid_odontocetes_nodup = unid_odontocetes_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
uo_true_dup_mask = unid_odontocetes_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
uo_n_true_dups = int(uo_true_dup_mask.sum())

# Drop extra copies of duplicate rows
unid_odontocetes_nodup = unid_odontocetes_nodup.loc[~uo_true_dup_mask].copy()
print(
    f"✅ Removed {uo_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(unid_odontocetes_clean)} → {len(unid_odontocetes_nodup)}"
)

        #𓇬 ✅ Removed 1 exact duplicate row(s) (same start_datetime_UTC): 2025-03-08 22:07:44+00:00
        #𓇬 Rows: 572 → 571

#%% Create copy of odontocetes_nodup df to use for final output CSV
unid_odontocetes_final = unid_odontocetes_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
unid_odontocetes_final = unid_odontocetes_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in unid_odontocetes_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64
        #~ UID: Int64
        #~ suborder: string
        #~ classification_confidence: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final odontocetes df as CSV (output to 'HF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
uo_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/unidentified_odontocetes_analyzed_UVI2_Around_STX_20250306.csv")
unid_odontocetes_final.to_csv(uo_output_csv_path, index=False)
print(f"Saved odontocetes CSV to: {uo_output_csv_path}")


#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ GERVAIS' BEAKED WHALES -------------------------------------------------------------------------------------------------
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#%% Create new df filtered to only rows with species gervais' beaked whale (species == "me")
gervais = data_clean.loc[data_clean["species_id"] == "me"].copy()

#%% Print list of all color codes present in df for this species (just to check)
print(gervais['color_code'].unique().tolist())

    #𓇬 COLOR CODE FOR ME SPECIES *SHOULD* BE: [2]

#%% Create new tidy df and remove species_id col (since all same species in this df) and color code col
gervais_clean = gervais.drop(columns=["species_id", "color_code"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
gervais_clean["suborder"] = "Odontoceti"
gervais_clean["family"] = "Ziphiidae"
gervais_clean["genus"] = "Mesoplodon"
gervais_clean["species"] = "europaeus"
gervais_clean["common_name"] = "gervais' beaked whale"

#%% Clean strings in classification and classification_confidence cols (ensure string format, strip whitespace)
gervais_clean["suborder"] = gervais_clean["suborder"].astype("string").str.strip()
gervais_clean["family"] = gervais_clean["family"].astype("string").str.strip()
gervais_clean["genus"] = gervais_clean["genus"].astype("string").str.strip()
gervais_clean["species"] = gervais_clean["species"].astype("string").str.strip()
gervais_clean["common_name"] = gervais_clean["common_name"].astype("string").str.strip()

#%% Reorder columns
gervais_clean = gervais_clean[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "suborder",
        "family",
        "genus",
        "species",
        "common_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#✦ Remove any duplicate rows
#%% Create copy of gervais_clean for duplicate row removal
gervais_nodup = gervais_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
me_true_dup_mask = gervais_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
me_n_true_dups = int(me_true_dup_mask.sum())

# Drop extra copies of duplicate rows
gervais_nodup = gervais_nodup.loc[~me_true_dup_mask].copy()
print(
    f"✅ Removed {me_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(gervais_clean)} → {len(gervais_nodup)}"
)

        #𓇬 ✅ Removed 0 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 4 → 4

#%% Create copy of gervais_nodup df to use for final output CSV
gervais_final = gervais_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
gervais_final = gervais_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in gervais_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64
        #~ UID: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final gervais df as CSV (output to 'HF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
me_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/gervais_analyzed_UVI2_Around_STX_20250306.csv")
gervais_final.to_csv(me_output_csv_path, index=False)
print(f"Saved gervais CSV to: {me_output_csv_path}")


#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ GOOSE-BEAKED WHALES ----------------------------------------------------------------------------------------------------
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#%% Create new df filtered to only rows with species goose-beaked whale (species == "zc")
goose = data_clean.loc[data_clean["species_id"] == "zc"].copy()

#%% Print list of all color codes present in df for this species (just to check)
print(goose['color_code'].unique().tolist())

    #𓇬 COLOR CODE FOR ZC SPECIES *SHOULD* BE: [12]

#%% Create new tidy df and remove species_id col (since all same species in this df) and color code col
goose_clean = goose.drop(columns=["species_id", "color_code"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
goose_clean["suborder"] = "Odontoceti"
goose_clean["family"] = "Ziphiidae"
goose_clean["genus"] = "Ziphius"
goose_clean["species"] = "cavirostris"
goose_clean["common_name"] = "goose-beaked whale"

#%% Clean strings in classification and classification_confidence cols (ensure string format, strip whitespace)
goose_clean["suborder"] = goose_clean["suborder"].astype("string").str.strip()
goose_clean["family"] = goose_clean["family"].astype("string").str.strip()
goose_clean["genus"] = goose_clean["genus"].astype("string").str.strip()
goose_clean["species"] = goose_clean["species"].astype("string").str.strip()
goose_clean["common_name"] = goose_clean["common_name"].astype("string").str.strip()

#%% Reorder columns
goose_clean = goose_clean[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "suborder",
        "family",
        "genus",
        "species",
        "common_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#✦ Remove any duplicate rows
#%% Create copy of goose_clean for duplicate row removal
goose_nodup = goose_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
zc_true_dup_mask = goose_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
zc_n_true_dups = int(zc_true_dup_mask.sum())

# Drop extra copies of duplicate rows
goose_nodup = goose_nodup.loc[~zc_true_dup_mask].copy()
print(
    f"✅ Removed {zc_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(goose_clean)} → {len(goose_nodup)}"
)

        #𓇬 ✅ Removed 0 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 9 → 9

#%% Create copy of goose_nodup df to use for final output CSV
goose_final = goose_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
goose_final = goose_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in goose_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64
        #~ UID: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final goose df as CSV (output to 'HF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
zc_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/goose_analyzed_UVI2_Around_STX_20250306.csv")
goose_final.to_csv(zc_output_csv_path, index=False)
print(f"Saved goose CSV to: {zc_output_csv_path}")


#❋ ◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠
#❋ KOGIA SPP --------------------------------------------------------------------------------------------------------------
#❋ ◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡
#%% Create new df filtered to only rows with species kogia (species == "kg")
kogia = data_clean.loc[data_clean["species_id"] == "kg"].copy()

#%% Print list of all color codes present in df for this species (just to check)
print(kogia['color_code'].unique().tolist())

    #𓇬 COLOR CODE FOR KG SPECIES *SHOULD* BE: [7]

#%% Create new tidy df and remove species_id col (since all same species in this df) and color code col
kogia_clean = kogia.drop(columns=["species_id", "color_code"], errors="ignore").copy()

#%% Add taxonomy + common name columns (set string value same for every row)
kogia_clean["suborder"] = "Odontoceti"
kogia_clean["family"] = "Kogiidae"
kogia_clean["genus"] = "Kogia"
kogia_clean["species"] = "breviceps or sima"
kogia_clean["common_name"] = "pygmy or dwarf sperm whale"

#%% Clean strings in classification and classification_confidence cols (ensure string format, strip whitespace)
kogia_clean["suborder"] = kogia_clean["suborder"].astype("string").str.strip()
kogia_clean["family"] = kogia_clean["family"].astype("string").str.strip()
kogia_clean["genus"] = kogia_clean["genus"].astype("string").str.strip()
kogia_clean["species"] = kogia_clean["species"].astype("string").str.strip()
kogia_clean["common_name"] = kogia_clean["common_name"].astype("string").str.strip()

#%% Reorder columns
kogia_clean = kogia_clean[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "suborder",
        "family",
        "genus",
        "species",
        "common_name",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#✦ Remove any duplicate rows
#%% Create copy of kogia_clean for duplicate row removal
kogia_nodup = kogia_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
kg_true_dup_mask = kogia_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
kg_n_true_dups = int(kg_true_dup_mask.sum())

# Drop extra copies of duplicate rows
kogia_nodup = kogia_nodup.loc[~kg_true_dup_mask].copy()
print(
    f"✅ Removed {kg_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(kogia_clean)} → {len(kogia_nodup)}"
)

        #𓇬 ✅ Removed 0 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 3 → 3

#%% Create copy of kogia_nodup df to use for final output CSV
kogia_final = kogia_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
kogia_final = kogia_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in kogia_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64
        #~ UID: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final kogia df as CSV (output to 'HF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
kg_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/kogia_analyzed_UVI2_Around_STX_20250306.csv")
kogia_final.to_csv(kg_output_csv_path, index=False)
print(f"Saved kogia CSV to: {kg_output_csv_path}")


#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱ 
#❥ OTHER ODONTOCETES: ALL DETECTIONS IN UNIDENTIFIED ODONTOCETES + ALL SPECIES *OTHER THAN* SPERM WHALES ---------------------------------------------------------------
#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱ 
#%% Combine all non-sperm whale odontocete dataframes (outer join preserves all columns; missing cols filled with pd.NA)
other_odontocetes = pd.concat(
    [unid_odontocetes_final, goose_final, gervais_final, kogia_final],
    axis=0,
    join="outer",
    ignore_index=True
)

#%% Reorder columns
other_odontocetes = other_odontocetes[
    [
        "mission_name",
        "n_channels",
        "sample_rate_kHz",
        "bit_depth",
        "ID",
        "UID",
        "suborder",
        "family",
        "genus",
        "species",
        "common_name",
        "classification_confidence",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
]

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
other_odontocetes = other_odontocetes.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in other_odontocetes.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ n_channels: Int64
        #~ sample_rate_kHz: Int64
        #~ bit_depth: Int64
        #~ ID: Int64
        #~ UID: Int64
        #~ suborder: string
        #~ family: string
        #~ genus: string
        #~ species: string
        #~ common_name: string
        #~ classification_confidence: string
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final combined non-sperm odontocetes df as CSV
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
other_odo_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/odontocetes_analyzed_UVI2_Around_STX_20250306.csv")
other_odontocetes.to_csv(other_odo_output_csv_path, index=False)
print(f"Saved other odontocetes CSV to: {other_odo_output_csv_path}")


#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱ 
#❥ SURFACING MINUTES ---------------------------------------------------------------------------------------------------------------------------------------------------
#❥ ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱⋰‧𐰢ᐝ⋱⋰⋱⋰⋱⋰⋱⋰⋱ 
#%% Create new df filtered to only rows with species surfacing (species == "surf")
surfacing = data_clean.loc[data_clean["species_id"] == "surf"].copy()

#%% Print list of all color codes present in df for this species (just to check)
print(surfacing['color_code'].unique().tolist())

    #𓇬 COLOR CODE FOR SURFACING MINS (SURF) *SHOULD* BE: [8]

#%% Create new tidy df + remove and reorder columns
surfacing_clean = surfacing[
    [
        "mission_name",
        "ID",
        "UID",
        "start_datetime_UTC",
        "end_datetime_UTC",
        "av_datetime_UTC"
    ]
].copy()

#✦ Remove any duplicate rows
#%% Create copy of surfacing_clean for duplicate row removal
surfacing_nodup = surfacing_clean.copy()

#%% IF duplicate rows have exact same value in start_datetime_UTC then only keep 1 row of each duplicate group
surf_true_dup_mask = surfacing_nodup.duplicated(
    subset=["start_datetime_UTC"],
    keep="first"
)
surf_n_true_dups = int(surf_true_dup_mask.sum())

# Drop extra copies of duplicate rows
surfacing_nodup = surfacing_nodup.loc[~surf_true_dup_mask].copy()
print(
    f"✅ Removed {surf_n_true_dups} exact duplicate row(s) (same start_datetime_UTC)"
    f"\nRows: {len(surfacing_clean)} → {len(surfacing_nodup)}"
)

        #𓇬 ✅ Removed 0 exact duplicate row(s) (same start_datetime_UTC)
        #𓇬 Rows: 533 → 533

#%% Create copy of surfacing_nodup df to use for final output CSV
surfacing_final = surfacing_nodup.copy()

#%% Sort rows by ascending start_datetime_UTC (earliest → latest)
surfacing_final = surfacing_final.sort_values(
    by="start_datetime_UTC",
    ascending=True,
    # stable sort (keeps existing order for any rows with same start_datetime_UTC - but this should never happen)
    kind="mergesort"
).reset_index(drop=True)

#%% Check data type of all cols
for col, dt in surfacing_final.dtypes.items():
    print(f"{col}: {dt}")

        #~ PRINT OUT SHOULD MATCH THIS:
        #~ mission_name: string
        #~ ID: Int64
        #~ UID: Int64
        #~ start_datetime_UTC: datetime64[ns, UTC]
        #~ end_datetime_UTC: datetime64[ns, UTC]
        #~ av_datetime_UTC: datetime64[ns, UTC]

#%% Export final surfacing df as CSV (output to 'HF_analyzed' folder in mission repo); this CSV will be used for interpolation calculations!!
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
surf_output_csv_path = Path(r"/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/3_data_analyzed/acoustic_analyzed/HF_analyzed/HF_surfacing_mins_UVI2_Around_STX_20250306.csv")
surfacing_final.to_csv(surf_output_csv_path, index=False)
print(f"Saved surfacing CSV to: {surf_output_csv_path}")