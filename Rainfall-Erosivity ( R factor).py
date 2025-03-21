import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define the Tangier region (bounding box)
tangier = ee.Geometry.Rectangle([-5.9, 35.7, -5.7, 35.85])

# Create a grid of points within Tangier region
point_grid = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point(lon, lat)) 
    for lon in ee.List.sequence(-5.9, -5.7, 0.02).getInfo() 
    for lat in ee.List.sequence(35.7, 35.85, 0.02).getInfo()
])

# Load precipitation data from ERA5-Land
era5 = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY") \
    .filterBounds(tangier) \
    .filterDate("2024-07-01", "2025-03-01") \
    .select("total_precipitation_hourly")

# Function to extract precipitation data for each point
def extract_precipitation(image):
    date = image.date().format("YYYY-MM-dd HH:mm")

    # Sample precipitation values at each point
    sampled_points = image.sampleRegions(
        collection=point_grid,
        scale=5000,  # Adjust based on ERA5 resolution
        geometries=True  # Keep geometry to get lat/lon
    ).map(lambda feature: feature.set("date", date))

    return sampled_points

# Apply function to all images
time_series = era5.map(extract_precipitation).flatten()

# Export to Google Drive
task = ee.batch.Export.table.toDrive(
    collection=time_series,
    description='Tangier_Precipitation_with_Coords',
    fileFormat='CSV'
)
task.start()

print("Exporting data to Google Drive... Check Google Earth Engine Tasks.")
