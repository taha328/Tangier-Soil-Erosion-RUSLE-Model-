import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

tangier_region = ee.Geometry.Rectangle([-5.94, 35.64, -5.72, 35.84])

# Sentinel-2 date range for cloud-free composite (representing growing season or relevant period)
start_date = "2023-06-01"
end_date = "2025-03-01"

# Cloud cover threshold for Sentinel-2 imagery (%)
cloud_cover_threshold = 5

# C-factor equation parameters (Exponential NDVI-based model - adjust based on literature/calibration)
c_factor_equation = "exp_ndvi"  # Options: "exp_ndvi" (exponential NDVI),  (more options can be added later)
c_factor_alpha = 2  # 'alpha' parameter for exp(-alpha * NDVI) - adjust based on regional calibration
c_factor_max_value = 1.0 # Maximum C-factor value (e.g., for bare soil)

# Output settings
output_folder = "EarthEngineOutputs"  # Google Drive folder for outputs
output_name_prefix = "C_Factor_Tangier"
output_scale = 30 # Resolution for raster export and sampling (Sentinel-2 resolution is 10m, but 30m can be reasonable for RUSLE factors)


sentinel = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") # Using Surface Reflectance Harmonized collection
sentinel = sentinel.filterBounds(tangier_region)
sentinel = sentinel.filterDate(start_date, end_date)
sentinel = sentinel.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_cover_threshold))
sentinel = sentinel.median()

# Compute NDVI: (NIR - Red) / (NIR + Red) - Sentinel-2 bands B8 (NIR), B4 (Red)
ndvi = sentinel.normalizedDifference(["B8", "B4"]).rename("NDVI")

# --- C-Factor Calculation based on selected equation ---
if c_factor_equation == "exp_ndvi":
    # Exponential NDVI-based C-factor equation: C = C_max * exp(-alpha * NDVI)
    alpha_param = ee.Number(c_factor_alpha) # Get alpha from configuration
    c_max_param = ee.Number(c_factor_max_value) # Get C_max from configuration
    c_factor = ndvi.expression(
        "C_max * exp(-alpha * NDVI)", {
            'C_max': c_max_param,
            'alpha': alpha_param,
            'NDVI': ndvi
        }).rename("C_Factor")
    print(f'C-factor calculated using Exponential NDVI equation: C = C_max * exp(-alpha * NDVI), alpha={c_factor_alpha}, C_max={c_factor_max_value}')
else:
    raise ValueError(f"C-factor equation type '{c_factor_equation}' not recognized. Please choose from: 'exp_ndvi'")


# Clip C Factor to Tangier region
c_factor_clipped = c_factor.clip(tangier_region)

# --- Print min/max values for NDVI and C-factor for quality check ---
ndvi_range = ndvi.reduceRegion(ee.Reducer.minMax(), tangier_region, scale=output_scale).getInfo()
c_factor_range = c_factor_clipped.reduceRegion(ee.Reducer.minMax(), tangier_region, scale=output_scale).getInfo()
print('NDVI range in Tangier region:', ndvi_range)
print('C-factor range in Tangier region:', c_factor_range)


# --- Sample C Factor across Tangier for CSV export ---
sampled_data_csv = c_factor_clipped.sample(
    region=tangier_region,
    scale=output_scale,
    numPixels=5000,  # Increased sample density for better representation
    geometries=True,
    seed=0 # Set seed for reproducibility of random sampling
)


# --- Export C Factor data as GeoTIFF raster ---
export_task_raster = ee.batch.Export.image.toDrive(
    image=c_factor_clipped,
    description=f"{output_name_prefix}_Raster_GeoTIFF",
    folder=output_folder,
    fileNamePrefix=f"{output_name_prefix}_raster",
    region=tangier_region,
    scale=output_scale,
    crs='EPSG:4326',
    fileFormat='GeoTIFF',
    formatOptions={'cloudOptimized': True}
)
export_task_raster.start()

# --- Export Sampled C Factor data as CSV table ---
export_task_csv = ee.batch.Export.table.toDrive(
    collection=sampled_data_csv,
    description=f"{output_name_prefix}_Sampled_CSV",
    folder=output_folder,
    fileNamePrefix=f"{output_name_prefix}_sampled",
    fileFormat='CSV'
)
export_task_csv.start()


print(f"Exporting C Factor RASTER (GeoTIFF) to Google Drive folder: '{output_folder}' as '{output_name_prefix}_raster.tif'. Task started. Check GEE Tasks.")
print(f"Exporting Sampled C Factor data as CSV to Google Drive folder: '{output_folder}' as '{output_name_prefix}_sampled.csv'. Task started. Check GEE Tasks.")
print("\n--- C Factor Calculation and Export script completed ---")