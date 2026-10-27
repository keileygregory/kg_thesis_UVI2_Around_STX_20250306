# Last edited on March 9, 2026

library(tidyverse)
library(ggridges)  # for ridge plots
library(patchwork) # optional, for combining plots
library(knitr)
library(kableExtra) # optional but makes it prettier


# Import *TIDY* HUMPBACK DETECTION mission data
hbk <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/TIDY_calc_humpback_POINTS_NAD83.csv")

# Import *TIDY* LF BACKGROUND mission data
bck <- read_csv("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/5_data_gis/TIDY_calc_LF_background_POINTS_NAD83.csv")


# ----------------------------------------
# Create DETECTIONS summary table dataframe
hbk_summary <- hbk %>%
  select("glider_depth_m", 
         "water_temperature_C",
         "salinity_PSU",
         "oxygen_concentration_μmol_L", 
         "sea_surface_water_temperature_C",
         "sea_surface_salinity_PSU",
         "sea_surface_oxygen_concentration_μmol_L",
         "bathymetric_depth_m",
         "bathymetric_slope_deg",
         "distance_near_shore_m"
         ) %>%
  pivot_longer(
    cols = everything(),
    names_to  = "Oceanographic_Variable",
    values_to = "Value"
  ) %>%
  group_by(Oceanographic_Variable) %>%
  summarise(
    n     = sum(!is.na(Value)),
    Mean  = mean(Value, na.rm = TRUE),
    SEM   = sd(Value, na.rm = TRUE) / sqrt(n),
    SD    = sd(Value, na.rm = TRUE),
    Min   = min(Value, na.rm = TRUE),
    Max   = max(Value, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    Oceanographic_Variable = case_when(
      Oceanographic_Variable == "glider_depth_m" ~ "Glider Depth (m)",
      Oceanographic_Variable == "water_temperature_C" ~ "Water Temperature (°C)",
      Oceanographic_Variable == "salinity_PSU" ~ "Salinity (PSU)",
      Oceanographic_Variable == "oxygen_concentration_μmol_L" ~ "Dissolved Oxygen Concentration (µmol/L)",
      Oceanographic_Variable == "sea_surface_water_temperature_C" ~ "Sea Surface Water Temperature (°C)",
      Oceanographic_Variable == "sea_surface_salinity_PSU" ~ "Sea Surface Salinity (PSU)",
      Oceanographic_Variable == "sea_surface_oxygen_concentration_μmol_L" ~ "Sea Surface Dissolved Oxygen Concentration (µmol/L)",
      Oceanographic_Variable == "bathymetric_depth_m" ~ "Bathymetric Depth (m)",
      Oceanographic_Variable == "bathymetric_slope_deg" ~ "Bathymetric Slope (°)",
      Oceanographic_Variable == "distance_near_shore_m" ~ "Distance to Nearest Shoreline (m)",
      TRUE ~ Oceanographic_Variable
    )
  )

# Reorder rows for table
hbk_summary <- hbk_summary %>%
  mutate(
    Oceanographic_Variable = factor(Oceanographic_Variable,
                                    levels = c(
                                      "Glider Depth (m)",
                                      "Water Temperature (°C)",
                                      "Sea Surface Water Temperature (°C)",
                                      "Salinity (PSU)",
                                      "Sea Surface Salinity (PSU)",
                                      "Dissolved Oxygen Concentration (µmol/L)",
                                      "Sea Surface Dissolved Oxygen Concentration (µmol/L)",
                                      "Bathymetric Depth (m)",
                                      "Bathymetric Slope (°)",
                                      "Distance to Nearest Shoreline (m)"
                                      )
                                    )
  ) %>%
  arrange(Oceanographic_Variable)

# Export as CSV
write_csv(hbk_summary, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_stats_output/sumtab_humpback_UVI2_Around_STX_20250306.csv")
# ----------------------------------------


# ----------------------------------------
# Create BACKRGOUND summary table dataframe
bck_summary <- bck %>%
  select("glider_depth_m",
         "water_temperature_C",
         "salinity_PSU",
         "oxygen_concentration_μmol_L",
         "sea_surface_water_temperature_C",
         "sea_surface_salinity_PSU",
         "sea_surface_oxygen_concentration_μmol_L",
         "bathymetric_depth_m",
         "bathymetric_slope_deg",
         "distance_near_shore_m"
  ) %>%
  pivot_longer(
    cols = everything(),
    names_to  = "Oceanographic_Variable",
    values_to = "Value"
  ) %>%
  group_by(Oceanographic_Variable) %>%
  summarise(
    n     = sum(!is.na(Value)),
    Mean  = mean(Value, na.rm = TRUE),
    SEM   = sd(Value, na.rm = TRUE) / sqrt(n),
    SD    = sd(Value, na.rm = TRUE),
    Min   = min(Value, na.rm = TRUE),
    Max   = max(Value, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    Oceanographic_Variable = case_when(
      Oceanographic_Variable == "glider_depth_m" ~ "Glider Depth (m)",
      Oceanographic_Variable == "water_temperature_C" ~ "Water Temperature (°C)",
      Oceanographic_Variable == "salinity_PSU" ~ "Salinity (PSU)",
      Oceanographic_Variable == "oxygen_concentration_μmol_L" ~ "Dissolved Oxygen Concentration (µmol/L)",
      Oceanographic_Variable == "sea_surface_water_temperature_C" ~ "Sea Surface Water Temperature (°C)",
      Oceanographic_Variable == "sea_surface_salinity_PSU" ~ "Sea Surface Salinity (PSU)",
      Oceanographic_Variable == "sea_surface_oxygen_concentration_μmol_L" ~ "Sea Surface Dissolved Oxygen Concentration (µmol/L)",
      Oceanographic_Variable == "bathymetric_depth_m" ~ "Bathymetric Depth (m)",
      Oceanographic_Variable == "bathymetric_slope_deg" ~ "Bathymetric Slope (°)",
      Oceanographic_Variable == "distance_near_shore_m" ~ "Distance to Nearest Shoreline (m)",
      TRUE ~ Oceanographic_Variable
    )
  )

# Reorder rows for table
bck_summary <- bck_summary %>%
  mutate(
    Oceanographic_Variable = factor(Oceanographic_Variable,
                                    levels = c(
                                      "Glider Depth (m)",
                                      "Water Temperature (°C)",
                                      "Sea Surface Water Temperature (°C)",
                                      "Salinity (PSU)",
                                      "Sea Surface Salinity (PSU)",
                                      "Dissolved Oxygen Concentration (µmol/L)",
                                      "Sea Surface Dissolved Oxygen Concentration (µmol/L)",
                                      "Bathymetric Depth (m)",
                                      "Bathymetric Slope (°)",
                                      "Distance to Nearest Shoreline (m)"
                                    )
    )
  ) %>%
  arrange(Oceanographic_Variable)

# Export as CSV
write_csv(bck_summary, "/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_stats_output/sumtab_LF_background_UVI2_Around_STX_20250306.csv")
# ----------------------------------------


# ----------------------------------------
# Create custom color scheme for oceanographic variables
custom_colors <- c(
  glider_depth_m = "#ffc803",
  water_temperature_C = "#ff8721",
  salinity_PSU = "#ff26d7",
  oxygen_concentration_μmol_L = "#e88aff",
  sea_surface_water_temperature_C = "#8130ff",
  sea_surface_salinity_PSU = "#1c46ff",
  sea_surface_oxygen_concentration_μmol_L = "#75afff",
  bathymetric_depth_m = "#03bcff",
  bathymetric_slope_deg = "#09ebd0",
  distance_near_shore_m = "#00b846"
)
# ----------------------------------------


# ----------------------------------------
# Create vector of clean variable names
clean_var_names <- c(
  glider_depth_m = "Glider Depth (m)",
  water_temperature_C = "Water Temperature (°C)",
  salinity_PSU = "Salinity (PSU)",
  oxygen_concentration_μmol_L = "Dissolved Oxygen Concentration (µmol/L)",
  sea_surface_water_temperature_C = "Sea Surface Water Temperature (°C)",
  sea_surface_salinity_PSU = "Sea Surface Salinity (PSU)",
  sea_surface_oxygen_concentration_μmol_L = "Sea Surface Dissolved Oxygen Concentration (µmol/L)",
  bathymetric_depth_m = "Bathymetric Depth (m)",
  bathymetric_slope_deg = "Bathymetric Slope (°)",
  distance_near_shore_m = "Distance to Nearest Shoreline (m)"
)
# ----------------------------------------


# ----------------------------------------
# Vector of environmental variables to summarize for table (*EXCLUDE glider depth because not really an environmental variable)
env_vars <- c(
  "glider_depth_m",
  "water_temperature_C",
  "salinity_PSU",
  "oxygen_concentration_μmol_L",
  "sea_surface_water_temperature_C",
  "sea_surface_salinity_PSU",
  "sea_surface_oxygen_concentration_μmol_L",
  "bathymetric_depth_m",
  "bathymetric_slope_deg",
  "distance_near_shore_m"
)
# ----------------------------------------


# ----------------------------------------
# Pivot longer *HUMPBACK* DETECTION data
hbk_long <- hbk %>%
  select(all_of(env_vars)) %>%
  pivot_longer(
    cols = everything(),
    names_to = "Oceanographic_Variable",
    values_to = "Value"
  ) %>%
  mutate(
    Oceanographic_Variable = factor(
      Oceanographic_Variable,
      levels = c(
        "glider_depth_m",
        "water_temperature_C",
        "salinity_PSU",
        "oxygen_concentration_μmol_L", 
        "sea_surface_water_temperature_C",
        "sea_surface_salinity_PSU",
        "sea_surface_oxygen_concentration_μmol_L",
        "bathymetric_depth_m",
        "bathymetric_slope_deg",
        "distance_near_shore_m"
      )
    )
  ) %>%
  filter(!is.na(Value)) # drop non-finite values
# ----------------------------------------


# ----------------------------------------
# Pivot longer BACKGROUND data
bck_long <- bck %>%
  select(all_of(env_vars)) %>%
  pivot_longer(
    cols = everything(),
    names_to = "Oceanographic_Variable",
    values_to = "Value"
  ) %>%
  mutate(
    Oceanographic_Variable = factor(
      Oceanographic_Variable,
      levels = c(
        "glider_depth_m",
        "water_temperature_C",
        "salinity_PSU",
        "oxygen_concentration_μmol_L", 
        "sea_surface_water_temperature_C",
        "sea_surface_salinity_PSU",
        "sea_surface_oxygen_concentration_μmol_L",
        "bathymetric_depth_m",
        "bathymetric_slope_deg",
        "distance_near_shore_m"
      )
    )
  ) %>%
  filter(!is.na(Value)) # drop non-finite values
# ----------------------------------------



# ----------------------------------------
# Function to make one density plot for one variable -----------------------
make_density_plot2 <- function(var_name) {
  ggplot() +
    geom_density(
      data = bck_long %>% filter(Oceanographic_Variable == var_name),
      aes(x = Value, y = after_stat(density)),
      fill = "grey45",
      color = "grey35",
      alpha = 0.3,
      linewidth = 0.5
    ) +
    geom_density(
      data = hbk_long %>% filter(Oceanographic_Variable == var_name),
      aes(x = Value, y = after_stat(density)),
      fill = unname(custom_colors[var_name]),
      color = unname(custom_colors[var_name]),
      alpha = 0.35,
      linewidth = 0.75
    ) +
    labs(
      title = stringr::str_wrap(clean_var_names[var_name], width = 35),
      x = NULL,
      y = NULL
    ) +
    theme_minimal(base_size = 7) +
    theme(
      text = element_text(color = "black"),
      plot.title = element_text(
        color = "black",
        face = "bold",
        size = 9.5,
        hjust = 0.5
      ),
      axis.text = element_text(color = "black", size = 7),
      axis.title = element_text(color = "black"),
      axis.ticks.x = element_blank(),
      panel.grid.minor = element_blank(),
      legend.position = "none"
    )
}


# One small custom legend for whole figure -----------------------
legend_stripes <- tibble(
  x = seq(0.555, 0.635, length.out = 10),
  y = 0.5,
  fill = unname(custom_colors)
)
legend_plot <- ggplot() +
  # small grey box
  annotate(
    "rect",
    xmin = 0.10, xmax = 0.14,
    ymin = 0.35, ymax = 0.65,
    fill = "grey45", color = "grey35", linewidth = 0.35
  ) +
  # small multicolor box made of stripes
  geom_tile(
    data = legend_stripes,
    aes(x = x, y = y, fill = fill),
    width = 0.008, height = 0.30,
    inherit.aes = FALSE
  ) +
  scale_fill_identity() +
  # bold labels
  annotate(
    "text",
    x = 0.145, y = 0.5,
    label = "Mission background conditions (low-frequency audio)",
    hjust = 0, vjust = 0.5, size = 2.5, fontface = "bold"
  ) +
  annotate(
    "text",
    x = 0.645, y = 0.5,
    label = "Humpback detection conditions",
    hjust = 0, vjust = 0.5, size = 2.5, fontface = "bold"
  ) +
  xlim(0, 1) +
  ylim(0, 1) +
  theme_void()

# Make each plot -----------------------
p_glider_depth <- make_density_plot2("glider_depth_m")
p_temp         <- make_density_plot2("water_temperature_C")
p_sal          <- make_density_plot2("salinity_PSU")
p_do           <- make_density_plot2("oxygen_concentration_μmol_L")
p_sst          <- make_density_plot2("sea_surface_water_temperature_C")
p_sss          <- make_density_plot2("sea_surface_salinity_PSU")
p_ssdo         <- make_density_plot2("sea_surface_oxygen_concentration_μmol_L")
p_bathy_depth  <- make_density_plot2("bathymetric_depth_m")
p_bathy_slope  <- make_density_plot2("bathymetric_slope_deg")
p_shore        <- make_density_plot2("distance_near_shore_m")

# Main panel layout -----------------------
density_panels <-
  plot_spacer() + p_glider_depth + plot_spacer() +
  p_temp + p_sal + p_do +
  p_sst + p_sss + p_ssdo +
  p_bathy_depth + p_bathy_slope + p_shore +
  plot_layout(ncol = 3)

# Final figure with ONE custom legend
density_CUSTOMSTACK <- density_panels / legend_plot +
  plot_layout(heights = c(18, 1.2))

density_CUSTOMSTACK

# Export plot as PNG -----------------------
ggsave("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/figures/envirovars_density_plots/envirovars_denplot_humpback_LF_background_UVI2_Around_STX_20250306.png", density_CUSTOMSTACK, width = 12, height = 9, dpi = 500)
# --------------------------------------------------------------------------------

