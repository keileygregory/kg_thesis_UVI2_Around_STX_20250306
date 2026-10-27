# This script...

# Input .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis
# Output figure .png files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots

# 𖠺 Created by Keiley Gregory on March 15, 2026
# Last updated on March 16, 2026



# x-axis : av_datetime_UTC      (datetime during mission)
# y-axis : glider_depth_m       (positive = deeper; flipped for plotting)
# bathy  : bathymetric_depth_m  (in CSV from GIS calculations)


library(tidyverse)
library(MBA)
library(reshape2)

# Import data from tidy arcgis calculations CSV
background_raw <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/TIDY_calc_LF_background_POINTS_NAD83.csv")

# Import HUMPBACK hotspot CSV and compute numeric datetime range for box overlays
humpback_hotspot_raw <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/hotspots_data/TIDY_humpback_hotspot01_LF_background_POINTS_NAD83.csv")

humpback_hotspot_xmin <- as.numeric(as.POSIXct(min(humpback_hotspot_raw$av_datetime_UTC, na.rm = TRUE), tz = "UTC"))
humpback_hotspot_xmax <- as.numeric(as.POSIXct(max(humpback_hotspot_raw$av_datetime_UTC, na.rm = TRUE), tz = "UTC"))

# Import MINKE hotspot CSV and compute numeric datetime range for box overlays
minke_hotspot_raw <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/hotspots_data/TIDY_minke_hotspot01_LF_background_POINTS_NAD83.csv")

minke_hotspot_xmin <- as.numeric(as.POSIXct(min(minke_hotspot_raw$av_datetime_UTC, na.rm = TRUE), tz = "UTC"))
minke_hotspot_xmax <- as.numeric(as.POSIXct(max(minke_hotspot_raw$av_datetime_UTC, na.rm = TRUE), tz = "UTC"))

# ODV colour palette (warm → cool when rev()'d)
ODV_colours <- c("#feb483", "#d31f2a", "#ffc000", "#27ab19", "#0db5e6", "#7139fe", "#d16cfa")

# MBA grid resolution (increase = finer)
INTERP_RES <- 600

# Convert datetime to numeric for MBA
background <- background_raw %>%
  mutate(datetime_num = as.numeric(as.POSIXct(av_datetime_UTC, tz = "UTC")),
         depth = glider_depth_m,
         bathy    = bathymetric_depth_m)

# Daily midnight breaks for x-axis (00:00:00 UTC each day)
daily_breaks <- seq(
  from = as.numeric(as.POSIXct(format(min(background$av_datetime_UTC), "%Y-%m-%d"), tz = "UTC")),
  to   = as.numeric(as.POSIXct(format(max(background$av_datetime_UTC), "%Y-%m-%d"), tz = "UTC")),
  by   = 86400
)



# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# BATHYMETRIC DEPTH (line only, no fill)
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Filter background to valid bathy + datetime rows
bathy_plot <- background %>%
  filter(!is.na(bathy), !is.na(av_datetime_UTC), !is.na(depth))

# Summarise bathy to ~500 datetime bins (mean per bin) for seafloor profile line
bathy_sum_bathy <- bathy_plot %>%
  mutate(datetime_bin = cut(datetime_num, breaks = 500, labels = FALSE)) %>%
  group_by(datetime_bin) %>%
  summarise(
    datetime_num = mean(datetime_num),
    bathy        = mean(bathy),
    .groups = "drop"
  ) %>%
  arrange(datetime_num)

# Depth axis limit — use bathy range so the seafloor profile is visible
y_min_bathy <- -max(abs(bathy_plot$bathy), na.rm = TRUE)

# Closed polygon for seafloor mask (same pattern as temp block)
bathy_mask_bathy <- bind_rows(
  bathy_sum_bathy %>% select(datetime_num, depth = bathy),
  tibble(datetime_num = rev(bathy_sum_bathy$datetime_num), depth = y_min_bathy)
)

# PLOT: BATHYMETRIC DEPTH ------------------------------------------------------
p_bathy <- ggplot() +
  # white panel background (no fill variable — plain background)
  theme_bw(base_size = 10) +
  # seafloor mask
  geom_polygon(data = bathy_mask_bathy,
               aes(x = datetime_num, y = depth),
               fill = "grey50", colour = "black", linewidth = 0.25) +
  # bathymetric depth profile line
  geom_line(data = bathy_sum_bathy,
            aes(x = datetime_num, y = bathy),
            colour = "black", linewidth = 0.25) +
  # humpback hotspot 01 time window box
  annotate("rect",
           xmin = humpback_hotspot_xmin, xmax = humpback_hotspot_xmax,
           ymin = y_min_bathy, ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = humpback_hotspot_xmin, y = 0,
           label = "Highest humpback\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # minke hotspot 01 time window box
  annotate("rect",
           xmin = minke_hotspot_xmin, xmax = minke_hotspot_xmax,
           ymin = y_min_bathy, ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = minke_hotspot_xmin, y = 0,
           label = "Highest minke\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # x-axis (86400 sec = 24 hours)
  scale_x_continuous(
    breaks = daily_breaks,
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%y-%m-%d")
  ) +
  # y-axis (show positive depth labels, extend to deepest bathy)
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(y_min_bathy, 0)
  ) +
  labs(x = "Date (UTC)", y = "Bathymetric Depth (m)") +
  coord_cartesian(expand = FALSE) +
  theme(
    panel.grid           = element_blank(),
    axis.text.x          = element_text(angle = 45, hjust = 1, size = 7, color = "black"),
    axis.text.y          = element_text(size = 7, color = "black"),
    axis.title.x         = element_text(face = "bold", size = 10),
    axis.title.y         = element_text(face = "bold", size = 10)
  )

print(p_bathy)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/LF_background_ODV_bathy.png", plot = p_bathy, width = 10, height = 5, dpi = 800)



# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# TEMPERATURE
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Create copy of raw dataframe, rename vars for convience, and filter for valid cells
temp <- background %>%
  rename(fill_val = "water_temperature_C") %>%
  filter(!is.na(fill_val), !is.na(av_datetime_UTC), !is.na(depth))

# BATHYMETRY MASK --------------------------------------------------------------
# Summarise bathy to ~500 datetime bins (mean per bin)
bathy_sum_temp <- temp %>%
  mutate(datetime_bin = cut(datetime_num, breaks = 500, labels = FALSE)) %>%
  group_by(datetime_bin) %>%
  summarise(
    datetime_num = mean(datetime_num),
    bathy        = mean(bathy),
    .groups = "drop"
  ) %>%
  arrange(datetime_num)

# Closed polygon (seafloor profile → bottom edge → close)
bathy_mask_temp <- bind_rows(
  bathy_sum_temp %>% select(datetime_num, depth = bathy),
  tibble(datetime_num = rev(bathy_sum_temp$datetime_num), depth = min(bathy_sum_temp$bathy))
)

# MULTILEVEL B-SPLINE (MBA) INTERPOLATION --------------------------------------
# mba.surf() takes columns in order: X, Y, Z
mba_temp <- mba.surf(
  temp[c("datetime_num", "depth", "fill_val")],
  no.X   = INTERP_RES,
  no.Y   = INTERP_RES,
  extend = TRUE
)

# dimnames(...) <- list(x, y) stamps actual X values (datetime_nums) onto rows and actual Y values (depths) onto columns (required for when you melt matrix so row/column indices become meaningful coordinates instead of 1, 2, 3...)
dimnames(mba_temp$xyz.est$z) <- list(
  mba_temp$xyz.est$x,
  mba_temp$xyz.est$y
)

# melt() takes labeled matrix and unpivots it from wide → long
interp_temp <- melt(
  mba_temp$xyz.est$z,
  varnames   = c("datetime_num", "depth"),
  value.name = "fill_val"
) %>%
  filter(depth < 0) %>%
  mutate(
    datetime_num = as.numeric(datetime_num),
    fill_val     = round(fill_val, 2)
  )

# PLOT: TEMPERATURE ------------------------------------------------------------
p_temp <- ggplot(interp_temp, aes(x = datetime_num, y = depth)) +
  # interpolated fill — geom_tile handles uneven intervals cleanly
  geom_tile(aes(fill = fill_val)) +
  # minor temp contours (every 2 units)
  geom_contour(aes(z = fill_val), binwidth = 2,
               colour = "white", alpha = 0.35, linewidth = 0.35) +
  # bathymetry mask
  geom_polygon(data = bathy_mask_temp,
               aes(x = datetime_num, y = depth),
               inherit.aes = FALSE,
               fill = "grey70", colour = "black", linewidth = 0.4) +
  # hotspot 01 time window box
  annotate("rect",
           xmin = humpback_hotspot_xmin, xmax = humpback_hotspot_xmax,
           ymin = -max(abs(temp$depth), na.rm = TRUE), ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = humpback_hotspot_xmin, y = 0,
           label = "Highest humpback\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # minke hotspot 01 time window box
  annotate("rect",
           xmin = minke_hotspot_xmin, xmax = minke_hotspot_xmax,
           ymin = -max(abs(temp$depth), na.rm = TRUE), ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = minke_hotspot_xmin, y = 0,
           label = "Highest minke\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # fill colour scale
  scale_fill_gradientn(colours = rev(ODV_colours), name = "Water \nTemperature \n(°C)") +
  scale_x_continuous(
    breaks = daily_breaks,
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%y-%m-%d")
  ) +
  # y-axis
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(-max(abs(temp$depth), na.rm = TRUE), 0)
  ) +
  # axis labels
  labs(x = "Date (UTC)", y = "Depth (m)") +
  # formatting
  coord_cartesian(expand = FALSE) +
  theme_bw(base_size = 10) +
  theme(
    panel.grid      = element_blank(),
    legend.position = "right",
    axis.text.x     = element_text(angle = 45, hjust = 1, size = 7, color = "black"),
    axis.text.y     = element_text(size = 7, color = "black"),
    legend.text     = element_text(size = 7, color = "black"),
    axis.title.x    = element_text(face = "bold", size = 10),
    axis.title.y    = element_text(face = "bold", size = 10),
    legend.title    = element_text(face = "bold", size = 10)
  )

print(p_temp)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/LF_background_ODV_temp.png", plot = p_temp, width = 15, height = 5, dpi = 800)



# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# SALINITY
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Create copy of raw dataframe, rename vars for convience, and filter for valid cells
sal <- background %>%
  rename(fill_val = "salinity_PSU") %>%
  filter(!is.na(fill_val), !is.na(av_datetime_UTC), !is.na(depth))

# BATHYMETRY MASK --------------------------------------------------------------
# Summarise bathy to ~500 datetime bins (mean per bin)
bathy_sum_sal <- sal %>%
  mutate(datetime_bin = cut(datetime_num, breaks = 500, labels = FALSE)) %>%
  group_by(datetime_bin) %>%
  summarise(
    datetime_num = mean(datetime_num),
    bathy        = mean(bathy),
    .groups = "drop"
  ) %>%
  arrange(datetime_num)

# Closed polygon (seafloor profile → bottom edge → close)
bathy_mask_sal <- bind_rows(
  bathy_sum_sal %>% select(datetime_num, depth = bathy),
  tibble(datetime_num = rev(bathy_sum_sal$datetime_num), depth = min(bathy_sum_sal$bathy))
)

# MULTILEVEL B-SPLINE (MBA) INTERPOLATION --------------------------------------
# mba.surf() takes columns in order: X, Y, Z
mba_sal <- mba.surf(
  sal[c("datetime_num", "depth", "fill_val")],
  no.X   = INTERP_RES,
  no.Y   = INTERP_RES,
  extend = TRUE
)

# dimnames(...) <- list(x, y) stamps actual X values (datetime_nums) onto rows and actual Y values (depths) onto columns (required for when you melt matrix so row/column indices become meaningful coordinates instead of 1, 2, 3...)
dimnames(mba_sal$xyz.est$z) <- list(
  mba_sal$xyz.est$x,
  mba_sal$xyz.est$y
)

# melt() takes labeled matrix and unpivots it from wide → long
interp_sal <- melt(
  mba_sal$xyz.est$z,
  varnames   = c("datetime_num", "depth"),
  value.name = "fill_val"
) %>%
  filter(depth < 0) %>%
  mutate(
    datetime_num = as.numeric(datetime_num),
    fill_val     = round(fill_val, 2)
  )

# PLOT: SALINITY ---------------------------------------------------------------
p_sal <- ggplot(interp_sal, aes(x = datetime_num, y = depth)) +
  # interpolated fill — geom_tile handles uneven intervals cleanly
  geom_tile(aes(fill = fill_val)) +
  # minor salinity contours (every 0.25 units)
  geom_contour(aes(z = fill_val), binwidth = 0.25,
               colour = "white", alpha = 0.35, linewidth = 0.35) +
  # bathymetry mask
  geom_polygon(data = bathy_mask_sal,
               aes(x = datetime_num, y = depth),
               inherit.aes = FALSE,
               fill = "grey70", colour = "black", linewidth = 0.4) +
  # hotspot 01 time window box
  annotate("rect",
           xmin = humpback_hotspot_xmin, xmax = humpback_hotspot_xmax,
           ymin = -max(abs(sal$depth), na.rm = TRUE), ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = humpback_hotspot_xmin, y = 0,
           label = "Highest humpback\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # minke hotspot 01 time window box
  annotate("rect",
           xmin = minke_hotspot_xmin, xmax = minke_hotspot_xmax,
           ymin = -max(abs(sal$depth), na.rm = TRUE), ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = minke_hotspot_xmin, y = 0,
           label = "Highest minke\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # fill colour scale
  scale_fill_gradientn(colours = rev(ODV_colours), name = "Salinity \n(PSU)") +
  scale_x_continuous(
    breaks = daily_breaks,
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%y-%m-%d")
  ) +
  # y-axis
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(-max(abs(sal$depth), na.rm = TRUE), 0)
  ) +
  # axis labels
  labs(x = "Date (UTC)", y = "Depth (m)") +
  # formatting
  coord_cartesian(expand = FALSE) +
  theme_bw(base_size = 10) +
  theme(
    panel.grid      = element_blank(),
    legend.position = "right",
    axis.text.x     = element_text(angle = 45, hjust = 1, size = 7, color = "black"),
    axis.text.y     = element_text(size = 7, color = "black"),
    legend.text     = element_text(size = 7, color = "black"),
    axis.title.x    = element_text(face = "bold", size = 10),
    axis.title.y    = element_text(face = "bold", size = 10),
    legend.title    = element_text(face = "bold", size = 10)
  )

print(p_sal)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/LF_background_ODV_salinity.png", plot = p_sal, width = 15, height = 5, dpi = 800)



# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# DISSOLVED OXYGEN
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬
# ▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬▭▬

# Create copy of raw dataframe, rename vars for convience, and filter for valid cells
oxy <- background %>%
  rename(fill_val = "oxygen_concentration_μmol_L") %>%
  filter(!is.na(fill_val), !is.na(av_datetime_UTC), !is.na(depth))

# BATHYMETRY MASK --------------------------------------------------------------
# Summarise bathy to ~500 datetime bins (mean per bin)
bathy_sum_oxy <- oxy %>%
  mutate(datetime_bin = cut(datetime_num, breaks = 500, labels = FALSE)) %>%
  group_by(datetime_bin) %>%
  summarise(
    datetime_num = mean(datetime_num),
    bathy        = mean(bathy),
    .groups = "drop"
  ) %>%
  arrange(datetime_num)

# Closed polygon (seafloor profile → bottom edge → close)
bathy_mask_oxy <- bind_rows(
  bathy_sum_oxy %>% select(datetime_num, depth = bathy),
  tibble(datetime_num = rev(bathy_sum_oxy$datetime_num), depth = min(bathy_sum_oxy$bathy))
)

# MULTILEVEL B-SPLINE (MBA) INTERPOLATION --------------------------------------
# mba.surf() takes columns in order: X, Y, Z
mba_oxy <- mba.surf(
  oxy[c("datetime_num", "depth", "fill_val")],
  no.X   = INTERP_RES,
  no.Y   = INTERP_RES,
  extend = TRUE
)

# dimnames(...) <- list(x, y) stamps actual X values (datetime_nums) onto rows and actual Y values (depths) onto columns (required for when you melt matrix so row/column indices become meaningful coordinates instead of 1, 2, 3...)
dimnames(mba_oxy$xyz.est$z) <- list(
  mba_oxy$xyz.est$x,
  mba_oxy$xyz.est$y
)

# melt() takes labeled matrix and unpivots it from wide → long
interp_oxy <- melt(
  mba_oxy$xyz.est$z,
  varnames   = c("datetime_num", "depth"),
  value.name = "fill_val"
) %>%
  filter(depth < 0) %>%
  mutate(
    datetime_num = as.numeric(datetime_num),
    fill_val     = round(fill_val, 2)
  )

# PLOT: DISSOLVED OXYGEN -------------------------------------------------------
p_oxy <- ggplot(interp_oxy, aes(x = datetime_num, y = depth)) +
  # interpolated fill — geom_tile handles uneven intervals cleanly
  geom_tile(aes(fill = fill_val)) +
  # minor dissolved oxygen contours (every 10 units)
  geom_contour(aes(z = fill_val), binwidth = 10,
               colour = "white", alpha = 0.35, linewidth = 0.35) +
  # bathymetry mask
  geom_polygon(data = bathy_mask_oxy,
               aes(x = datetime_num, y = depth),
               inherit.aes = FALSE,
               fill = "grey70", colour = "black", linewidth = 0.4) +
  # hotspot 01 time window box
  annotate("rect",
           xmin = humpback_hotspot_xmin, xmax = humpback_hotspot_xmax,
           ymin = -max(abs(oxy$depth), na.rm = TRUE), ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = humpback_hotspot_xmin, y = 0,
           label = "Highest humpback\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # minke hotspot 01 time window box
  annotate("rect",
           xmin = minke_hotspot_xmin, xmax = minke_hotspot_xmax,
           ymin = -max(abs(oxy$depth), na.rm = TRUE), ymax = 0,
           fill = NA, colour = "black", linewidth = 0.7) +
  annotate("text",
           x = minke_hotspot_xmin, y = 0,
           label = "Highest minke\ndetection density",
           hjust = 1.05, vjust = 1.2,
           size = 2.5, fontface = "bold", colour = "black") +
  # fill colour scale
  scale_fill_gradientn(colours = rev(ODV_colours), name = "Dissolved \nOxygen \n(μmol/L)") +
  scale_x_continuous(
    breaks = daily_breaks,
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%y-%m-%d")
  ) +
  # y-axis
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(-max(abs(oxy$depth), na.rm = TRUE), 0)
  ) +
  # axis labels
  labs(x = "Date (UTC)", y = "Depth (m)") +
  # formatting
  coord_cartesian(expand = FALSE) +
  theme_bw(base_size = 10) +
  theme(
    panel.grid      = element_blank(),
    legend.position = "right",
    axis.text.x     = element_text(angle = 45, hjust = 1, size = 7, color = "black"),
    axis.text.y     = element_text(size = 7, color = "black"),
    legend.text     = element_text(size = 7, color = "black"),
    axis.title.x    = element_text(face = "bold", size = 10),
    axis.title.y    = element_text(face = "bold", size = 10),
    legend.title    = element_text(face = "bold", size = 10)
  )

print(p_oxy)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/LF_background_ODV_oxygen.png", plot = p_oxy, width = 15, height = 5, dpi = 800)
