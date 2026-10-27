# ──────────────────────────────────────────────────────────────────────────────
# This script...


# ⺌⺌⺌ DATA SOURCES ⺌⺌⺌
# Sea surface temperature: "Multi-scale Ultra-high Resolution (MUR) SST Analysis fv04.1, Global, 0.01°, 2002-present, Daily" (NASA JPL); resolution = 1 km; EPSG:4326 (WGS 1984)

# Sea surface salinity: "Global Ocean Physics Analysis and Forecast Salinity, daily" (Copernicus Marine Service); resolution = 0.083° (~9.2 km at equator); EPSG:4326 (WGS 1984)

# Sea surface chlorophyll-a: "Chlorophyll (Gap-filled DINEOF), NOAA S-NPP NOAA-20 VIIRS and Copernicus S-3A OLCI, Science Quality, Global 2km, 2018-recent, Daily" (NOAA NESDIS STAR); resolution = 2 km; EPSG:4326 (WGS 1984)
  # https://coastwatch.noaa.gov/cwn/products/noaa-msl12-multi-sensor-dineof-global-2-km-gap-filled-products-chlorophyll-diffuse.html
  # https://coastwatch.noaa.gov/thredds/socd/coastwatch/catalog_blended_dineof_2km_global_chlora_daily.html

# Bathymetry (depth and slope): GEBCO 2025 Gridded Bathymetry Data; resolution = 15 arc-second (~0.46 km at equator); EPSG:26920 (NAD83 / UTM zone 20N)

# Distance to nearest shoreline: CARIBBEAN_SHORELINES shapefile (J. Blondeau, UVI); EPSG:26920 (NAD83 / UTM zone 20N)
# ⺣ ⺣ ⺣

# 𖠺 Created by Keiley Gregory on March 17, 2026
# Last updated on July 17, 2026
# ──────────────────────────────────────────────────────────────────────────────

# SEARCH "#‼️" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION



library(rerddap)
library(terra)
library(sdmpredictors)
library(corrplot)
library(ncdf4)
library(ggplot2)
library(tidyterra)

# ╬╬═════════════════════════════════════════════════════════════════════════╬╬ 
# Use bathymetry raster cropped to mission boundary (in ArcGIS) for extent of MaxEnt variable maps
#‼️‼️ UPDATE FILE PATH FOR MISSION
bathy_gbc <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/rasters_shapefiles/merge_bathy_aroundstx2025.tif")

# print extent lat/lon values of bathymetry raster (*prints lat/lon even if in UTM)
ext(project(bathy_gbc, "EPSG:4326")) # SpatExtent : -66.0167521541008, -62.9050377752297, 16.6029114106496, 18.7892888718758 (xmin, xmax, ymin, ymax)

# SET MAP EXTENT PARAMETERS ----------------------------------------------------
#‼️‼️ UPDATE BASED ON OUTPUT OF ABOVE LINE
lon_min <- -66.0167521541008
lon_max <- -62.9050377752297
lat_min <- 16.6029114106496
lat_max <- 18.7892888718758
date_start <- "2025-03-06T00:00:00"
date_end   <- "2025-03-24T11:59:59"
# ╬╬═════════════════════════════════════════════════════════════════════════╬╬ 


################################################################################
# LOAD AND SAVE SST, SSS, AND CHL-A DATA AS .NC FILES + EXPORT MEANS TO GEOTIFFS
################################################################################

# ------------------------------------------------------------------------------
# Sea surface water temperature (daily, ERDDAP)                                 
# ------------------------------------------------------------------------------
# ERDDAP dataset info
#‼️‼️ UPDATE BASED ON TIMESPAN AND AREA OF MISSION 
sst_erd <- info("jplMURSST41", url = "https://coastwatch.pfeg.noaa.gov/erddap/")
sst_erd
# <ERDDAP(TM) info> jplMURSST41 
# Base URL: https://coastwatch.pfeg.noaa.gov/erddap 
# Dataset Type: griddap 
# Dimensions (range):  
#   time: (2002-06-01T09:00:00Z, 2026-03-16T09:00:00Z) 
#   latitude: (-89.99, 89.99) 
#   longitude: (-179.99, 180.0) 
# Variables:  
#   analysed_sst: 
#     Units: degree_C 
#   analysis_error: 
#     Units: degree_C 
# mask: 
#   sea_ice_fraction: 
#     Units: 1 

# pull SST data from loaded dataset
sst_raw <- griddap(
  sst_erd,
  fields    = "analysed_sst",
  time      = c(date_start, date_end),
  latitude  = c(lat_min, lat_max),
  longitude = c(lon_min, lon_max),
  fmt       = "nc",
  # directory for output file
  store     = disk("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/")
)

# Find name of downloaded .nc file (since can't set manually) and rename
list.files("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/", pattern = "\\.nc$")
# ‼️CHANGE FILE RENAME BASED ON RESULTS OF LIST.FILES OUTPUT
file.rename(
  "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/94d57c8c36179d3badb29521d21f183a.nc",
  "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sst_maxent_env_stack_mur_nasajpl.nc"
)

# Load data from output netCDF and compute temporal mean
sst_nc <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sst_maxent_env_stack_mur_nasajpl.nc")
# verify range (should be ~27-29 C)
sst_nc <- setMinMax(sst_nc)
global(sst_nc[[1]], "range", na.rm = TRUE) 
#                 min     max   
# analysed_sst_1  26.14   27.382

# Calculate mean across mission period
sst_mean <- mean(sst_nc, na.rm = TRUE)
names(sst_mean) <- "SST"

# Export SST maxent data as GeoTIFF
writeRaster(sst_mean, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sstmean_maxent_env_stack_mur_nasajpl.tif", overwrite = TRUE)

# Plot data and export as PNG
png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sstmean_maxent_env_stack_mur_nasajpl.png", width = 10, height = 8, units = "in", res = 300)
plot(sst_mean, main = "SST Mean (°C) - UVI2_Around_STX_20250306")
dev.off()


# ------------------------------------------------------------------------------
# Sea surface salinity (daily, CMEMS)                                           
# ------------------------------------------------------------------------------
# Import SSS data from GLOBAL_ANALYSISFORECAST_PHY_001_024 product
#‼️‼️ UPDATE BASED ON TIMESPAN AND AREA OF MISSION 
system(paste(
  "copernicusmarine subset",
  "--dataset-id cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
  "--variable so",
  "--start-datetime 2025-03-06T00:00:00",
  "--end-datetime 2025-03-24T11:59:59",
  "--minimum-longitude", lon_min,
  "--maximum-longitude", lon_max,
  "--minimum-latitude",  lat_min,
  "--maximum-latitude",  lat_max,
  "--minimum-depth 0",
  "--maximum-depth 0.5",
  "--output-filename sss_maxent_env_stack_anfc_cmems.nc",
  "--output-directory '/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/'",
  "--overwrite"
))

# Load data from downloaded .nc file
sss_nc <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sss_maxent_env_stack_anfc_cmems.nc")
# verify range (should be ~35-37 PSU for Caribbean)
sss_nc <- setMinMax(sss_nc)
global(sss_nc[[1]], "range", na.rm = TRUE)
#                         min       max
# so_depth=0.49402499_1   35.89314  36.92997

# Calculate mean across mission period
sss_mean <- mean(sss_nc, na.rm = TRUE)
names(sss_mean) <- "SSS"

# Crop to study extent (should already be clipped but enforce)
study_ext <- ext(c(lon_min, lon_max, lat_min, lat_max))
sss_crop <- crop(sss_mean, study_ext)

# Export SSS maxent data as GeoTIFF
writeRaster(sss_crop, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sssmean_maxent_env_stack_anfc_cmems.tif", overwrite = TRUE)

# Plot data and export as PNG
png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sssmean_maxent_env_stack_anfc_cmems.png", width = 10, height = 8, units = "in", res = 300)
plot(sss_crop, main = "SSS Mean (PSU) - UVI2_Around_STX_20250306")
dev.off()


# ------------------------------------------------------------------------------
# Sea surface chlorophyll-a (daily, ERDDAP)                                     
# ------------------------------------------------------------------------------
# ERDDAP dataset info
#‼️‼️ UPDATE BASED ON TIMESPAN AND AREA OF MISSION 
chl_erd <- info("noaacwNPPN20S3ASCIDINEOF2kmDaily", url = "https://coastwatch.noaa.gov/erddap/")
chl_erd
# <ERDDAP(TM) info> noaacwNPPN20S3ASCIDINEOF2kmDaily 
# Base URL: https://coastwatch.noaa.gov/erddap 
# Dataset Type: griddap 
# Dimensions (range):  
#   time: (2018-01-01T12:00:00Z, 2026-03-06T12:00:00Z) 
#   altitude: (0.0, 0.0) 
#   latitude: (-89.98959, 89.98959) 
#   longitude: (-179.9896, 179.9896) 
# Variables:  
#   chlor_a: 
#     Units: mg m^-3 

# pull Chl-a data from loaded dataset
chl_raw <- griddap(
  chl_erd,
  fields    = "chlor_a",
  time      = c("2025-03-06T00:00:00Z", "2025-03-24T11:59:59Z"),
  latitude  = c(lat_min, lat_max),
  longitude = c(lon_min, lon_max),
  fmt       = "nc",
  store     = disk("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/")
)

# Find name of saved .nc file (since can't set manually) and rename
list.files("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/", pattern = "\\.nc$", full.names = TRUE)
# ‼️CHANGE FILE RENAME BASED ON RESULTS OF LIST.FILES OUTPUT
file.rename(
  "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/0be265f0bfaa1b0b7f392865c389a1d6.nc",
  "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/chla_maxent_env_stack_noaa_nesdisstar.nc"
)

# Load data from downloaded .nc file
chl_nc <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/chla_maxent_env_stack_noaa_nesdisstar.nc")
# check units and n layers
print(chl_nc)
# class       : SpatRaster 
# size        : 106, 150, 19  (nrow, ncol, nlyr)
# resolution  : 0.02083334, 0.02083333  (x, y)
# extent      : -66.02083, -62.89583, 16.58333, 18.79166  (xmin, xmax, ymin, ymax)
# coord. ref. : lon/lat WGS 84 (CRS84) (OGC:CRS84) 
# source      : chla_maxent_env_stack_noaa_nesdisstar.nc 
# varname     : chlor_a (Chlorophyll Concentration, Default Algorithm) 
# names       : chlor~e=0_1, chlor~e=0_2, chlor~e=0_3, chlor~e=0_4, chlor~e=0_5, chlor~e=0_6,     ... 
# unit        : mg m^-3 
# depth       : 0 
# time        : 2025-03-06 12:00:00 to 2025-03-24 12:00:00 UTC (19 steps) 

# Calculate mean across mission period
chl_mean <- mean(chl_nc, na.rm = TRUE)
names(chl_mean) <- "CHL"

# Color scale is being stretched by a few high nearshore pixels --> log-transform for habitat model since chl-a is typically log-normally distributed
chl_mean_log <- log(chl_mean)
names(chl_mean_log) <- "CHL_log"

# Export Chl-a maxent data as GeoTIFF
writeRaster(chl_mean_log, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/chlameanlog_maxent_env_stack_noaa_nesdisstar.tif", overwrite = TRUE)

# Plot data and export as PNG
png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/chlameanlog_maxent_env_stack_noaa_nesdisstar.png", width = 10, height = 8, units = "in", res = 300)
plot(chl_mean_log, main = "log(Chl-a) (mg m^-3) - UVI2_Around_STX_20250306")
dev.off()


#ꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘ


################################################################################
# RESAMPLE AND REPORJECT TO MATCH GEBCO BATHYMETRY RASTER                       
################################################################################

# Reference grid from GEBCO bathy (UTM 26920, ~462m) = resample target: 1km in UTM units (creates empty template raster that matches spatial extent and CRS of bathy_gbc (UTM 26920, meters) *BUT* with fixed resolution of 1000 m × 1000 m)
ref_grid <- rast(ext = ext(bathy_gbc), res = 1000, crs = crs(bathy_gbc))

# Warp bathy_gbc (originally ~462 m resolution) onto 1 km grid (*bilinear interpolation estimates each new cell depth value as weighted average of four nearest source cells)
bathy_1km <- resample(bathy_gbc, ref_grid, method = "bilinear")
names(bathy_1km) <- "bathymetry"

# Calculate slope onto 1 km grid (from bathymetry raster)
slope_1km <- terrain(bathy_1km, v = "slope", unit = "degrees")
names(slope_1km) <- "slope"

# Reproject SST → UTM 1km
sst <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sstmean_maxent_env_stack_mur_nasajpl.tif")
sst_1km <- project(sst, ref_grid, method = "bilinear")
names(sst_1km) <- "SST"

# Reproject SSS → UTM 1km
sss <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/sssmean_maxent_env_stack_anfc_cmems.tif")
sss_1km <- project(sss, ref_grid, method = "bilinear")
names(sss_1km) <- "SSS"

# !!! Gap-fill SSS NA cells (coastal gaps from ~9 km source resolution) !!!
# uses iterative focal mean with 3x3 window — repeats until all ocean cells are filled.
# ocean mask defined by bathymetry (non-NA bathy = valid ocean cell).
ocean_mask  <- !is.na(bathy_1km)
cat("SSS NA cells before gap-fill:", global(is.na(sss_1km) & ocean_mask, "sum")[[1]], "\n") # SSS NA cells before gap-fill: 2764
sss_filled <- sss_1km
max_iter    <- 50
for (i in seq_len(max_iter)) {
  na_count <- global(is.na(sss_filled) & ocean_mask, "sum")[[1]]
  if (na_count == 0) break
  sss_filled <- focal(sss_filled, w = 3, fun = "mean", na.policy = "only", na.rm = TRUE)
  cat("  Gap-fill iteration", i, "— remaining NA ocean cells:", 
      global(is.na(sss_filled) & ocean_mask, "sum")[[1]], "\n")
}
    # Gap-fill iteration 3 — remaining NA ocean cells: 1353 
    # ...
    # Gap-fill iteration 13 — remaining NA ocean cells: 209 
    # ...
    # Gap-fill iteration 23 — remaining NA ocean cells: 0 

# Re-apply ocean mask so land cells stay NA
sss_filled <- mask(sss_filled, bathy_1km)
names(sss_filled) <- "SSS"
cat("SSS NA cells after gap-fill:", global(is.na(sss_filled) & ocean_mask, "sum")[[1]], "\n") # SSS NA cells after gap-fill: 0
sss_1km <- sss_filled
rm(sss_filled, ocean_mask)

# Reproject Chl-a → UTM 1km
chl <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/chlameanlog_maxent_env_stack_noaa_nesdisstar.tif")
chl_1km <- project(chl, ref_grid, method = "bilinear")
names(chl_1km) <- "Chl_log"

# (note: Distance to nearest shoreline does NOT need to be resampled/reprojected)


# ------------------------------------------------------------------------------
# Distance to nearest shoreline (CARIBBEAN_SHORELINES.shp)                      
# ------------------------------------------------------------------------------
# Load shoreline data from CARIBBEAN_SHORELINES shapefile (*MUST also have .dbf, .prj, and .shx sidecar files in same folder as .shp file)
shore <- vect("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/rasters_shapefiles/CARIBBEAN_SHORELINES.shp")

# Crop to map extent
shore_crop <- project(shore, crs(bathy_1km))

# Compute distance from each raster cell to nearest shoreline (meters)
dist_shore <- distance(bathy_1km, shore_crop)
names(dist_shore) <- "dist_shore"

# Export shoreline distance maxent data as GeoTIFF
writeRaster(dist_shore, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/shoredist_maxent_env_stack.tif", overwrite = TRUE)
plot(dist_shore, main = "Distance to Nearest Shoreline (m)")

# Plot data and export as PNG
png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/shoredist_maxent_env_stack.png", width = 10, height = 8, units = "in", res = 300)
plot(dist_shore, main = "Distance to Nearest Shoreline (m) - UVI2_Around_STX_20250306")
dev.off()


# ⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁
# STACK VARIABLES                                                               
# ⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁
env_stack <- c(bathy_1km, slope_1km, dist_shore, sst_1km, sss_1km, chl_1km)
print(env_stack)
# class       : SpatRaster 
# size        : 239, 328, 6  (nrow, ncol, nlyr)
# resolution  : 1000, 1000  (x, y)
# extent      : 181926.6, 509926.6, 1838105, 2077105  (xmin, xmax, ymin, ymax)
# coord. ref. : NAD83 / UTM zone 20N (EPSG:26920) 
# source(s)   : memory
# names       : bathymetry,    slope, dist_shore,      SST,     SSS,   Chl_log 
# min values  :     -32768,  0.00000,        0.0, 26.80055, 35.9955, -2.996236 
# max values  :          0, 86.57863,   150720.2, 27.68863, 36.9508,  4.534241 

# export individual layers
out_dir <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files/"
writeRaster(bathy_1km,   paste0(out_dir, "bathy_1km_UTM20N.tif"),    overwrite = TRUE)
writeRaster(slope_1km,   paste0(out_dir, "slope_1km_UTM20N.tif"),    overwrite = TRUE)
writeRaster(dist_shore,  paste0(out_dir, "distshore_1km_UTM20N.tif"), overwrite = TRUE)
writeRaster(sst_1km,     paste0(out_dir, "sst_1km_UTM20N.tif"),      overwrite = TRUE)
writeRaster(sss_1km,     paste0(out_dir, "sss_1km_UTM20N.tif"),      overwrite = TRUE)
writeRaster(chl_1km,     paste0(out_dir, "chllog_1km_UTM20N.tif"),  overwrite = TRUE)

# Plot stack and export as PNG
png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/maxent_env_stack_1km_UTM20N.png", width = 10, height = 8, units = "in", res = 300)
plot(env_stack)
dev.off()


# 𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈
# CORRELTATIONS                                                                 
# 𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈𖧈
# Extract values from stack (*ocean pixels only, no NA)
env_df <- as.data.frame(env_stack, na.rm = TRUE)
head(env_df)
#             bathymetry    slope     dist_shore  SST       SSS       Chl_log
# 330         0             0.00000   31702.74    27.21686  36.08340  -2.615798
# 331         0             10.48407  31697.61    27.21494  36.08496  -2.618876
# 332         0             71.64902  31719.79    27.21302  36.08698  -2.622210
# 333         0             81.88838  31771.80    27.21223  36.08899  -2.625636
# 334         0             83.96839  31855.14    27.21320  36.09101  -2.630769
# 335         0             84.25493  31949.86    27.21594  36.09303  -2.637883
nrow(env_df)
# [1] 75736

# Correlation matrix
cor_matrix <- cor(env_df, use = "pairwise.complete.obs", method = "pearson")
round(cor_matrix, 3)
#                 bathymetry   slope      dist_shore   SST     SSS     Chl_log
# bathymetry      1.000      -0.540      -0.106       -0.088  0.064  -0.273
# slope          -0.540       1.000      -0.125       -0.078 -0.020   0.354
# dist_shore     -0.106      -0.125       1.000        0.606 -0.394  -0.297
# SST            -0.088      -0.078       0.606        1.000 -0.585   0.203
# SSS             0.064      -0.020      -0.394       -0.585  1.000  -0.109
# Chl_log        -0.273       0.354      -0.297        0.203 -0.109   1.000

# Visualize correlation matrix and export as PNG
corrplot(cor_matrix, method = "number", type = "upper", 
         tl.col = "black", tl.cex = 0.9)

png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/correlation_matrix_maxent_env_stack.png", width = 8, height = 8, units = "in", res = 300)
corrplot(cor_matrix, method = "number", type = "upper", tl.col = "black", tl.cex = 0.9)
dev.off()

# ******************************************************************************
# ******************************************************************************
# Correlations to flag (|r| near 0.7):
#     dist_shore × SST: 0.61 — moderate collinearity
#     SST × SSS: -0.58 — moderate collinearity
#     bathymetry × slope: -0.54 (expected)
# NOT dropping any variables because both vars in highest correlation (dist_shore × SST) have distinct ecological relevance for cetacean distributions
# ******************************************************************************
# ******************************************************************************

# Export final stack
writeRaster(env_stack, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/maxent_env_stack_1km_UTM20N.tif", overwrite = TRUE)
