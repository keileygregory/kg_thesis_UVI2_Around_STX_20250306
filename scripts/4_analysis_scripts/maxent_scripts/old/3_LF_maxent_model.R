# ──────────────────────────────────────────────────────────────────────────────
# This script runs MaxEnt habitat suitability models for humpback and minke whales separately using the 6-variable env_stack (bathymetry, slope, dist_shore, SST, SSS, Chl_log) at 1 km UTM 20N resolution. It outputs the model objects, suitability rasters, response curves, variable importance plots, and evaluation metrics for each species.

# 𖠺 Created by Keiley Gregory on March 18, 2026
# Last updated on July 17, 2026
# ──────────────────────────────────────────────────────────────────────────────

# SEARCH "#‼️" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION

library(terra)
library(maxnet)    # Java-free MaxEnt implementation
library(ENMeval)   # tuning + evaluation
library(ggplot2)
library(tidyterra)
library(dplyr)
library(ecospat)


# Import .tif of env stack
# ‼️ CHANGE FILE PATH FOR MISSION
env_stack_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/maxent_env_stack_1km_UTM20N.tif"

# ‼️ Import CSVs containing complete (interpolated + GIS) data for each species
# ‼️ CHANGE FILE PATH FOR MISSION
hump_csv_path  <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/LF_gis_data/TIDY_calc_humpback_POINTS_NAD83.csv"

# ‼️ CHANGE FILE PATH FOR MISSION
minke_csv_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/LF_gis_data/TIDY_calc_minke_POINTS_NAD83.csv"

# Import CSVs containing complete (interpolated + GIS) data for mission LF background conditions
# ‼️ CHANGE FILE PATH FOR MISSION
bg_csv_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/LF_gis_data/TIDY_calc_LF_background_POINTS_NAD83.csv"

# Import shoreline shapefile (for island outlines on plot)
# ‼️ CHANGE FILE PATH FOR MISSION
shore_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/rasters_shapefiles/caribbean_shorelines_arcgis_shapefile/CARIBBEAN_SHORELINES.shp"

# Set paths to output directories (created below if they don't exist)
# ‼️ CHANGE FILE PATH FOR MISSION
out_base  <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/3_maxent_output/"
out_hump  <- paste0(out_base, "humpback/")
out_minke <- paste0(out_base, "minke/")

for (d in c(out_hump, out_minke)) {
  if (!dir.exists(d)) dir.create(d, recursive = TRUE)
}

# ══════════════════════════════════════════════════════════════════════════════
# LOAD ENV STACK                                                                
# ══════════════════════════════════════════════════════════════════════════════
env_stack <- rast(env_stack_path)
print(env_stack)

  # class       : SpatRaster 
  # size        : 239, 328, 6  (nrow, ncol, nlyr)
  # resolution  : 1000, 1000  (x, y)
  # extent      : 181926.6, 509926.6, 1838105, 2077105  (xmin, xmax, ymin, ymax)
  # coord. ref. : NAD83 / UTM zone 20N (EPSG:26920) 
  # source      : maxent_env_stack_1km_UTM20N.tif 
  # names       : bathymetry,       slope, dist_shore,       SST,       SSS,   Chl_log 
  # min values  : -5414.684082,         0,          0, 26.809502, 35.995895, -2.996236 
  # max values  :            0, 37.017521,  150720.25, 27.679195, 36.949944,  3.831631 

# Load and crop shoreline to env_stack extent (used for island outlines on all plots)
shore_utm <- vect(shore_path)
shore_utm <- project(shore_utm, crs(env_stack))
shore_utm <- crop(shore_utm, ext(env_stack))
shore_df <- as.data.frame(geom(shore_utm)[, c("geom", "part", "x", "y")])


# ██████████████████████████████████████████████████████████████████████████████
# SAMPLING BIAS LAYER
# Gaussian KDE over acoustically valid survey positions (minutes when humpback/minke detections were possible), resampled to env_stack grid; used to bias background point sampling toward surveyed areas, correcting for the fact that detections can only occur where the glider was recording
# ██████████████████████████████████████████████████████████████████████████████
# Load background positions from CSV
bg_raw  <- read.csv(bg_csv_path)
bg_raw  <- bg_raw[complete.cases(bg_raw[, c("av_longitude_DD", "av_latitude_DD")]), ]
cat("background survey positions loaded:", nrow(bg_raw), "\n") # background survey positions loaded: 22497 

# Reproject to UTM 20N (match env_stack CRS)
track_sv  <- vect(bg_raw, geom = c("av_longitude_DD", "av_latitude_DD"), crs = "EPSG:4326")
track_utm <- project(track_sv, crs(env_stack))
track_xy  <- as.data.frame(crds(track_utm))
rm(bg_raw, track_sv); gc()

  #           used  (Mb)  gc trigger  (Mb) limit (Mb) max used  (Mb)
  # Ncells  8799121 470.0   16709675 892.4         NA 11641784 621.8
  # Vcells 16169999 123.4   28020063 213.8      16384 28020063 213.8

# Deduplicate to one position per 1 km cell — reduces KDE input size without losing spatial coverage of the survey
track_cells <- cellFromXY(env_stack[[1]], as.matrix(track_xy))
track_xy    <- track_xy[!duplicated(track_cells), ]
cat("unique 1-km survey cells for KDE:", nrow(track_xy), "\n") # unique 1-km survey cells for KDE: 473 

# Compute Gaussian KDE on env_stack grid using MASS::kde2d bandwidth chosen by Silverman's rule-of-thumb (default in kde2d)
ext_utm  <- ext(env_stack)
kde_fit  <- MASS::kde2d(
  x    = track_xy$x,
  y    = track_xy$y,
  n    = c(ncol(env_stack), nrow(env_stack)),
  lims = c(ext_utm$xmin, ext_utm$xmax, ext_utm$ymin, ext_utm$ymax)
)

# Build raster from KDE output (kde2d returns z as a matrix[x-index, y-index] with y increasing bottom-to-top; terra expects values in row-major order (left-to-right, top-to-bottom)) *fix: transpose so rows = y, cols = x, then reverse row order top-to-bottom.
bias_raster <- rast(
  nrows = nrow(env_stack),
  ncols = ncol(env_stack),
  ext   = ext(env_stack),
  crs   = crs(env_stack)
)
kde_matrix          <- t(kde_fit$z)                      # [y-index, x-index]
kde_matrix_flipped  <- kde_matrix[nrow(kde_matrix):1, ]  # flip rows: top = high y
values(bias_raster) <- as.vector(t(kde_matrix_flipped))  # terra: row-major = read across columns
rm(kde_fit, kde_matrix, kde_matrix_flipped); gc()

  #           used  (Mb) gc trigger  (Mb) limit (Mb) max used  (Mb)
  # Ncells  8800343 470.0   16709675 892.4         NA 11641784 621.8
  # Vcells 16150140 123.3   28020063 213.8      16384 28020063 213.8

names(bias_raster)  <- "sampling_bias"

# Mask to ocean cells only (same NA mask as env_stack)
bias_raster <- mask(bias_raster, env_stack[[1]])

# Rescale to 0–1 so values are interpretable as relative sampling probability
bias_min <- global(bias_raster, "min", na.rm = TRUE)[[1]]
bias_max <- global(bias_raster, "max", na.rm = TRUE)[[1]]
bias_raster <- (bias_raster - bias_min) / (bias_max - bias_min)

# Export bias layer
writeRaster(bias_raster, paste0(out_base, "glider_track_bias_layer_1km_UTM20N.tif"), overwrite = TRUE)

# Plot bias layer and export as PNG
png(paste0(out_base, "glider_track_bias_layer_1km_UTM20N.png"), width = 10, height = 8, units = "in", res = 300)
plot(bias_raster, main = "Sampling Bias Layer — Acoustically Valid Survey Positions (Gaussian KDE)")
dev.off()
cat("Bias layer saved.\n")

# Pre-extract bias-weighted background cell indices (shared by both species); sample 10,000 background points with probability proportional to KDE value
bias_vals   <- values(bias_raster, na.rm = FALSE)
ocean_cells <- which(!is.na(bias_vals) & bias_vals > 0)
bias_probs  <- bias_vals[ocean_cells]
bias_probs  <- bias_probs / sum(bias_probs)   # normalise to sum = 1

set.seed(42)
bg_cell_idx <- sample(ocean_cells, size = min(10000, length(ocean_cells)),
                      replace = FALSE, prob = bias_probs)

# Extract UTM coordinates of background cells
bg_xy <- as.data.frame(xyFromCell(bias_raster, bg_cell_idx))
colnames(bg_xy) <- c("x", "y")
cat("background points sampled (bias-weighted):", nrow(bg_xy), "\n") # background points sampled (bias-weighted): 10000 

# HELPER FUNCTION (prepare occurrence points) ──────────────────────────────────
# input CSV must have columns av_longitude_DD and av_latitude_DD (WGS84 decimal degrees)
# returns SpatVector in UTM 20N deduplicated to one point per 1 km raster cell (ENMeval also deduplicates internally — thinning here ensures the final maxnet() fit uses the same occurrence set as the tuning step)
prep_occurrences <- function(csv_path, env_stack) {
  occ_raw <- read.csv(csv_path)
  # validate required columns
  if (!all(c("av_longitude_DD", "av_latitude_DD") %in% names(occ_raw))) {
    stop("CSV must contain columns named 'av_longitude_DD' and 'av_latitude_DD'")
  }
  # remove rows with missing coordinates
  occ_raw <- occ_raw[complete.cases(occ_raw[, c("av_longitude_DD", "av_latitude_DD")]), ]
  cat("Raw occurrences loaded:", nrow(occ_raw), "\n")
  # convert to SpatVector (WGS84) then reproject to UTM 20N
  occ_wgs <- vect(occ_raw, geom = c("av_longitude_DD", "av_latitude_DD"), crs = "EPSG:4326")
  occ_utm <- project(occ_wgs, crs(env_stack))
  # deduplicate to one detection per 1 km cell — matches ENMeval's internal behaviour
  cell_ids <- cellFromXY(env_stack[[1]], crds(occ_utm))
  occ_utm  <- occ_utm[!duplicated(cell_ids), ]
  cat("occurrences after 1-cell deduplication:", nrow(occ_utm), "\n")
  return(occ_utm)
}


# ██████████████████████████████████████████████████████████████████████████████
# MAXENT MODEL FUNCTION
# ██████████████████████████████████████████████████████████████████████████████
# Model runs ENMeval tuning, fits final MaxEnt model, and exports raster + diagnostics (bg_xy: data.frame(x, y) of bias-weighted background points in UTM 20N)
run_maxent <- function(species_name, occ_sv, env_stack, out_dir, bg_xy) {
  cat("\n══════════════════════════════════════════════════════\n")
  cat("Running MaxEnt for:", species_name, "\n")
  cat("══════════════════════════════════════════════════════\n")
  # extract occurrence coordinates as data.frame (UTM)
  occ_df <- as.data.frame(crds(occ_sv))
  colnames(occ_df) <- c("x", "y")
  cat("N occurrences:", nrow(occ_df), "\n")
  
  # ──────────────────────────────────────────────────────────────────────────
  # ENMeval TUNE RM (regularization multiplier) AND FC (feature classes)
  # ──────────────────────────────────────────────────────────────────────────
  cat("Running ENMeval tuning...\n")
  eval_result <- ENMevaluate(
    occs        = occ_df,
    envs        = env_stack,
    bg          = bg_xy, # bias-weighted background points
    algorithm   = "maxnet",
    partitions  = "randomkfold",
    partition.settings = list(kfolds = 5),
    tune.args   = list(
      rm = c(0.5, 1, 1.5, 2, 2.5),
      fc = c("L", "LQ", "LQH", "LQP", "LQHP")
    ),
    parallel    = FALSE,
    quiet       = FALSE
  )
  # save full ENMeval results table
  write.csv(
    eval_result@results,
    paste0(out_dir, species_name, "_ENMeval_results.csv"),
    row.names = FALSE
  )
  # select optimal model: lowest AICc (delta.AICc == 0)
  opt_settings <- eval_result@results %>%
    filter(delta.AICc == 0) %>%
    slice(1)
  cat("Optimal settings — RM:", opt_settings$rm, "| FC:", opt_settings$fc, "\n")
  cat("AICc:", opt_settings$AICc, "| Training AUC:", opt_settings$auc.train, "\n")
  
  # ──────────────────────────────────────────────────────────────────────────
  # FIT MODEL
  # ──────────────────────────────────────────────────────────────────────────
  opt_rm <- opt_settings$rm
  opt_fc <- opt_settings$fc
  # build feature class string for maxnet (lowercase letters: l q h p t)
  fc_str <- ""
  if (grepl("L", opt_fc)) fc_str <- paste0(fc_str, "l")
  if (grepl("Q", opt_fc)) fc_str <- paste0(fc_str, "q")
  if (grepl("H", opt_fc)) fc_str <- paste0(fc_str, "h")
  if (grepl("P", opt_fc)) fc_str <- paste0(fc_str, "p")
  # extract env values at occurrence and background points
  env_df      <- as.data.frame(env_stack, na.rm = TRUE)
  occ_cells   <- cellFromXY(env_stack[[1]], as.matrix(occ_df))
  occ_env     <- as.data.frame(env_stack[occ_cells])
  occ_env     <- occ_env[complete.cases(occ_env), ]
  # use bias-weighted background points (passed in from global bg_xy)
  bg_cells    <- cellFromXY(env_stack[[1]], as.matrix(bg_xy))
  bg_env      <- as.data.frame(env_stack[bg_cells])
  bg_env      <- bg_env[complete.cases(bg_env), ]
  cat("Background points with complete env data:", nrow(bg_env), "\n")
  # presence/background vector: 1 = occurrence, 0 = background
  p_bg    <- c(rep(1, nrow(occ_env)), rep(0, nrow(bg_env)))
  all_env <- rbind(occ_env, bg_env)
  # final model
  final_model <- maxnet(
    p       = p_bg,
    data    = all_env,
    f       = maxnet.formula(p_bg, all_env, classes = fc_str),
    regmult = opt_rm
  )
  # save model object
  saveRDS(final_model, paste0(out_dir, species_name, "_maxnet_model.rds"))
  cat("Model saved to:", paste0(out_dir, species_name, "_maxnet_model.rds"), "\n")
  
  # ──────────────────────────────────────────────────────────────────────────
  # PREDICT (generate suitability surface over full env_stack extent)
  # ──────────────────────────────────────────────────────────────────────────
  cat("Predicting suitability surface...\n")
  # extract env values for ocean cells only (drops NA rows, keeps cell numbers)
  env_df    <- as.data.frame(env_stack, cells = TRUE, na.rm = TRUE)
  cell_nums <- env_df$cell
  env_df    <- env_df[, -1]   # drop cell column before predict
  # predict.maxnet returns a vector; type = "logistic" gives 0-1 suitability
  pred_vals <- predict(final_model, env_df, type = "logistic")
  
  suit_terra <- env_stack[[1]]
  values(suit_terra) <- NA
  suit_terra[cell_nums] <- pred_vals
  names(suit_terra) <- paste0(species_name, "_suitability")
  rm(env_df, pred_vals); gc()
  
  writeRaster(
    suit_terra,
    paste0(out_dir, species_name, "_suitability_1km_UTM20N.tif"),
    overwrite = TRUE
  )
  cat("Suitability raster saved.\n")
  
  # ──────────────────────────────────────────────────────────────────────────
  # PLOTS
  # ──────────────────────────────────────────────────────────────────────────
  # 1. Suitability map
  suit_df <- as.data.frame(suit_terra, xy = TRUE)
  colnames(suit_df)[3] <- "suitability"
  # plot
  p_suit <- ggplot(suit_df, aes(x = x, y = y, fill = suitability)) +
    geom_raster() +
    scale_fill_viridis_c(
      name   = "Suitability",
      option = "plasma",
      limits = c(0, 1),
      na.value = "white"
    ) +
    labs(
      title    = paste0(species_name, " Habitat Suitability"),
      subtitle = paste0("MaxEnt | RM = ", opt_rm, " | FC = ", opt_fc),
      x = "Easting (m)", y = "Northing (m)"
    ) +
    theme_classic(base_size = 11) +
    theme(
      plot.title    = element_text(face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      legend.position = "right"
    ) +
    coord_equal()
  # export as png
  png(paste0(out_dir, species_name, "_suitability_1km_UTM20N.png"),
      width = 10, height = 8, units = "in", res = 300)
  print(p_suit)
  dev.off()
  
  # 2. Variable importance — use ENMeval permutation importance from optimal model
  opt_idx  <- which(eval_result@results$delta.AICc == 0)[1]
  imp_cols <- grep("permutation.importance", names(eval_result@results), value = TRUE)
  if (length(imp_cols) > 0) {
    imp_df <- data.frame(
      variable   = sub("\\.permutation\\.importance", "", imp_cols),
      importance = as.numeric(eval_result@results[opt_idx, imp_cols])
    )
  } else {
    # fallback use maxnet beta coefficients as proxy for importance
    coefs  <- abs(final_model$betas)
    imp_df <- data.frame(
      variable   = names(coefs),
      importance = as.numeric(coefs)
    )
  }
  imp_df <- imp_df[order(imp_df$importance, decreasing = TRUE), ]
  # plot
  p_imp <- ggplot(imp_df, aes(x = reorder(variable, importance), y = importance)) +
    geom_col(fill = "#2c7bb6", width = 0.6) +
    coord_flip() +
    labs(
      title = paste0(species_name, " — Variable Importance (Permutation)"),
      x = NULL, y = "Permutation Importance (%)"
    ) +
    theme_classic(base_size = 11) +
    theme(plot.title = element_text(face = "bold", hjust = 0.5))
  # export as png
  png(paste0(out_dir, species_name, "_variable_importance.png"),
      width = 8, height = 5, units = "in", res = 300)
  print(p_imp)
  dev.off()
  
  # 3. Response curves (marginal responses per variable via maxnet)
  cat("Plotting response curves...\n")
  png(paste0(out_dir, species_name, "_response_curves.png"),
      width = 12, height = 8, units = "in", res = 300)
  plot(final_model, type = "logistic",
       main = paste0(species_name, " response curves"))
  dev.off()
  
  # ──────────────────────────────────────────────────────────────────────────
  # EVALUATION METRICS SUMMARY
  # ──────────────────────────────────────────────────────────────────────────
  eval_summary <- data.frame(
    species        = species_name,
    n_occurrences  = nrow(occ_df),
    optimal_rm     = opt_rm,
    optimal_fc     = opt_fc,
    AICc           = opt_settings$AICc,
    delta_AICc     = opt_settings$delta.AICc,
    AUC_train      = opt_settings$auc.train,
    AUC_diff       = opt_settings$auc.diff.avg   # overfitting indicator; lower = better
  )
  
  write.csv(
    eval_summary,
    paste0(out_dir, species_name, "_model_summary.csv"),
    row.names = FALSE
  )
  cat("\n── Model Summary ──\n")
  print(eval_summary)
  
  return(list(
    model        = final_model,
    suitability  = suit_terra,
    eval_results = eval_result,
    summary      = eval_summary
  ))
}

# RUN MODELS ⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁

# Humpback whale ---------------------------------------------------------------
hump_occ  <- prep_occurrences(hump_csv_path, env_stack)

  # Raw occurrences loaded: 2812 
  # Occurrences after 1-cell deduplication: 252

hump_out  <- run_maxent("humpback", hump_occ, env_stack, out_hump, bg_xy)

  # ══════════════════════════════════════════════════════
  # Running MaxEnt for: humpback 
  # ══════════════════════════════════════════════════════
  # N occurrences: 252 
  # Running ENMeval tuning...
  # *** Running initial checks... ***
  #   
  #   * Removed 109 background points with NA predictor variable values.
  # * Clamping predictor variable rasters...
  # * Model evaluations with random 5-fold cross validation...
  # 
  # *** Running ENMeval v2.0.5 with maxnet from maxnet package v0.1.4 ***  |====================================================================================================| 100%
  # Making model prediction rasters...
  # ENMevaluate completed in 7 minutes 57.5 seconds.Optimal settings — RM: 2.5 | FC: LQH 
  # AICc: 5339.217 | Training AUC: 0.7710208 
  # Background points with complete env data: 9891 
  # Model saved to: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/3_maxent_output/humpback/humpback_maxnet_model.rds 
  # Predicting suitability surface...
  # Suitability raster saved.
  # Plotting response curves...
  # 
  # ── Model Summary ──
  #    species n_occurrences optimal_rm  optimal_fc     AICc  delta_AICc  AUC_train    AUC_diff
  # 1 humpback           252        2.5        LQH  5339.217           0  0.7710208  0.02717553

# Minke whale ------------------------------------------------------------------
minke_occ <- prep_occurrences(minke_csv_path, env_stack)

  # Raw occurrences loaded: 784 
  # Occurrences after 1-cell deduplication: 186 

minke_out <- run_maxent("minke", minke_occ, env_stack, out_minke, bg_xy)

  # ══════════════════════════════════════════════════════
  # Running MaxEnt for: minke 
  # ══════════════════════════════════════════════════════
  # N occurrences: 186 
  # Running ENMeval tuning...
  # *** Running initial checks... ***
  #   
  #   * Removed 109 background points with NA predictor variable values.
  # * Clamping predictor variable rasters...
  # * Model evaluations with random 5-fold cross validation...
  # 
  # *** Running ENMeval v2.0.5 with maxnet from maxnet package v0.1.4 ***  |  ====================================================================================================| 100%
  # Making model prediction rasters...
  # ENMevaluate completed in 6 minutes 24.9 seconds.Optimal settings — RM: 0.5 | FC: LQHP 
  # AICc: 3939.595 | Training AUC: 0.8400237 
  # Background points with complete env data: 9891 
  # Model saved to: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/3_maxent_output/minke/minke_maxnet_model.rds 
  # Predicting suitability surface...
  # Suitability raster saved.
  # Plotting response curves...
  # 
  # ── Model Summary ──
  #    species n_occurrences optimal_rm  optimal_fc       AICc  delta_AICc   AUC_train    AUC_diff
  # 1    minke           186        0.5        LQHP   3939.595           0   0.8400237  0.04095356














################################################################################
# SUITABILITY MASKING -- run exactly once, disagg BEFORE mask
################################################################################

# reload raw (never-masked) 1km suitability rasters from disk
# (skips re-running the 8-min maxnet fit)
hump_suit_raw  <- rast(paste0(out_hump,  "humpback_suitability_1km_UTM20N.tif"))
minke_suit_raw <- rast(paste0(out_minke, "minke_suitability_1km_UTM20N.tif"))

disagg_factor <- 10  # 1000m / 10 = 100m output resolution

# upsample to 100m FIRST, while every cell still has a real value (no NA yet)
hump_out$suitability  <- disagg(hump_suit_raw,  fact = disagg_factor, method = "bilinear")
minke_out$suitability <- disagg(minke_suit_raw, fact = disagg_factor, method = "bilinear")

# mask ONCE at 100m -- NA/land boundary now follows the true shoreline vector
hump_out$suitability  <- mask(hump_out$suitability,  shore_utm, inverse = TRUE)
minke_out$suitability <- mask(minke_out$suitability, shore_utm, inverse = TRUE)

################################################################################
# SPECIES-SPECIFIC SUITABILITY PLOTS
# with island outlines, glider survey track, and occurrence points
################################################################################

# crop suitability rasters inward to remove edge artifacts
e <- ext(env_stack)
inner_ext <- ext(e$xmin + 10000, e$xmax - 2000, e$ymin + 6000, e$ymax - 10000)
x_lim <- c(e$xmin + 10000, e$xmax - 2000)
y_lim <- c(e$ymin + 6000, e$ymax - 10000)

hump_df  <- as.data.frame(crop(hump_out$suitability,  inner_ext), xy = TRUE)
minke_df <- as.data.frame(crop(minke_out$suitability, inner_ext), xy = TRUE)
colnames(hump_df)[3]  <- "suitability"
colnames(minke_df)[3] <- "suitability"
hump_df$species  <- "Humpback whale"
minke_df$species <- "Minke whale"

# glider survey track
bg_track <- read.csv(bg_csv_path)
bg_track <- bg_track[complete.cases(bg_track[, c("av_longitude_DD", "av_latitude_DD")]), ]
bg_sv <- vect(bg_track, geom = c("av_longitude_DD", "av_latitude_DD"), crs = "EPSG:4326")
bg_sv <- project(bg_sv, crs(env_stack))
bg_track_xy <- as.data.frame(crds(bg_sv))
colnames(bg_track_xy) <- c("x", "y")
rm(bg_track, bg_sv)

# occurrence points for both species
hump_pts_df <- as.data.frame(crds(hump_occ))
colnames(hump_pts_df) <- c("x", "y")
hump_pts_df$species <- "Humpback whale"
minke_pts_df <- as.data.frame(crds(minke_occ))
colnames(minke_pts_df) <- c("x", "y")
minke_pts_df$species <- "Minke whale"
occ_plot_df <- rbind(hump_pts_df, minke_pts_df)

indiv_specs <- list(
  list(label = "Humpback whale", suit_df = hump_df,  out_dir = "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/maxent_model/", fname = "humpback_maxent_map.png"),
  list(label = "Minke whale",    suit_df = minke_df, out_dir = "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/maxent_model/", fname = "minke_maxent_map.png")
)

for (sp in indiv_specs) {
  sp_track <- bg_track_xy
  sp_occ   <- occ_plot_df[occ_plot_df$species == sp$label, ]
  
  p_indiv <- ggplot(sp$suit_df, aes(x = x, y = y, fill = suitability)) +
    geom_raster() +
    scale_fill_viridis_c(
      name     = expression(bold("Suitability")),
      option   = "plasma",
      limits   = c(0, 1),
      na.value = "white"
    ) +
    geom_polygon(data = shore_df, aes(x = x, y = y, group = interaction(geom, part)),
                 inherit.aes = FALSE, fill = "white", color = NA) +
#    geom_polygon(data = shore_df, aes(x = x, y = y, group = interaction(geom, part)),
#                 inherit.aes = FALSE, fill = NA, color = "grey80", linewidth = 0.25) +
    geom_path(data = sp_track, aes(x = x, y = y),
              inherit.aes = FALSE, color = "black", linewidth = 0.7, alpha = 0.6) +
    geom_point(data = sp_occ, aes(x = x, y = y),
               inherit.aes = FALSE, color = "black", fill = "white",
               shape = 21, size = 1.5, stroke = 0.4, alpha = 0.85) +
    labs(title = paste0(sp$label, " Habitat Suitability"), x = "Easting (m)", y = "Northing (m)") +
    theme_classic(base_size = 11) +
    theme(
      plot.title  = element_text(face = "bold", hjust = 0.5),
      axis.title  = element_text(face = "bold"),
      legend.title = element_text(face = "bold"),
      legend.position = "right"
    ) +
    scale_x_continuous(expand = c(0, 0)) +
    scale_y_continuous(expand = c(0, 0)) +
    coord_equal(xlim = x_lim, ylim = y_lim, expand = FALSE)
  
  png(paste0(sp$out_dir, sp$fname), width = 10, height = 8, units = "in", res = 300)
  print(p_indiv)
  dev.off()
  cat("saved:", paste0(sp$out_dir, sp$fname), "\n")
}

################################################################################
# OCCURRENCE DISTRIBUTION CHECK
################################################################################
hump_pts_df  <- as.data.frame(crds(hump_occ));  hump_pts_df$species  <- "Humpback whale"
minke_pts_df <- as.data.frame(crds(minke_occ)); minke_pts_df$species <- "Minke whale"
both_pts_df  <- rbind(hump_pts_df, minke_pts_df)
shore_df <- as.data.frame(geom(shore_utm)[, c("geom", "part", "x", "y")])

# same disagg-then-mask order as above, applied to bathymetry
bathy_masked <- disagg(env_stack[[1]], fact = disagg_factor, method = "bilinear")
bathy_masked <- mask(bathy_masked, shore_utm, inverse = TRUE)

p_thincheck <- ggplot() +
  geom_raster(data = as.data.frame(bathy_masked, xy = TRUE),
              aes(x = x, y = y, fill = bathymetry), show.legend = FALSE) +
  scale_fill_distiller(palette = "Greys", direction = 1, na.value = "white") +
  geom_polygon(data = shore_df, aes(x = x, y = y, group = interaction(geom, part)),
               fill = "grey70", color = NA) +
  geom_point(data = both_pts_df, aes(x = x, y = y, color = species),
             size = 0.6, alpha = 0.5) +
  scale_color_manual(values = c("Humpback whale" = "#e84545", "Minke whale" = "#2196f3"), name = NULL) +
  labs(title = "Raw Occurrences — Humpback vs. Minke", x = "Easting (m)", y = "Northing (m)") +
  theme_classic(base_size = 11) +
  theme(plot.title = element_text(face = "bold", hjust = 0.5), legend.position = "bottom") +
  coord_equal()

png(paste0(out_base, "occurrence_distribution_check.png"), width = 10, height = 8, units = "in", res = 300)
print(p_thincheck)
dev.off()
cat("saved: occurrence_distribution_check.png\n")
















