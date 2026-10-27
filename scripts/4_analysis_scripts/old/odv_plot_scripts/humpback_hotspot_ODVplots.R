# This script...

# Input .csv files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/hotspots_data
# Output figure .png files directory: /Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots

# 𖠺 Created by Keiley Gregory on March 15, 2026
# Last updated on March 15, 2026



# x-axis : av_datetime_UTC      (datetime during mission)
# y-axis : glider_depth_m       (positive = deeper; flipped for plotting)
# bathy  : bathymetric_depth_m  (in CSV from GIS calculations)


library(tidyverse)
library(MBA)
library(reshape2)

# Import data from tidy arcgis calculations CSV
background_raw <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/hotspots_data/TIDY_humpback_hotspot01_LF_background_POINTS_NAD83.csv")

detections_raw <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/hotspots_data/TIDY_humpback_hotspot01_humpback_POINTS_NAD83.csv")

# ODV colour palette (warm → cool when rev()'d)
ODV_colours <- c("#feb483", "#d31f2a", "#ffc000", "#27ab19", "#0db5e6", "#7139fe", "#d16cfa")

# MBA grid resolution (increase = finer)
INTERP_RES <- 600

# Convert datetime to numeric for MBA
background <- background_raw %>%
  mutate(datetime_num = as.numeric(as.POSIXct(av_datetime_UTC, tz = "UTC")),
         depth = glider_depth_m,
         bathy    = bathymetric_depth_m)

detections <- detections_raw %>%
  mutate(datetime_num = as.numeric(as.POSIXct(av_datetime_UTC, tz = "UTC")), 
         depth = glider_depth_m,
         bathy    = bathymetric_depth_m)

# Crop detections dataframe av_datetime_UTC range to background dataframe av_datetime_UTC range
detections <- detections %>%
  filter(datetime_num >= min(background$datetime_num),
         datetime_num <= max(background$datetime_num))



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

# Closed polygon for seafloor mask (same pattern as temp block)
bathy_mask_bathy <- bind_rows(
  bathy_sum_bathy %>% select(datetime_num, depth = bathy),
  tibble(datetime_num = rev(bathy_sum_bathy$datetime_num), depth = min(bathy_sum_bathy$bathy))
)

# Depth axis limit — use bathy range so the seafloor profile is visible
y_min_bathy <- -max(abs(bathy_sum_bathy$bathy), na.rm = TRUE) * 1.05

# PLOT: BATHYMETRIC DEPTH ------------------------------------------------------
p_bathy <- ggplot() +
  # white panel background (no fill variable — plain background)
  theme_bw(base_size = 10) +
  # seafloor mask
  geom_polygon(data = bathy_mask_bathy,
               aes(x = datetime_num, y = depth),
               fill = "grey30", colour = "black", linewidth = 0.5) +
  # bathymetric depth profile line
  geom_line(data = bathy_sum_bathy,
            aes(x = datetime_num, y = bathy),
            colour = "black", linewidth = 0.5) +
  # actual glider depth track (mapped to colour so appears in legend)
  geom_line(data = bathy_plot,
            aes(x = datetime_num, y = depth, colour = "Glider Depth (m)"), 
            linewidth = 0.25) +
  # detection points (mapped to colour so appears in legend)
  geom_point(data = detections,
             aes(x = datetime_num, y = depth, shape = "Humpback Detections"),
             inherit.aes = FALSE,
             fill = "black",
             size = 1.25, stroke = 0) +
  # manual colour scale for glider depth line
  scale_colour_manual(
    name   = "Glider \nDepth (m)",
    values = c("Glider Depth (m)" = "black")
  ) +
  # manual shape scale for detection points
  scale_shape_manual(
    name   = "Humpback \nDetections",
    values = c("Humpback Detections" = 21)
  ) +
  # x-axis (3600 sec = 1 hour)
  scale_x_continuous(
    breaks = seq(min(bathy_plot$datetime_num),
                 max(bathy_plot$datetime_num),
                 by = 3600),
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%H:%M:%S")
  ) +
  # y-axis (show positive depth labels, extend to deepest bathy)
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(y_min_bathy, 0)
  ) +
  labs(x = "Time (UTC) on March 19, 2025", y = "Bathymetric Depth (m)") +
  coord_cartesian(expand = FALSE) +
  # title.position = "top" places each guide title above its key; label = FALSE suppresses the redundant text label beside the key
  guides(
    colour = guide_legend(
      order          = 1,
      title.position = "top",
      title.hjust    = 0.5,
      label          = FALSE,
      override.aes   = list(linewidth = 0.8, shape = NA)
    ),
    shape = guide_legend(
      order          = 2,
      title.position = "top",
      title.hjust    = 0.5,
      label          = FALSE,
      override.aes   = list(colour = "black", fill = "black", size = 2)
    )
  ) +
  theme(
    panel.grid           = element_blank(),
    legend.position      = "right",
    legend.title         = element_text(size = 8.5, color = "black", hjust = 0.5),
    legend.title.align   = 0.5,
    legend.text          = element_text(size = 7, color = "black"),
    legend.key.size      = unit(0.6, "cm"),
    legend.spacing.y     = unit(0.4, "cm"),
    axis.text.x          = element_text(angle = 45, hjust = 1, size = 7, color = "black"),
    axis.text.y          = element_text(size = 7, color = "black"),
    axis.title.x         = element_text(face = "bold", size = 10),
    axis.title.y         = element_text(face = "bold", size = 10)
  )

print(p_bathy)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/humpback_hotspot01_ODV_bathy.png", plot = p_bathy, width = 10, height = 5, dpi = 800)



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
  # glider depth track (mapped to colour for legend)
  geom_line(data = temp,
            aes(x = datetime_num, y = depth, colour = "Glider Track"),
            inherit.aes = FALSE,
            linewidth = 0.4) +
  # detection points (mapped to shape for legend)
  geom_point(data = detections,
             aes(x = datetime_num, y = depth, shape = "Humpback Detections"),
             inherit.aes = FALSE,
             fill = "grey90",
             size = 1.75, stroke = 0.25) +
  # fill colour scale
  scale_fill_gradientn(colours = rev(ODV_colours), name = "Water Temperature (°C)") +
  # manual colour scale for glider track
  scale_colour_manual(
    name   = NULL,
    values = c("Glider Track" = "black")
  ) +
  # manual shape scale for detections
  scale_shape_manual(
    name   = NULL,
    values = c("Humpback Detections" = 21)
  ) +
  scale_x_continuous(
    breaks = seq(min(interp_temp$datetime_num),
                 max(interp_temp$datetime_num),
                 by = 3600),
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%H:%M:%S")
  ) +
  # y-axis
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(-max(abs(temp$depth), na.rm = TRUE), 0)
  ) +
  # axis labels
  labs(x = "Time (UTC) on March 19, 2025", y = "Depth (m)") +
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
  ) +
  guides(
    fill   = guide_colorbar(order = 1),
    colour = guide_legend(order = 2,
                          override.aes = list(linewidth = 0.8)),
    shape  = guide_legend(order = 3,
                          override.aes = list(fill = "grey90", size = 2.5, stroke = 0.5))
  )

print(p_temp)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/humpback_hotspot01_ODV_temp.png", plot = p_temp, width = 15, height = 5, dpi = 800)



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
  # glider depth track (mapped to colour for legend)
  geom_line(data = sal,
            aes(x = datetime_num, y = depth, colour = "Glider Track"),
            inherit.aes = FALSE,
            linewidth = 0.4) +
  # detection points (mapped to shape for legend)
  geom_point(data = detections,
             aes(x = datetime_num, y = depth, shape = "Humpback Detections"),
             inherit.aes = FALSE,
             fill = "grey90",
             size = 1.75, stroke = 0.25) +
  # fill colour scale
  scale_fill_gradientn(colours = rev(ODV_colours), name = "Salinity (PSU)") +
  # manual colour scale for glider track
  scale_colour_manual(
    name   = NULL,
    values = c("Glider Track" = "black")
  ) +
  # manual shape scale for detections
  scale_shape_manual(
    name   = NULL,
    values = c("Humpback Detections" = 21)
  ) +
  scale_x_continuous(
    breaks = seq(min(interp_sal$datetime_num),
                 max(interp_sal$datetime_num),
                 by = 3600),
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%H:%M:%S")
  ) +
  # y-axis
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(-max(abs(sal$depth), na.rm = TRUE), 0)
  ) +
  # axis labels
  labs(x = "Time (UTC) on March 19, 2025", y = "Depth (m)") +
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
  ) +
  guides(
    fill   = guide_colorbar(order = 1),
    colour = guide_legend(order = 2,
                          override.aes = list(linewidth = 0.8)),
    shape  = guide_legend(order = 3,
                          override.aes = list(fill = "grey90", size = 2.5, stroke = 0.5))
  )

print(p_sal)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/humpback_hotspot01_ODV_salinity.png", plot = p_sal, width = 15, height = 5, dpi = 800)



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
  # glider depth track (mapped to colour for legend)
  geom_line(data = oxy,
            aes(x = datetime_num, y = depth, colour = "Glider Track"),
            inherit.aes = FALSE,
            linewidth = 0.4) +
  # detection points (mapped to shape for legend)
  geom_point(data = detections,
             aes(x = datetime_num, y = depth, shape = "Humpback Detections"),
             inherit.aes = FALSE,
             fill = "grey90",
             size = 1.75, stroke = 0.25) +
  # fill colour scale
  scale_fill_gradientn(colours = rev(ODV_colours), name = "Dissolved Oxygen (μmol/L)") +
  # manual colour scale for glider track
  scale_colour_manual(
    name   = NULL,
    values = c("Glider Track" = "black")
  ) +
  # manual shape scale for detections
  scale_shape_manual(
    name   = NULL,
    values = c("Humpback Detections" = 21)
  ) +
  scale_x_continuous(
    breaks = seq(min(interp_oxy$datetime_num),
                 max(interp_oxy$datetime_num),
                 by = 3600),
    labels = function(x) format(as.POSIXct(x, origin = "1970-01-01", tz = "UTC"), "%H:%M:%S")
  ) +
  # y-axis
  scale_y_continuous(
    labels = function(x) abs(x),
    limits = c(-max(abs(oxy$depth), na.rm = TRUE), 0)
  ) +
  # axis labels
  labs(x = "Time (UTC) on March 19, 2025", y = "Depth (m)") +
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
  ) +
  guides(
    fill   = guide_colorbar(order = 1),
    colour = guide_legend(order = 2,
                          override.aes = list(linewidth = 0.8)),
    shape  = guide_legend(order = 3,
                          override.aes = list(fill = "grey90", size = 2.5, stroke = 0.5))
  )

print(p_oxy)

# Export plot as PNG
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/odv_plots/LF_odv_plots/humpback_hotspot01_ODV_oxygen.png", plot = p_oxy, width = 15, height = 5, dpi = 800)
