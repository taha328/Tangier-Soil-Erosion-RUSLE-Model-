import ee
import json
import pandas as pd

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define Tangier region (bounding box)
tangier = ee.Geometry.Rectangle([-5.9, 35.7, -5.7, 35.85])

# Load precipitation data from ERA5-Land
chirps = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY") \
    .filterBounds(tangier) \
    .filterDate("2024-07-01", "2025-03-01") \
    .select("total_precipitation_hourly")  # ✅ Correct band name

# Function to extract precipitation data
def extract_precipitation(image):
    date = image.date().format("YYYY-MM-dd HH:mm")
    mean_precip = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=tangier,
        scale=5000
    ).get("total_precipitation_hourly")
    
    # Ensure no missing values
    return ee.Feature(None, {"date": date, "total_precipitation_hourly": ee.Algorithms.If(mean_precip, mean_precip, 0)})

# Limit results to avoid "5000 elements" error
time_series = chirps.map(extract_precipitation).limit(5000)

# Export to Google Drive (avoids getInfo() limit)
task = ee.batch.Export.table.toDrive(
    collection=time_series,
    description='Tangier_Precipitation',
    fileFormat='CSV'
)
task.start()

print("Exporting data to Google Drive... Check Google Earth Engine Tasks.")
