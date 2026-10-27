# Last updated on July 17, 2026


library(RStoolbox)
library(raster)  # RStoolbox requires raster objects not terra
library(ggplot2) # for biplot
library(ggrepel)

# Convert terra stack to raster for RStoolbox (rast() needs terra package)
env_stack <- terra::rast("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/1_env_stack_output/maxent_env_stack_1km_UTM20N.tif")

# RUN PCA ꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘ
pca_result <- rasterPCA(env_stack, nComp = 3, spca = TRUE)
summary(pca_result$model)

  # Importance of components:                                                          
  #                           Comp.1    Comp.2    Comp.3    Comp.4     Comp.5    Comp.6
  # Standard deviation     1.4496495 1.3709921 0.9217599 0.7786842 0.62262823 0.4186177
  # Proportion of Variance 0.3502473 0.3132699 0.1416069 0.1010582 0.06461098 0.0292068
  # Cumulative Proportion  0.3502473 0.6635172 0.8051240 0.9061822 0.97079320 1.0000000

# Loadings (which variables drive each PC)
pca_result$model$loadings

  # Loadings:                                                
  #             Comp.1 Comp.2 Comp.3 Comp.4 Comp.5 Comp.6    
  # bathymetry   0.426  0.416  0.129  0.474  0.585  0.249    
  # slope       -0.195 -0.426 -0.741  0.318  0.359           
  # dist_shore  -0.279  0.534 -0.417 -0.407         0.545    
  # SST         -0.556  0.294  0.176 -0.137  0.502 -0.550    
  # SSS          0.482 -0.268        -0.700  0.446           
  # CHL-a_log   -0.402 -0.449  0.475         0.278  0.577    
  #                                                          
  #                 Comp.1 Comp.2 Comp.3 Comp.4 Comp.5 Comp.6
  # SS loadings      1.000  1.000  1.000  1.000  1.000  1.000
  # Proportion Var   0.167  0.167  0.167  0.167  0.167  0.167
  # Cumulative Var   0.167  0.333  0.500  0.667  0.833  1.000

# Plot PC1, PC2, PC3 and export as PNGs
plot(pca_result$map[[1]], main = "PC1")
plot(pca_result$map[[2]], main = "PC2")
plot(pca_result$map[[3]], main = "PC3")

for (i in 1:3) {
  png(paste0("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/2_pca_output/pca_pc", i, ".png"), width = 8, height = 6, units = "in", res = 300)
  plot(pca_result$map[[i]], main = paste0("PC", i))
  dev.off()
}

# ******************************************************************************
# PC1 (35%): offshore/thermal gradient (driven by SST (-0.61), dist_shore (-0.54), SSS (0.54)); higher values = shallower, saltier, cooler nearshore
# PC2 (28%): bathymetric/slope structure (driven by bathymetry (0.56), slope (-0.66), Chl_log (-0.45)); captures seafloor complexity
# PC3 (18%): productivity signal (Chl_log dominates (0.72))
# PC1–PC3 cumulatively explain 81% of variance
# ******************************************************************************


# PCA BIPLOTS ꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘꁘ

# Extract all 3 PC scores
scores <- data.frame(
  Comp.1 = as.vector(raster::values(pca_result$map[[1]])),
  Comp.2 = as.vector(raster::values(pca_result$map[[2]])),
  Comp.3 = as.vector(raster::values(pca_result$map[[3]]))
)
scores <- na.omit(scores)

# Sample once — used for both biplots
set.seed(42)
idx <- sample(nrow(scores), 2000)
scores_sample <- scores[idx, ]
scale_factor <- 3

# PC1 and PC2 PLOT -------------------------------------------------------------
# Loadings for biplot
loadings_df12 <- as.data.frame(pca_result$model$loadings[, 1:2])
colnames(loadings_df12) <- c("Comp.1", "Comp.2")
loadings_df12$variable <- rownames(loadings_df12)
loadings_df12$nudge_x <- c(0.2, 0.2, -0.3, -0.2, 0.2, -0.3) # bathymetry, slope, dist_shore, SST, SSS, Chl_log
loadings_df12$nudge_y <- c(0.2, -0.2, 0.2, 0.05, 0, -0.15)

# Create manual biplot for PC1 and PC2 and export as PNG
p_pc1pc2 <- ggplot() +
  geom_hline(yintercept = 0, linetype = "dashed", color = "black", linewidth = 0.25) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "black", linewidth = 0.25) +
  geom_point(data = scores_sample, aes(x = Comp.1, y = Comp.2),
             color = "grey50", alpha = 0.25, size = 1) +
  geom_segment(data = loadings_df12,
               aes(x = 0, y = 0,
                   xend = Comp.1 * scale_factor,
                   yend = Comp.2 * scale_factor),
               arrow = arrow(length = unit(0.25, "cm"), type = "open"),
               color = "blue", linewidth = 0.75) +
  geom_label_repel(data = loadings_df12,
                   aes(x = Comp.1 * scale_factor,
                       y = Comp.2 * scale_factor,
                       label = variable),
                   color = "blue", size = 3, fontface = "bold",
                   fill = "#ebf2ff", label.size = 0.15,
                   label.padding = unit(0.15, "lines"),
                   nudge_x = loadings_df12$nudge_x,
                   nudge_y = loadings_df12$nudge_y,
                   segment.color = NA,
                   max.overlaps = Inf) +
  labs(title = "PCA Biplot (PC1 and PC2)",
       x = "PC1 (35.1%)", y = "PC2 (27.8%)") +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold", hjust = 0.5))

png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/2_pca_output/pca_biplot_pc1_pc2.png", width = 8, height = 8, units = "in", res = 300)
print(p_pc1pc2)
dev.off()

# PC2 and PC3 PLOT -------------------------------------------------------------
# Loadings for biplot
loadings_df23 <- as.data.frame(pca_result$model$loadings[, 2:3])
colnames(loadings_df23) <- c("Comp.2", "Comp.3")
loadings_df23$variable <- rownames(loadings_df23)
loadings_df23$nudge_x <- c(0.2, 0.2, -0.3, -0.2, 0.2, -0.3) # bathymetry, slope, dist_shore, SST, SSS, Chl_log
loadings_df23$nudge_y <- c(0.2, -0.2, 0.2, 0.05, 0, -0.15)

# Create manual biplot for PC2 and PC3 and export as PNG
p_pc2pc3 <- ggplot() +
  geom_hline(yintercept = 0, linetype = "dashed", color = "black", linewidth = 0.25) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "black", linewidth = 0.25) +
  geom_point(data = scores_sample, aes(x = Comp.2, y = Comp.3),
             color = "grey50", alpha = 0.25, size = 1) +
  geom_segment(data = loadings_df23,
               aes(x = 0, y = 0,
                   xend = Comp.2 * scale_factor,
                   yend = Comp.3 * scale_factor),
               arrow = arrow(length = unit(0.25, "cm"), type = "open"),
               color = "blue", linewidth = 0.75) +
  geom_label_repel(data = loadings_df23,
                   aes(x = Comp.2 * scale_factor,
                       y = Comp.3 * scale_factor,
                       label = variable),
                   color = "blue", size = 3, fontface = "bold",
                   fill = "#ebf2ff", label.size = 0.15,
                   label.padding = unit(0.15, "lines"),
                   nudge_x = loadings_df23$nudge_x,
                   nudge_y = loadings_df23$nudge_y,
                   segment.color = NA,
                   max.overlaps = Inf) +
  labs(title = "PCA Biplot (PC2 and PC3)",
       x = "PC2 (27.8%)", y = "PC3 (18.0%)") +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold", hjust = 0.5))

png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/2_pca_output/pca_biplot_pc2_pc3.png", width = 8, height = 8, units = "in", res = 300)
print(p_pc2pc3)
dev.off()

# PC1 and PC3 PLOT -------------------------------------------------------------
# Loadings for biplot
loadings_df13 <- as.data.frame(pca_result$model$loadings[, c(1,3)])
colnames(loadings_df13) <- c("Comp.1", "Comp.3")
loadings_df13$variable <- rownames(loadings_df13)
loadings_df13$nudge_x <- c(0.2, 0.2, -0.3, -0.2, 0.2, -0.3) # bathymetry, slope, dist_shore, SST, SSS, Chl_log
loadings_df13$nudge_y <- c(0.2, -0.2, 0.2, 0.05, 0, -0.15)

# Create manual biplot for PC1 and PC3 and export as PNG
p_pc1pc3 <- ggplot() +
  geom_hline(yintercept = 0, linetype = "dashed", color = "black", linewidth = 0.25) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "black", linewidth = 0.25) +
  geom_point(data = scores_sample, aes(x = Comp.1, y = Comp.3),
             color = "grey50", alpha = 0.25, size = 1) +
  geom_segment(data = loadings_df13,
               aes(x = 0, y = 0,
                   xend = Comp.1 * scale_factor,
                   yend = Comp.3 * scale_factor),
               arrow = arrow(length = unit(0.25, "cm"), type = "open"),
               color = "blue", linewidth = 0.75) +
  geom_label_repel(data = loadings_df13,
                   aes(x = Comp.1 * scale_factor,
                       y = Comp.3 * scale_factor,
                       label = variable),
                   color = "blue", size = 3, fontface = "bold",
                   fill = "#ebf2ff", label.size = 0.15,
                   label.padding = unit(0.15, "lines"),
                   nudge_x = loadings_df13$nudge_x,
                   nudge_y = loadings_df13$nudge_y,
                   segment.color = NA,
                   max.overlaps = Inf) +
  labs(title = "PCA Biplot (PC1 and PC3)",
       x = "PC1 (35.1%)", y = "PC3 (18.0%)") +
  theme_classic(base_size = 10) +
  theme(plot.title = element_text(face = "bold", hjust = 0.5))

png("/Users/keileygregory/THESIS_REPOSITORIES/MISSION_REPOSITORIES/UVI2_Around_STX_20250306/data/6_data_analysis_outputs/maxent_model/LF_maxent_model/2_pca_output/pca_biplot_pc1_pc3.png",
    width = 8, height = 8, units = "in", res = 300)
print(p_pc1pc3)
dev.off()
