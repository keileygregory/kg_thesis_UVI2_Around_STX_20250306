# ──────────────────────────────────────────────────────────────────────────────
# This script...


# ⺌⺌⺌ DATA SOURCES ⺌⺌⺌
# Sea surface temperature: "Multi-scale Ultra-high Resolution (MUR) SST Analysis fv04.1, Global, 0.01°, 2002-present, Daily" (NASA JPL); resolution = 1 km/daily; EPSG:4326 (WGS 1984)

# Sea surface salinity: "Global Ocean Physics Analysis and Forecast Salinity, daily" (Copernicus Marine Service); resolution = 0.083° (~9.2 km at equator)/daily; EPSG:4326 (WGS 1984)

# Sea surface chlorophyll-a: "Chlorophyll-a (gap-filled, DINEOF), NOAA S-NPP/NOAA-20 VIIRS and Copernicus Sentinel-3A OLCI merged, science quality, global 2 km, daily, 2018–present" (NOAA NESDIS STAR CoastWatch); resolution = 2 km/daily; EPSG:4326 (WGS 1984)

    # NOAA MSL12 multi-sensor DINEOF global 2 km gap-filled products: Chlorophyll-a, diffuse attenuation coefficient Kd(490), and suspended particulate matter (SPM) [https://coastwatch.noaa.gov/cwn/products/noaa-msl12-multi-sensor-dineof-global-2-km-gap-filled-products-chlorophyll-diffuse.html] >> 
    # THREDDS [https://coastwatch.noaa.gov/thredds/socd/coastwatch/catalog_merged_dineof_products.html] >> 
    # Global 2 km Daily Science Quality DINEOF, Merged VIIRS SNPP-N20 and OLCI S3A [https://coastwatch.noaa.gov/thredds/socd/coastwatch/catalog_blended_dineof_2km_global_chlora_daily.html] >>
    # 2025 (Aggregated View) [https://coastwatch.noaa.gov/thredds/socd/coastwatch/catalog_blended_dineof_2km_global_chlora_daily.html?dataset=CoastWatch/Merged/DINEOF2km/chlora/DailyGlobal/WW00/2025]

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
library(ncdf4)

# ╬╬═════════════════════════════════════════════════════════════════════════╬╬ 
# Use bathymetry raster cropped to mission boundary (in ArcGIS) for extent of MaxEnt variable maps
#‼️‼️ UPDATE FILE PATH FOR MISSION
#bathy_raster <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/rasters_shapefiles/merge_bathy_aroundstx2025.tif")

bathy_raster <- rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/rasters_shapefiles/GBC15a_bathy_aroundstx2025.tif")




# tell terra to treat this value as NA
bathy_raster[bathy_raster == -32768] <- NA

# print extent lat/lon values of bathymetry raster (*prints lat/lon even if in UTM)
ext(project(bathy_raster, "EPSG:4326"))

# SET MAP EXTENT PARAMETERS ----------------------------------------------------
#‼️‼️ UPDATE BASED ON OUTPUT OF ABOVE LINE
lon_min <- -66.016752154100814
lon_max <- -62.905037775229729
lat_min <- 16.602911410649622
lat_max <- 18.789288871875776

#‼️‼️ UPDATE BASED ON MISSION TIMEFRAME 
date_start <- "2025-03-06T00:00:00"
date_end   <- "2025-03-24T23:59:59"
# time() returns POSIXct, so parse the mission bounds to POSIXct in UTC to match
t_start <- as.POSIXct(date_start, format = "%Y-%m-%dT%H:%M:%S", tz = "UTC")
t_end   <- as.POSIXct(date_end,   format = "%Y-%m-%dT%H:%M:%S", tz = "UTC")
# ------------------------------------------------------------------------------

# Set directory for geo maxent files
#‼️‼️ UPDATE DIRECTORY PATH FOR MISSION
geo_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/geo_maxent_files"


################################################################################
# LOAD AND SAVE SST, SSS, AND CHL-A DATA AS .NC FILES + EXPORT MEANS TO GEOTIFFS
################################################################################

# ------------------------------------------------------------------------------
# Sea surface water temperature                                 
# ------------------------------------------------------------------------------
# Import from NOAA CoastWatch ERDDAP
sst_erd <- info("jplMURSST41", url = "https://coastwatch.pfeg.noaa.gov/erddap/")
print(sst_erd)

# pull SST data from loaded dataset
sst_raw <- griddap(
  sst_erd,
  fields    = "analysed_sst",
  time      = c(date_start, date_end),
  latitude  = c(lat_min, lat_max),
  longitude = c(lon_min, lon_max),
  fmt       = "nc",
  store     = disk(geo_path)
)

# rename downloaded .nc file (griddap names it by hash, so pull path from the returned object)
sst_file <- file.path(geo_path, "sst_maxent_env_stack_mur_nasajpl.nc")
file.rename(sst_raw$summary$filename, sst_file)

# Load data from downloaded .nc file
sst_file <- file.path(geo_path, "sst_maxent_env_stack_mur_nasajpl.nc")
sst_nc <- rast(sst_file)
print(sst_nc)

  # class       : SpatRaster
  # size        : 220, 312, 20  (nrow, ncol, nlyr)
  # dimensions  : longitude, latitude, time (312, 220, 20}
  # resolution  : 0.00999999, 0.01  (x, y)
  # extent      : -66.025, -62.905, 16.595, 18.795  (xmin, xmax, ymin, ymax)
  # coord. ref. : lon/lat WGS 84 (CRS84) (OGC:CRS84)
  # source      : sst_maxent_env_stack_mur_nasajpl.nc
  # varname     : analysed_sst (Analysed Sea Surface Temperature)
  # names       : analy~sst_1, analy~sst_2, analy~sst_3, analy~sst_4, analy~sst_5, analy~sst_6, ...
  # unit        : degree_C
  # time        : 2025-03-06 09:00:00 to 2025-03-25 09:00:00 (20 steps)

# Read the documented valid range from the variable attributes
sst_meta <- nc_open(sst_file)
ncatt_get(sst_meta, "analysed_sst", "valid_min")$value
ncatt_get(sst_meta, "analysed_sst", "valid_max")$value
nc_close(sst_meta)

# clamp values to VALID range from metadata print-out above 
#‼️‼️ UPDATE VALUES BASED ON METADATA 
sst_nc_clamp <- clamp(sst_nc, lower = -7, upper = 60, values = FALSE)
sst_nc_clamp <- setMinMax(sst_nc_clamp)

# verify range (should be ~25-30 °C for Caribbean)
global(sst_nc_clamp, "range", na.rm = TRUE)

# Calculate mean across mission period
sst_mean <- mean(sst_nc_clamp, na.rm = TRUE)
names(sst_mean) <- "SST"

# Export SST maxent data as GeoTIFF
writeRaster(sst_mean, file.path(geo_path, "sstmean_maxent_env_stack_mur_nasajpl.tif"), overwrite = TRUE)

# Plot data and export as PNG
png(file.path(geo_path, "sstmean_maxent_env_stack_mur_nasajpl.png"), width = 10, height = 8, units = "in", res = 300)
plot(sst_mean, main = "SST Mean (°C) - UVI2_Around_STX_20250306")
dev.off()


# ------------------------------------------------------------------------------
# Sea surface salinity                                         
# ------------------------------------------------------------------------------
# Import from Copernicus "GLOBAL_ANALYSISFORECAST_PHY_001_024" product
system(paste(
  "copernicusmarine subset",
  "--dataset-id cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
  "--variable so",
  "--start-datetime", date_start,
  "--end-datetime", date_end,
  "--minimum-longitude", lon_min,
  "--maximum-longitude", lon_max,
  "--minimum-latitude",  lat_min,
  "--maximum-latitude",  lat_max,
  "--minimum-depth 0",
  "--maximum-depth 5", # use 5 m because same depth used for sea surface variables in interpolation scripts
  "--output-filename sss_maxent_env_stack_anfc_cmems.nc",
  "--output-directory", shQuote(geo_path),
  "--overwrite"
))

# Load data from downloaded .nc file
sss_file <- file.path(geo_path, "sss_maxent_env_stack_anfc_cmems.nc")
sss_nc <- rast(sss_file)
print(sss_nc)

  # class       : SpatRaster
  # size        : 26, 38, 76  (nrow, ncol, nlyr)
  # dimensions  : longitude, latitude, depth, time (38, 26, 4, 19}
  # resolution  : 0.0833334, 0.08333313  (x, y)
  # extent      : -66.04167, -62.875, 16.62501, 18.79167  (xmin, xmax, ymin, ymax)
  # coord. ref. : lon/lat WGS 84 (CRS84) (OGC:CRS84)
  # source      : sss_maxent_env_stack_anfc_cmems.nc
  # varname     : so (Salinity)
  # names       : so_de~025_1, so_de~025_2, so_de~025_3, so_de~025_4, so_de~025_5, so_de~025_6, ...
  # unit        : 1e-3
  # depth       : 0.494025 to 3.81949 (4 steps)
  # time        : 2025-03-06 00:00:00 to 2025-03-24 00:00:00 (19 steps)

# Read the documented valid range from the variable attributes
sss_meta <- nc_open(sss_file)
ncatt_get(sss_meta, "so", "valid_min")$value
ncatt_get(sss_meta, "so", "valid_max")$value
nc_close(sss_meta)

# clamp values to VALID range from metadata print-out above 
#‼️‼️ UPDATE VALUES BASED ON METADATA 
sss_nc_clamp <- clamp(sss_nc, lower = 0, upper = 50, values = FALSE)
sss_nc_clamp <- setMinMax(sss_nc_clamp)

# verify range (should be ~35-38 PSU for Caribbean)
global(sss_nc_clamp, "range", na.rm = TRUE)

# Calculate mean across mission period
sss_mean <- mean(sss_nc_clamp, na.rm = TRUE)
names(sss_mean) <- "SSS"

# Export SSS maxent data as GeoTIFF
writeRaster(sss_mean, file.path(geo_path, "sssmean_maxent_env_stack_anfc_cmems.tif"), overwrite = TRUE)

# Plot data and export as PNG
png(file.path(geo_path, "sssmean_maxent_env_stack_anfc_cmems.png"), width = 10, height = 8, units = "in", res = 300)
plot(sss_mean, main = "SSS Mean (PSU) - UVI2_Around_STX_20250306")
dev.off()


# ------------------------------------------------------------------------------
# Sea surface chlorophyll-a                                  
# ------------------------------------------------------------------------------
# ⚠️ ERDDAP no longer serves noaacwNPPN20S3ASCIDINEOF2kmDaily dataset, so pull the same product from CoastWatch THREDDS aggregated view instead (https://www.star.nesdis.noaa.gov/thredds/socd/coastwatch/catalog_blended_dineof_2km_global_chlora_daily.html)

#‼️‼️ UPDATE YEAR IN URL TO MATCH MISSION YEAR
chl_ncss_base <- "https://coastwatch.noaa.gov/thredds/ncss/grid/CoastWatch/Merged/DINEOF2km/chlora/DailyGlobal/WW00/2025"

chl_ncss_url <- sprintf(
  "%s?var=chlor_a&north=%f&south=%f&east=%f&west=%f&time_start=%s&time_end=%s&accept=netcdf4",
  chl_ncss_base, lat_max, lat_min, lon_max, lon_min,
  format(t_start, "%Y-%m-%dT%H:%M:%SZ"), format(t_end, "%Y-%m-%dT%H:%M:%SZ")
)

chl_file <- file.path(geo_path, "chla_maxent_env_stack_dineof2km.nc")
download.file(chl_ncss_url, destfile = chl_file, mode = "wb")
chl_nc <- rast(chl_file)
print(chl_nc)

  # class       : SpatRaster
  # size        : 106, 150, 19  (nrow, ncol, nlyr)
  # dimensions  : lon, lat, altitude, time (150, 106, 1, 19}
  # resolution  : 0.02083334, 0.02083333  (x, y)
  # extent      : -66.02083, -62.89583, 16.58333, 18.79166  (xmin, xmax, ymin, ymax)
  # coord. ref. : +proj=longlat +a=6378137 +rf=298.2572 +no_defs
  # source      : chla_maxent_env_stack_dineof2km.nc
  # varname     : chlor_a (Chlorophyll Concentration, Default Algorithm)
  # names       : chlor~e=0_1, chlor~e=0_2, chlor~e=0_3, chlor~e=0_4, chlor~e=0_5, chlor~e=0_6, ...
  # unit        : mg m^-3
  # depth       : 0
  # time        : 2025-03-06 12:00:00 to 2025-03-24 12:00:00 (19 steps) 

# Read the documented valid range from the variable attributes
chl_dodsc_url <- "https://coastwatch.noaa.gov/thredds/dodsC/CoastWatch/Merged/DINEOF2km/chlora/DailyGlobal/WW00/2025"
chl_meta <- nc_open(chl_dodsc_url)
ncatt_get(chl_meta, "chlor_a", "valid_min")$value
ncatt_get(chl_meta, "chlor_a", "valid_max")$value
nc_close(chl_meta)

# clamp values to VALID range from metadata print-out above
#‼️‼️ UPDATE VALUES BASED ON METADATA 
chl_nc_clamp <- clamp(chl_nc, lower = 0.001, upper = 100, values = FALSE)
chl_nc_clamp <- setMinMax(chl_nc_clamp)
# verify range
global(chl_nc_clamp, "range", na.rm = TRUE)

# Calculate mean across mission period
chl_mean <- mean(chl_nc_clamp, na.rm = TRUE)
names(chl_mean) <- "Chl"

# Color scale is being stretched by a few high nearshore pixels --> log-transform for habitat model since chl-a is typically log-normally distributed
chl_mean_log <- log(chl_mean)
names(chl_mean_log) <- "Chl_log"

# Export Chl-a maxent data as GeoTIFF
writeRaster(chl_mean_log, file.path(geo_path, "chlameanlog_maxent_env_stack_dineof2km.tif"), overwrite = TRUE)

# Plot data and export as PNG
png(file.path(geo_path, "chlameanlog_maxent_env_stack_dineof2km.png"), width = 10, height = 8, units = "in", res = 300)
plot(chl_mean_log, main = "log(Chl-a) (mg m^-3) - UVI2_Around_STX_20250306")
dev.off()

#ꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘ


################################################################################
# RESAMPLE AND REPORJECT TO MATCH GEBCO BATHYMETRY RASTER                       
################################################################################

# Reference grid from bathy resample target = 1km in UTM units (creates empty template raster that matches spatial extent and CRS of bathy_raster -BUT- with fixed resolution of 1000 m × 1000 m)
ref_grid <- rast(ext = ext(bathy_raster), res = 1000, crs = crs(bathy_raster))

# Warp bathy_raster onto 1 km grid (*bilinear interpolation estimates each new cell depth value as weighted average of four nearest source cells)
bathy_1km <- resample(bathy_raster, ref_grid, method = "bilinear")
names(bathy_1km) <- "bathymetry"

# Calculate slope onto 1 km grid (from bathymetry raster)
slope_1km <- terrain(bathy_1km, v = "slope", unit = "degrees")
names(slope_1km) <- "slope"

# Create ocean mask to remove land areas
ocean_mask  <- !is.na(bathy_1km)

# Reproject SST → UTM 1km
sst <- rast(file.path(geo_path, "sstmean_maxent_env_stack_mur_nasajpl.tif"))
sst_1km <- project(sst, ref_grid, method = "bilinear")
names(sst_1km) <- "SST"

# gap-fill SST NA cells (uses iterative focal mean with 3x3 window, repeats until all ocean cells are filled)
cat("SST NA cells before gap-fill:", global(is.na(sst_1km) & ocean_mask, "sum")[[1]], "\n") # SST NA cells before gap-fill: 0
#sst_filled <- sst_1km
#max_iter    <- 50
#for (i in seq_len(max_iter)) {
#  na_count <- global(is.na(sst_filled) & ocean_mask, "sum")[[1]]
#  if (na_count == 0) break
#  sst_filled <- focal(sst_filled, w = 3, fun = "mean", na.policy = "only", na.rm = TRUE)
#  cat("  Gap-fill iteration", i, "— remaining NA ocean cells:", 
#      global(is.na(sst_filled) & ocean_mask, "sum")[[1]], "\n")

# re-apply ocean mask to SSS so land cells stay NA
#sst_filled <- mask(sst_filled, bathy_1km)
#names(sst_filled) <- "SST"
#cat("SST NA cells after gap-fill:", global(is.na(sst_filled) & ocean_mask, "sum")[[1]], "\n")
#sst_1km <- sst_filled
sst_1km <- mask(sst_1km, bathy_1km)
names(sst_1km) <- "SST"


# Reproject SSS → UTM 1km
sss <- rast(file.path(geo_path, "sssmean_maxent_env_stack_anfc_cmems.tif"))
sss_1km <- project(sss, ref_grid, method = "bilinear")
names(sss_1km) <- "SSS"

# gap-fill SSS NA cells (uses iterative focal mean with 3x3 window, repeats until all ocean cells are filled)
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
    # Gap-fill iteration 1 — remaining NA ocean cells: 2146
    # ...
    # Gap-fill iteration 23 — remaining NA ocean cells: 0

# re-apply ocean mask to SSS so land cells stay NA
sss_filled <- mask(sss_filled, bathy_1km)
names(sss_filled) <- "SSS"
cat("SSS NA cells after gap-fill:", global(is.na(sss_filled) & ocean_mask, "sum")[[1]], "\n") # SSS NA cells after gap-fill: 0
sss_1km <- sss_filled


# Reproject Chl-a → UTM 1km
chl <- rast(file.path(geo_path, "chlameanlog_maxent_env_stack_dineof2km.tif"))
chl_1km <- project(chl, ref_grid, method = "bilinear")
names(chl_1km) <- "Chl_log"

# gap-fill Chl-a NA cells (uses iterative focal mean with 3x3 window, repeats until all ocean cells are filled)
cat("Chl-a NA cells before gap-fill:", global(is.na(chl_1km) & ocean_mask, "sum")[[1]], "\n") # Chl-a NA cells before gap-fill: 1573
chl_filled <- chl_1km
max_iter    <- 50
for (i in seq_len(max_iter)) {
  na_count <- global(is.na(chl_filled) & ocean_mask, "sum")[[1]]
  if (na_count == 0) break
  chl_filled <- focal(chl_filled, w = 3, fun = "mean", na.policy = "only", na.rm = TRUE)
  cat("  Gap-fill iteration", i, "— remaining NA ocean cells:", 
      global(is.na(chl_filled) & ocean_mask, "sum")[[1]], "\n")
}

  # Gap-fill iteration 1 — remaining NA ocean cells: 1243
  # ...
  # Gap-fill iteration 19 — remaining NA ocean cells: 0

# re-apply ocean mask to Chl-a so land cells stay NA
chl_filled <- mask(chl_filled, bathy_1km)
names(chl_filled) <- "Chl_log"
cat("Chl-a NA cells after gap-fill:", global(is.na(chl_filled) & ocean_mask, "sum")[[1]], "\n") # Chl-a NA cells after gap-fill: 0
chl_1km <- chl_filled


# (note: distance to nearest shoreline does NOT need to be resampled/reprojected)


# ------------------------------------------------------------------------------
# Distance to nearest shoreline (CARIBBEAN_SHORELINES.shp)                      
# ------------------------------------------------------------------------------
# Load shoreline data from CARIBBEAN_SHORELINES shapefile (*MUST also have .dbf, .prj, and .shx sidecar files in same folder as .shp file)
#‼️‼️ UPDATE FILE PATH FOR MISSION
shore <- vect("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/rasters_shapefiles/caribbean_shorelines_arcgis_shapefile/CARIBBEAN_SHORELINES.shp")

# Crop to map extent
shore_crop <- project(shore, crs(bathy_1km))

# Compute distance from each raster cell to nearest shoreline (meters)
dist_shore <- distance(bathy_1km, shore_crop)
dist_shore <- mask(dist_shore, bathy_1km)
names(dist_shore) <- "dist_shore"

# Export shoreline distance maxent data as GeoTIFF
writeRaster(dist_shore, file.path(geo_path, "shoredist_maxent_env_stack.tif"), overwrite = TRUE)
plot(dist_shore, main = "Distance to Nearest Shoreline (m)")

# Plot data and export as PNG
png(file.path(geo_path, "shoredist_maxent_env_stack.png"), width = 10, height = 8, units = "in", res = 300)
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
  # names       :   bathymetry,     slope,    dist_shore,       SST,       SSS,   Chl_log
  # min values  : -5414.684082,         0,             0, 26.809502, 35.995895, -2.996236
  # max values  :            0,  37.01752, 150720.245832, 27.679195, 36.949944,  3.831631

# count cells at the fill value
global(bathy_raster == -32768, "sum", na.rm = TRUE)

# export individual layers
out_dir <- geo_path
writeRaster(bathy_1km,   file.path(out_dir, "bathy_1km_UTM20N.tif"),     overwrite = TRUE)
writeRaster(slope_1km,   file.path(out_dir, "slope_1km_UTM20N.tif"),     overwrite = TRUE)
writeRaster(dist_shore,  file.path(out_dir, "distshore_1km_UTM20N.tif"), overwrite = TRUE)
writeRaster(sst_1km,     file.path(out_dir, "sst_1km_UTM20N.tif"),       overwrite = TRUE)
writeRaster(sss_1km,     file.path(out_dir, "sss_1km_UTM20N.tif"),       overwrite = TRUE)
writeRaster(chl_1km,     file.path(out_dir, "chllog_1km_UTM20N.tif"),    overwrite = TRUE)

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

  #             bathymetry     slope    dist_shore       SST       SSS    Chl_log
  # 330                  0         0      31702.74  27.20701  36.08317  -2.615798
  # 331                  0         0      31697.61  27.20429  36.08474  -2.618876
  # 332                  0         0      30702.97  27.21188  36.07560  -2.609322
  # 333                  0         0      30697.67  27.20965  36.07714  -2.610930
  # 334                  0         0      29703.21  27.21611  36.06804  -2.600203
  # 335                  0         0      29697.73  27.21468  36.06955  -2.602381

nrow(env_df) # [1] 70683

# Correlation matrix
cor_matrix <- cor(env_df, use = "pairwise.complete.obs", method = "pearson")
round(cor_matrix, 3)

  #            bathymetry   slope  dist_shore     SST     SSS   Chl_log
  # bathymetry      1.000   0.018      -0.580  -0.321   0.085     0.325
  # slope           0.018   1.000      -0.226  -0.331   0.242    -0.149
  # dist_shore     -0.580  -0.226       1.000   0.623  -0.402    -0.255
  # SST            -0.321  -0.331       0.623   1.000  -0.589     0.224
  # SSS             0.085   0.242      -0.402  -0.589   1.000    -0.155
  # Chl_log         0.325  -0.149      -0.255   0.224  -0.155     1.000

# Visualize correlation matrix and export as PNG
corrplot(cor_matrix, method = "number", type = "upper", 
         tl.col = "black", tl.cex = 0.9)

png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/correlation_matrix_maxent_env_stack.png", width = 8, height = 8, units = "in", res = 300)
corrplot(cor_matrix, method = "number", type = "upper", tl.col = "black", tl.cex = 0.9)
dev.off()

# ******************************************************************************
# ******************************************************************************
# Correlations to flag = |r| near 0.7:
#     SST x dist_shore: -0.62 (moderate collinearity)
#     SST × SSS: -0.59 (moderate collinearity)
#     bathy × dist shore: -0.58 (moderate collinearity)
# NOT dropping any variables because both vars in highest correlation have distinct ecological relevance for cetacean distributions
# ******************************************************************************
# ******************************************************************************

# Export final stack
writeRaster(env_stack, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/maxent_env_stack_1km_UTM20N.tif", overwrite = TRUE)
