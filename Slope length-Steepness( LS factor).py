import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define Tangier region
tangier_region = ee.Geometry.Rectangle([-5.94, 35.64, -5.72, 35.84])

# Load DEM
dem = ee.Image("USGS/SRTMGL1_003")  # NASA SRTM 30m DEM

# Compute slope in percentage (%)
slope_percent = ee.Terrain.slope(dem).multiply(100)

flow_accum = ee.Terrain.products(dem)

# Cell size (SRTM 30m)
cell_size = ee.Number(30)

# Slope < 1%
m1 = 0.2
n1 = 1   # or 0.3

# Slope >= 1% and <= 3%
m2 = 0.3
n2 = 1   # or 0.4

# Slope > 3% and <= 5%
m3 = 0.4
n3 = 1   # or 0.5

# Slope > 5%
m4 = 0.5
n4 = 1   # or 0.6

# Classify slope into categories
slope_class = ee.Image(0).where(slope_percent.lt(1), 1) \
                         .where(slope_percent.gte(1).And(slope_percent.lte(3)), 2) \
                         .where(slope_percent.gt(3).And(slope_percent.lte(5)), 3) \
                         .where(slope_percent.gt(5), 4)

# Apply corresponding m and n values based on slope class using conditionals
m_factor = ee.Image(m1).where(slope_class.eq(2), m2).where(slope_class.eq(3), m3).where(slope_class.eq(4), m4)
n_factor = ee.Image(n1).where(slope_class.eq(2), n2).where(slope_class.eq(3), n3).where(slope_class.eq(4), n4)


# Calculate LS Factor using the formula with conditional exponents and percentage slope
ls_factor = ((flow_accum.multiply(cell_size).divide(22.13)).pow(m_factor)).multiply(
                (slope_percent.divide(9)).sin().pow(n_factor) # using percentage slope divided by approx 9% as threshold here (similar to 5.14 deg angle)
            )


# Clip LS Factor to Tangier region
ls_factor_clipped = ls_factor.clip(tangier_region)


# Sample LS Factor across Tangier
sampled_data = ls_factor_clipped.sample(
    region=tangier_region,
    scale=30,  # Keep resolution
    numPixels=5000, # Increase sample points if needed
    geometries=True
)

# Export LS Factor data to Google Drive
task = ee.batch.Export.table.toDrive(
    collection=sampled_data,
    description="LS_Factor_Tangier_Corrected",
    folder="EarthEngineExports",
    fileNamePrefix="ls_factor_tangier_corrected",
    fileFormat="CSV"
)


# Start the export task
task.start()
print("Exporting CORRECTED LS Factor data for Tangier to Google Drive... Check GEE Tasks for progress.")