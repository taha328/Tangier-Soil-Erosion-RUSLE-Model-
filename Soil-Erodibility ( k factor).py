import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define the Tangier region (bounding box)
tangier_region = ee.Geometry.Rectangle([-5.94, 35.64, -5.72, 35.84])

# Load soil property layers
sand = ee.Image("projects/soilgrids-isric/sand_mean").select("sand_0-5cm_mean")
silt = ee.Image("projects/soilgrids-isric/silt_mean").select("silt_0-5cm_mean")
clay = ee.Image("projects/soilgrids-isric/clay_mean").select("clay_0-5cm_mean")
soc = ee.Image("projects/soilgrids-isric/soc_mean").select("soc_0-5cm_mean")

# Convert SOC from g/kg to percentage
soc_percent = soc.divide(10)  

# Compute K-factor using the Williams equation
k_factor = (ee.Image(0.2).add(ee.Image(0.3).multiply((clay.multiply(-0.0256)).exp())))
k_factor = k_factor.multiply(((silt.add(sand)).divide(100)).pow(1.14))
k_factor = k_factor.multiply((ee.Image(1).subtract(soc_percent.divide(100))))

# Merge K-factor with soil properties
soil_image = sand.addBands([silt, clay, soc, k_factor.rename("K_factor")])

# Generate sample points across the region
sampled_data = soil_image.sample(
    region=tangier_region,
    scale=250,
    numPixels=1000,
    geometries=True
)

# Export task to Google Drive
task = ee.batch.Export.table.toDrive(
    collection=sampled_data,
    description="Soil_Data_Tangier",
    folder="EarthEngineExports",
    fileNamePrefix="soil_data_tangier",
    fileFormat="CSV"
)

# Start the export task
task.start()
print("Exporting soil data with K-factor for Tangier to Google Drive...")
