import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define Tangier region (adjust coordinates if needed)
tangier_region = ee.Geometry.Rectangle([-5.94, 35.64, -5.72, 35.84])

# Output settings
output_folder = "EarthEngineOutputs"
output_name_prefix = "P_Factor_Tangier" # Updated output name for P-factor only
output_scale = 30


# --- P-FACTOR CONFIGURATION (LULC-BASED) ---
p_factor_method = "lulc_based"  # Using LULC-based method
lulc_dataset = "COPERNICUS/Landcover/100m/Proba-V-C3/Global"  # Copernicus Global Land Service LULC (100m) - Good starting point, but consider alternatives
lulc_year = "2019" # Year of the LULC data


p_factor_values_lulc = {
    "forest": 0.1,
    "grassland": 0.3,
    "cropland": 0.6,
    "urban": 0.9,
    "water": 0.01,
    "shrubland": 0.4,
    "bare": 1.0
    # Add more LULC classes if needed and their corresponding P-factor values.
}


# Load LULC dataset
lulc_image = ee.ImageCollection(lulc_dataset).filterDate(f'{lulc_year}-01-01', f'{lulc_year}-12-31').first() # Get LULC for the specified year.
lulc_band_name = 'discrete_classification' # Band name for land cover classification in Copernicus LULC

if p_factor_method == "lulc_based":
    print("P-factor calculated using LULC-based method.")

    # --- P-factor Remapping based on LULC classes ---
    p_factor_image = ee.Image(0).rename('P_Factor') # Initialize P-factor image to 0.

    # --- Remapping logic for Copernicus LULC classes (ADJUST CLASS CODES AND P-FACTOR VALUES!) ---
    # Copernicus LULC classes are numerically coded.  Refer to dataset documentation for specific class codes.
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(10)  , p_factor_values_lulc["cropland"])   # Cropland, rainfed
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(20)  , p_factor_values_lulc["cropland"])   # Cropland, irrigated or post-flooding
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(30)  , p_factor_values_lulc["grassland"])  # Herbaceous vegetation
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(40)  , p_factor_values_lulc["forest"])     # Tree cover, broadleaved, deciduous, closed to open
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(50)  , p_factor_values_lulc["forest"])     # Tree cover, broadleaved, deciduous, closed
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(60)  , p_factor_values_lulc["forest"])     # Tree cover, broadleaved, deciduous, open
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(70)  , p_factor_values_lulc["forest"])     # Tree cover, needleleaved, evergreen, closed to open
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(80)  , p_factor_values_lulc["forest"])     # Tree cover, needleleaved, evergreen, closed
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(90)  , p_factor_values_lulc["forest"])     # Tree cover, needleleaved, evergreen, open
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(100) , p_factor_values_lulc["forest"])    # Tree cover, mixed leaf type, closed to open
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(110) , p_factor_values_lulc["forest"])    # Tree cover, mosaic
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(120) , p_factor_values_lulc["shrubland"]) # Shrubland
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(130) , p_factor_values_lulc["shrubland"]) # Shrubland, mosaic
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(140) , p_factor_values_lulc["grassland"]) # Herbaceous vegetation, mosaic
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(160) , p_factor_values_lulc["urban"])     # Built-up
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(170) , p_factor_values_lulc["bare"])      # Bare / sparse vegetation
    p_factor_image = p_factor_image.where(lulc_image.select(lulc_band_name).eq(180) , p_factor_values_lulc["water"])     # Water
    # Add more LULC classes and remapping as needed for your LULC dataset

else:
    raise ValueError(f"P-factor method '{p_factor_method}' not recognized.")

p_factor_clipped = p_factor_image.clip(tangier_region) # Clip P-factor


# ------------------------ PRINT MIN/MAX VALUES FOR QUALITY CHECK (P-factor ONLY) ------------------------
p_factor_range = p_factor_clipped.reduceRegion(ee.Reducer.minMax(), tangier_region, scale=output_scale).getInfo()
print('P-factor range in Tangier region:', p_factor_range) # Print P-factor range


# ------------------------ SAMPLE P FACTOR FOR CSV EXPORT (P-factor ONLY) ------------------------
sampled_data_csv = p_factor_clipped.sample( # Sample directly from p_factor_clipped
    region=tangier_region,
    scale=output_scale,
    numPixels=5000,
    geometries=True,
    seed=0
)

export_task_raster = ee.batch.Export.image.toDrive(
    image=p_factor_clipped, # Export p_factor_clipped directly
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

# ------------------------ EXPORT SAMPLED P FACTOR DATA AS CSV TABLE (P-factor ONLY) ------------------------
export_task_csv = ee.batch.Export.table.toDrive(
    collection=sampled_data_csv,
    description=f"{output_name_prefix}_Sampled_CSV",
    folder=output_folder,
    fileNamePrefix=f"{output_name_prefix}_sampled",
    fileFormat='CSV'
)
export_task_csv.start()


print(f"Exporting P Factor RASTER (GeoTIFF) to Google Drive folder: '{output_folder}' as '{output_name_prefix}_raster.tif'. Task started. Check GEE Tasks.")
print(f"Exporting Sampled P Factor data as CSV to Google Drive folder: '{output_folder}' as '{output_name_prefix}_sampled.csv'. Task started. Check GEE Tasks.")
print("\n--- P Factor Calculation and Export script completed ---")