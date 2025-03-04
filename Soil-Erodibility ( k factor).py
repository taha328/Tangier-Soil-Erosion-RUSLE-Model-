import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define the Tangier region (approximate bounding box, adjust as needed)
tangier_region = ee.Geometry.Rectangle([-5.94, 35.64, -5.72, 35.84])  # (minLon, minLat, maxLon, maxLat)

# Load soil property layers
sand = ee.Image("projects/soilgrids-isric/sand_mean").select("sand_0-5cm_mean")
silt = ee.Image("projects/soilgrids-isric/silt_mean").select("silt_0-5cm_mean")
clay = ee.Image("projects/soilgrids-isric/clay_mean").select("clay_0-5cm_mean")
soc = ee.Image("projects/soilgrids-isric/soc_mean").select("soc_0-5cm_mean")

# Merge soil properties into a single image
soil_image = sand.addBands([silt, clay, soc])

# Generate sample points across the region
sampled_data = soil_image.sample(
    region=tangier_region,
    scale=250,  # Adjust resolution as needed
    numPixels=1000,  # Adjust number of sample points
    geometries=True  # Keep geometries if needed
)

# Define export task to Google Drive
task = ee.batch.Export.table.toDrive(
    collection=sampled_data,
    description="Soil_Data_Tangier",
    folder="EarthEngineExports",
    fileNamePrefix="soil_data_tangier",
    fileFormat="CSV"
)

# Start the export task
task.start()
print("Exporting soil data for Tangier to Google Drive... Check GEE Tasks for progress.")
