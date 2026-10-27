# ──────────────────────────────────────────────────────────────────────────────
# This script runs MaxEnt habitat suitability models for humpback and minke whales separately using the 6-variable env_stack (bathymetry, slope, dist_shore, SST, SSS, Chl_log) at 1 km UTM 20N resolution. It outputs the model objects, suitability rasters, response curves, variable importance plots, and evaluation metrics for each species.
# All models are fit with Java MaxEnt (maxent.jar) so that every table and figure derives from the same model object.

# 𖠺 Created by Keiley Gregory on March 18, 2026
# Last updated on July 17, 2026
# ──────────────────────────────────────────────────────────────────────────────

# SEARCH "#‼️" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION

library(terra)
library(raster)    # dismo::maxent still expects Raster* objects, not SpatRaster
library(dismo)     # Java MaxEnt wrapper
library(rJava)
library(ENMeval)   # tuning + evaluation
library(ggplot2)
library(tidyterra)
library(dplyr)
library(tidyr)
library(stringr)
library(ecospat)
library(gt)


# Import .tif of env stack
# ‼️ CHANGE FILE PATH FOR MISSION
env_stack_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/maxent_env_stack_1km_UTM20N.tif"

# ‼️ Import CSVs containing complete (interpolated + GIS) data for each species
# ‼️ CHANGE FILE PATH FOR MISSION
hump_csv_path <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/LF_gis_data/TIDY_calc_humpback_POINTS_NAD83.csv"

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
out_base <- "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/3_maxent_output/"
out_hump <- paste0(out_base, "humpback/")
out_minke <- paste0(out_base, "minke/")

# Verify maxent.jar is installed before anything runs — every fit below needs it
maxent_jar <- paste0(system.file("java", package = "dismo"), "/maxent.jar")
if (!file.exists(maxent_jar)) {
  stop("maxent.jar not found. Download from ",
       "https://biodiversityinformatics.amnh.org/open_source/maxent/ and place in: ",
       dirname(maxent_jar))
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
  # min values  : -5414.684082,        -0,          0, 26.809502, 35.995895, -2.996236 
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
# *input CSV must have columns av_longitude_DD and av_latitude_DD (WGS84 decimal degrees); returns SpatVector in UTM 20N deduplicated to 1 pt per 1 km raster cell (ENMeval also deduplicates internally = ensures final maxent() fit uses same occurrence set as tuning step)
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
# SHARED HELPERS
# ██████████████████████████████████████████████████████████████████████████████

# translate an ENMeval feature class string (e.g. "LQH") into Java MaxEnt args
fc_to_java_args <- function(fc) {
  c(
    paste0("linear=",    tolower(grepl("L", fc))),
    paste0("quadratic=", tolower(grepl("Q", fc))),
    paste0("hinge=",     tolower(grepl("H", fc))),
    paste0("product=",   tolower(grepl("P", fc))),
    paste0("threshold=", tolower(grepl("T", fc)))
  )
}

# strip feature wrappers to recover parent variable name (hinge(dist_shore):123:456 -> dist_shore ; I(Chl_log^2) -> Chl_log)
strip_wrapper <- function(x) {
  x <- str_remove(x, "^(hinge|linear|quadratic|product|threshold|reverse_hinge)\\(")
  x <- str_remove(x, "^I\\(")
  x <- str_remove(x, "\\).*$")
  x <- str_remove(x, "\\^\\d+$")
  str_trim(x)
}

# read both importance metrics from maxentResults.csv and pair them by variable
# Java MaxEnt names these columns "<var> contribution" and "<var> permutation importance"
parse_maxent_results <- function(results_dir) {
  res <- read.csv(file.path(results_dir, "maxentResults.csv"), check.names = FALSE)
  
  long <- res %>%
    dplyr::select(matches(" contribution$| permutation importance$")) %>%
    pivot_longer(everything(), names_to = "feature_metric", values_to = "value") %>%
    mutate(
      metric = case_when(
        str_detect(feature_metric, " permutation importance$") ~ "perm_importance",
        str_detect(feature_metric, " contribution$")           ~ "contribution"
      ),
      # the variable name is whatever precedes the metric suffix
      variable = str_remove(feature_metric, " (permutation importance|contribution)$")
    )
  
  long %>%
    dplyr::select(variable, metric, value) %>%
    pivot_wider(names_from = metric, values_from = value) %>%
    # rank disagreement between the two metrics flags variables trading off credit
    mutate(
      perm_rank    = rank(-perm_importance, ties.method = "min"),
      contrib_rank = rank(-contribution,    ties.method = "min"),
      rank_diff    = perm_rank - contrib_rank
    ) %>%
    arrange(desc(contribution))
}


# ██████████████████████████████████████████████████████████████████████████████
# MAXENT MODEL FUNCTION
# ██████████████████████████████████████████████████████████████████████████████
# Model runs ENMeval tuning with maxent.jar, refits final model with same engine at selected settings, and exports raster + diagnostics (bg_xy: data.frame(x, y) of bias-weighted background points in UTM 20N)
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
    algorithm   = "maxent.jar",
    partitions  = "randomkfold",
    partition.settings = list(kfolds = 5),
    tune.args   = list(
      rm = c(0.5, 1, 1.5, 2, 2.5, 3, 3.5),
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
    dplyr::filter(delta.AICc == 0) %>%
    slice(1)
  cat("Optimal settings — RM:", opt_settings$rm, "| FC:", opt_settings$fc, "\n")
  cat("AICc:", opt_settings$AICc, "| Training AUC:", opt_settings$auc.train, "\n")
  
  # warn if several models tied — slice(1) picked one of them arbitrarily
  n_opt <- sum(eval_result@results$delta.AICc == 0, na.rm = TRUE)
  if (n_opt > 1) {
    warning(species_name, ": ", n_opt, " models tied at delta.AICc == 0 — slice(1) picked one arbitrarily")
  }
  # warn if the selected RM sits at the edge of the grid — the true optimum may lie outside it
  if (opt_settings$rm %in% range(c(0.5, 1, 1.5, 2, 2.5, 3, 3.5))) {
    warning(species_name, ": optimal RM (", opt_settings$rm, ") is at the edge of the tuning grid — consider widening it")
  }
  
  # ──────────────────────────────────────────────────────────────────────────
  # FIT MODEL
  # ──────────────────────────────────────────────────────────────────────────
  opt_rm <- opt_settings$rm
  opt_fc <- opt_settings$fc
  # extract env values at occurrence and background points
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
  # Java MaxEnt writes maxentResults.csv and its diagnostics into this directory
  java_dir <- paste0(out_dir, "java_maxent")
  if (!dir.exists(java_dir)) dir.create(java_dir, recursive = TRUE)
  # final model
  final_model <- maxent(
    x    = all_env,
    p    = p_bg,
    path = java_dir,
    args = c(
      fc_to_java_args(opt_fc),
      paste0("betamultiplier=", opt_rm),
      "responsecurves=true",
      "jackknife=true",
      "writeplotdata=true"
    )
  )
  # save model object
  saveRDS(final_model, paste0(out_dir, species_name, "_maxent_model.rds"))
  cat("Model saved to:", paste0(out_dir, species_name, "_maxent_model.rds"), "\n")
  
  # ──────────────────────────────────────────────────────────────────────────
  # PREDICT (generate suitability surface over full env_stack extent)
  # ──────────────────────────────────────────────────────────────────────────
  cat("Predicting suitability surface...\n")
  # extract env values for ocean cells only (drops NA rows, keeps cell numbers)
  env_df    <- as.data.frame(env_stack, cells = TRUE, na.rm = TRUE)
  cell_nums <- env_df$cell
  env_df    <- env_df[, -1]   # drop cell column before predict
  # dismo's predict on a data.frame returns the logistic output by default
  pred_vals <- predict(final_model, env_df)
  
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
  # VARIABLE IMPORTANCE (parsed from this model's own maxentResults.csv)
  # ──────────────────────────────────────────────────────────────────────────
  imp_df <- parse_maxent_results(java_dir)
  write.csv(
    imp_df,
    paste0(out_dir, species_name, "_variable_importance.csv"),
    row.names = FALSE
  )
  cat("\n── Variable Importance ──\n")
  print(imp_df)
  
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
  
  # 2. Variable importance — one bar per parent variable, not per hinge fragment
  p_imp <- ggplot(imp_df, aes(x = reorder(variable, contribution), y = contribution)) +
    geom_col(fill = "#2c7bb6", width = 0.6) +
    coord_flip() +
    labs(
      title = paste0(species_name, " — Variable Contribution"),
      x = NULL, y = "Variable Contribution (%)"
    ) +
    theme_classic(base_size = 11) +
    theme(plot.title = element_text(face = "bold", hjust = 0.5))
  # export as png
  png(paste0(out_dir, species_name, "_variable_importance.png"),
      width = 8, height = 5, units = "in", res = 300)
  print(p_imp)
  dev.off()
  
  # 3. Response curves (marginal responses per variable via dismo)
  cat("Plotting response curves...\n")
  png(paste0(out_dir, species_name, "_response_curves.png"),
      width = 12, height = 8, units = "in", res = 300)
  response(final_model)
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
    # mean cross-validated AUC across the 5 random folds — the reportable value
    AUC_val        = opt_settings$auc.val.avg,
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
    summary      = eval_summary,
    importance   = imp_df,
    occ_env      = occ_env,
    bg_env       = bg_env
  ))
}

# RUN MODELS ⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁⛁

# Humpback whale ---------------------------------------------------------------
hump_occ  <- prep_occurrences(hump_csv_path, env_stack)
hump_out  <- run_maxent("humpback", hump_occ, env_stack, out_hump, bg_xy)

# Minke whale ------------------------------------------------------------------
minke_occ <- prep_occurrences(minke_csv_path, env_stack)
minke_out <- run_maxent("minke", minke_occ, env_stack, out_minke, bg_xy)


# ██████████████████████████████████████████████████████████████████████████████
# MODEL SUMMARY TABLE
# ██████████████████████████████████████████████████████████████████████████████

# format the top-n variables as "Variable (12.34%), Variable (11.22%), etc."
format_contrib <- function(imp_df, n = 3) {
  top <- head(imp_df, n)
  paste0(top$variable, " (", sprintf("%.2f", top$contribution), "%)", collapse = " ")
}

# assemble one table row per species
build_table_row <- function(sp_out, sp_label) {
  data.frame(
    Species      = sp_label,
    Config       = paste0(sp_out$summary$optimal_fc, " RM ", sp_out$summary$optimal_rm),
    N_occurrence = sp_out$summary$n_occurrences,
    AUC_val      = sprintf("%.3f", sp_out$summary$AUC_val),
    Contribution = format_contrib(sp_out$importance)
  )
}

table2 <- rbind(
  build_table_row(hump_out,  "Humpback whale"),
  build_table_row(minke_out, "Minke whale")
)

write.csv(table2, paste0(out_base, "table2_model_summary.csv"), row.names = FALSE)
print(table2)

# Render the table as a publication-style PNG
gt(table2) %>%
  cols_label(
    Species      = "Species",
    Config       = "Feature classes and regularization multiplier values",
    N_occurrence = "Occurrences",
    AUC_val      = "AUC (5-fold CV)",
    Contribution = "Variable contribution (%)"
  ) %>%
  tab_footnote(
    "L, linear; Q, quadratic; H, hinge; P, product; RM, regularization multiplier."
  ) %>%
  gtsave(paste0(out_base, "table2.png"))
cat("saved:", paste0(out_base, "table2.png"), "\n")


################################################################################
# SUITABILITY MASKING -- run exactly once, disagg BEFORE mask
################################################################################

# reload raw (never-masked) 1km suitability rasters from disk
# (skips re-running the maxent fit)
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