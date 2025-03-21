import ee

# Initialize Earth Engine
try:
    ee.Initialize(project='ee-tahaelouali2016')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='ee-tahaelouali2016')

# Define Tangier region
tangier_region = ee.Geometry.Rectangle([-5.94, 35.64, -5.72, 35.84])

# Load DEM (Still needed for slope)
dem = ee.Image("USGS/SRTMGL1_003")  # NASA SRTM 30m DEM

# Compute slope in percentage (%) from SRTM DEM
slope_percent = ee.Terrain.slope(dem).multiply(100)

# Load WWF HydroSHEDS Flow Accumulation (3s resolution)

hydro_sheds_fa = ee.Image("WWF/HydroSHEDS/15ACC") # Corrected Image ID
flow_accum = hydro_sheds_fa.select('b1').clip(tangier_region) 

# Cell size for HydroSHEDS (3s resolution is approximately 90m at equator, and slightly less at higher latitudes. Using 90m approximation.)
cell_size_hydrosheds = ee.Number(90) # Approximate cell size for HydroSHEDS 3s

# Define slope classes and corresponding m, n values (as before)
m_values = [0.2, 0.3, 0.4, 0.5]
n_values = [1, 1, 1, 1]

# Classify slope into categories (as before using SRTM slope)
slope_class = ee.Image(0).where(slope_percent.lt(1), 1) \
                         .where(slope_percent.gte(1).And(slope_percent.lte(3)), 2) \
                         .where(slope_percent.gt(3).And(slope_percent.lte(5)), 3) \
                         .where(slope_percent.gt(5), 4)

# Assign m and n factors based on slope class (as before)
m_factor = ee.Image(m_values[0]).where(slope_class.eq(2), m_values[1]) \
                               .where(slope_class.eq(3), m_values[2]) \
                               .where(slope_class.eq(4), m_values[3])

n_factor = ee.Image(n_values[0]).where(slope_class.eq(2), n_values[1]) \
                               .where(slope_class.eq(3), n_values[2]) \
                               .where(slope_class.eq(4), n_values[3])

# Calculate LS Factor using the correct formula, now using HydroSHEDS FA
# NOTE: 22.13 constant is typically related to ~30m cell size. Using ~90m HydroSHEDS, constant may need adjustment depending on formula sensitivity.  Let's start with 22.13.
ls_factor = ((flow_accum.multiply(cell_size_hydrosheds).divide(22.13)).pow(m_factor)).multiply( # Using HydroSHEDS FA and cell_size
                (slope_percent.divide(100)).tan().pow(n_factor)
            ).rename('LS_factor') # Rename band to 'LS_factor'

# Clip LS Factor to Tangier region (already clipped flow_accum during loading, but re-clip LS_factor for good measure)
ls_factor_clipped = ls_factor.clip(tangier_region)

# Sample LS Factor across Tangier
sampled_data = ls_factor_clipped.sample(
    region=tangier_region,
    scale=90, # Adjust scale to HydroSHEDS resolution (~90m) - Or higher if needed.
    numPixels=5000,
    geometries=True
)

# Export LS Factor data to Google Drive
task = ee.batch.Export.table.toDrive(
    collection=sampled_data,
    description="LS_Factor_Tangier_HydroSHEDS", # Descriptive description
    folder="EarthEngineExports",
    fileNamePrefix="ls_factor_tangier_hydrosheds", # Descriptive filename
    fileFormat="CSV"
)

# Start the export task
task.start()
print("Exporting LS Factor data for Tangier using HydroSHEDS to Google Drive... Check GEE Tasks for progress.")