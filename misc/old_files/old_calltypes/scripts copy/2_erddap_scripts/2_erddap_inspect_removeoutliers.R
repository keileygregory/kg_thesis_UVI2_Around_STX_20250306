# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This script examines the mission ERDDAP data for outliers/illogical values and removes these values if necessary (*so that incorrect measurements recorded by glider do NOT affect values of environmental conditions interpolated for detections or in background conditions*) to output a CSV file containing cleaned ERDDAP data for use in interpolation and statistical calculations (example of possible illogical values to be removed: oxygen sensor recording measurements when out of water during surfacing event).

# Input raw ERDDAP .csv file directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/missionname/data/2_data_processed/erddap_processed
# Output clean ERDDAP .csv file directory: Same as input directory

# 𖠺 Created by Keiley Gregory on December 1, 2025
# Last updated on March 2, 2026
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#𖠜 SEARCH "#𖠜" TO FIND LINES WHERE FILE PATHS NEED TO BE CHANGED FOR CURRENT MISSION


library(tidyverse)
library(patchwork)  # optional, for combining plots
library(knitr)
library(kableExtra) # optional but makes it prettier

# Import .csv of raw ERDDAP data for mission (*using relative path since working in R project)
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
data <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/erddap_processed/raw_erddap_UVI2_Around_STX_20250306.csv")



# ██████████████████████████████████████████████████████████████████████████████████████████████████

# 𓇼 PART 1 - INSPECT RAW DATA FOR OUTLIERS 𓇼

# ██████████████████████████████████████████████████████████████████████████████████████████████████


#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# SUMMARY TABLE
#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Create summary table of descriptive stats for each environmental variable in ERDDAP data
summary_table <- data %>%
  select("glider_depth_m", "water_temperature_C", "salinity_PSU", "oxygen_concentration_μmol_L") %>%
  pivot_longer(
    cols = everything(),
    names_to  = "Oceanographic_Variable",
    values_to = "Value"
  ) %>%
  group_by(Oceanographic_Variable) %>%
  summarise(
    n     = sum(!is.na(Value)),
    n_NA  = sum(is.na(Value)),
    Mean  = mean(Value, na.rm = TRUE),
    SEM   = sd(Value, na.rm = TRUE) / sqrt(n),
    SD    = sd(Value, na.rm = TRUE),
    Min   = min(Value, na.rm = TRUE),
    Q1    = quantile(Value, 0.25, na.rm = TRUE),
    Median = median(Value, na.rm = TRUE),
    Q3    = quantile(Value, 0.75, na.rm = TRUE),
    Max   = max(Value, na.rm = TRUE),
    .groups = "drop"
  )

#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# BOX PLOT
#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Pivot longer to create Oceanographic_Variable col + Value col
data_long <- data %>%
  select(glider_depth_m, water_temperature_C, salinity_PSU, oxygen_concentration_μmol_L) %>%
  pivot_longer(
    cols = everything(),
    names_to = "Oceanographic_Variable",
    values_to = "Value"
  )

# Create custom color scheme for oceanographic variables
custom_colors <- c(
  glider_depth_m                 = "#908bc9",
  water_temperature_C            = "#a45cad",
  salinity_PSU                   = "#e632ad",
  oxygen_concentration_μmol_L    = "#ffa100"
)

# Faceted box plot
boxplot <- ggplot(data_long, aes(x = "", y = Value, fill = Oceanographic_Variable, color = Oceanographic_Variable)) +
  geom_boxplot(width = 0.5, alpha = 0.45, outlier.alpha = 0.7, outlier.size = 1.5) +
  facet_wrap(
    ~ Oceanographic_Variable,
    scales = "free_y",
    ncol = 3,
    labeller = labeller(
      Oceanographic_Variable = function(x) {
        x <- gsub("_", " ", x)            # underscores → spaces
        x <- gsub("μmol L", "μmol/L", x)  # ONLY fix this unit
        stringr::str_wrap(x, width = 12)
      }
    )
  ) +
  scale_fill_manual(values = custom_colors, guide = "none") +
  scale_color_manual(values = custom_colors, guide = "none") +
  labs(
    x = NULL,
    y = "Value"
  ) +
  theme_minimal(base_size = 10) +
  theme(
    text = element_text(color = "black"),
    strip.text = element_text(color = "black", face = "bold", size = 11),
    axis.title.x = element_blank(),
    axis.text.x  = element_blank(),
    axis.ticks.x = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 10, margin = margin(r = 5))
  )
boxplot
# --------------
# oxygen has low outlier dot near 0
# salinity has low outlier dot near ~26.25
# --------------

#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# IQR THRESHOLD FOR OUTLIER VARIABLE(S)
#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Function to compute IQR thresholds
iqr_limits <- function(x) {
  Q1  <- quantile(x, 0.25, na.rm = TRUE)
  Q3  <- quantile(x, 0.75, na.rm = TRUE)
  IQR <- Q3 - Q1
  tibble(
    lower = Q1 - 1.5 * IQR,
    upper = Q3 + 1.5 * IQR
  )
}

# Compute oxygen thresholds
oxy_limits <- iqr_limits(data$oxygen_concentration_μmol_L)
oxy_limits
# --------------
# 79.1 to 250 umol/L
# --------------

# Compute salinity thresholds
sal_limits <- iqr_limits(data$salinity_PSU)
sal_limits 
# --------------
# 35.3 to 38.3 psu
# --------------

#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# TABLE OF ROWS SURROUNDING OUTLIER ROW(S)
# *to show conditions surrounding time of measurement*
#▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Function to print table of each outlier WITH 5 rows before + 5 rows after every outlier
extract_context <- function(df, outlier_rows, k = 5) {
  out_ids <- outlier_rows$row_id
  context <- map_df(out_ids, function(id) {
    start <- max(1, id - k)
    end   <- min(nrow(df), id + k)
    df[start:end, ] %>%
      mutate(outlier_row = id)
  })
  context
}


# OXYGEN:
# Extract oxy outlier rows
oxy_outliers <- data %>%
  mutate(row_id = row_number()) %>%
  filter(
    oxygen_concentration_μmol_L < oxy_limits$lower |
      oxygen_concentration_μmol_L > oxy_limits$upper
  )
# --------------
# datetime_UTC            glider_depth_m      oxygen_concentration_μmol_L
#	2025-03-17 19:45:38     0.00437378          0
# 2025-03-19 14:19:36     0.03856818          0
# 2025-03-23 18:01:32     0.04850802          0
# 2025-03-23 18:01:35     0.07385544          0
# --------------

# Oxy outliers context table
oxygen_context <- extract_context(
  df = data %>% mutate(row_id = row_number()),
  outlier_rows = oxy_outliers,
  k = 5
)
# --------------
# No oxy measurements collected in rows surrounding outlier measurements, but ALL oxy outlier values recorded when glider was at surface (depth < 0.1 m)
# **Conclude outlier values likely due to oxygen sensor being out of the water at time of measurement**
# --------------

# SALINITY:
# Extract salinity outlier row
sal_outliers <- data %>%
  mutate(row_id = row_number()) %>%
  filter(
    salinity_PSU < sal_limits$lower |
      salinity_PSU > sal_limits$upper
  )
# --------------
# datetime_UTC            glider_depth_m      water_temperature_c     salinity_psu
# 2025-03-17 09:13:22     299.969             15.3916                 26.23719
# --------------

# Salinity outlier context table
salinity_context <- extract_context(
  df = data %>% mutate(row_id = row_number()),
  outlier_rows = sal_outliers,
  k = 5
)
# --------------
# outlier row AND all surrounding rows with salinity values have glider depth btwn 299-300 m, water temp btwn 15.37-15.39 C, and oxygen ~139.9 umol/L
# all surrounding rows have salinity btwn 36.35-26.36 psu - which is ~10 psu HIGHER than outlier
# **Since all salinity values recorded only a few seconds before/after outlier have consistent salinity value (~36.3) and similar conditions (depth, temp, oxy) as when outlier was recorded - conclude outlier value probably due to anomaly instrument issue**
# --------------



# ██████████████████████████████████████████████████████████████████████████████████████████████████

# 𓇼 PART 2 - REMOVE OUTLIERS AS DECIDED AND EXPORT CLEANED CSV OF DATA 𓇼

# ██████████████████████████████████████████████████████████████████████████████████████████████████


# Remove outliers for specified variables using manually set thresholds defined in code below (change all cells with outlier values to NA *WITHOUT AFFECTING ANY OTHER COLUMNS IN THOSE ROWS*)
data_CLEAN <- data %>% mutate(
  
  salinity_PSU = if_else(
    # remove value in 1 cell (= 26.23719 psu) with implausibly low value (*salinity IQR range = 35.3 to 38.3)
    salinity_PSU < 35,
    # set outlier cell to NA
    NA_real_,
    # keep original value in row for all other var columns
    salinity_PSU
  ),
  
  oxygen_concentration_μmol_L = if_else(
    # remove values in 4 cells (all = 0.000 µmol/L) with values recorded when sensor was out of water during surfacing (glider depth < 0.1 m) (*oxy IQR range = 79.1 to 250)
    oxygen_concentration_μmol_L < 70,
    # set outlier cell to NA
    NA_real_,
    # keep original value in row for all other var columns
    oxygen_concentration_μmol_L
  )
)

# Save cleaned dataframe as CSV to use for interpolation/statistical calculations
#𖠜 CHANGE FILE PATH FOR CURRENT MISSION
write_csv(data_CLEAN, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/2_data_processed/erddap_processed/CLEAN_erddap_UVI2_Around_STX_20250306.csv")

# ██████████████████████████████████████████████████████████████████████████████████████████████████










# ################################################################################
# # EXTRA OPTIONAL SCATTERPLOTS (OUTLIER VARIABLE(S) OVER DEPTH) CODE TO USE IF DESIRED:
# 
# # Oxygen vs depth scatterplot (*clip to weirdly low oxy values less than 50 psu)
# oxy_depth_scatter <- ggplot(data, aes(x = oxygen_concentration_μmol_L, y = glider_depth_m)) +
#   geom_point(alpha = 0.5, size = 5, color = "#ffa100") +
#   scale_y_reverse() +
#   coord_cartesian(xlim = c(0, 20)) +   # CLIP X-AXIS RANGE TO SHOW OUTLIER
#   labs(
#     x = "[D.O.] (μmol/L)",
#     y = "Glider Depth (m)",
#     title = "D.O. Outliers vs Depth"
#   ) +
#   theme_bw()
# oxy_depth_scatter
# 
# # Salinity vs depth scatterplot (*clip to weirdly low salinity values less than 30 psu)
# salinity_depth_scatter <- ggplot(data, aes(x = salinity_PSU, y = glider_depth_m)) +
#   geom_point(alpha = 0.5, size = 5, color = "#e632ad") +
#   scale_y_reverse() +
#   coord_cartesian(xlim = c(10, 30)) +   # CLIP X-AXIS RANGE TO SHOW OUTLIER
#   labs(
#     x = "Salinity (PSU)",
#     y = "Glider Depth (m)",
#     title = "Salinity Outliers vs Depth"
#   ) +
#   theme_bw()
# salinity_depth_scatter
# ################################################################################