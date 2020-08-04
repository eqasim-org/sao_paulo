import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import KDTree

def configure(context):
    context.config("data_path")
    context.config("shapefile_name")

def execute(context):
    
    df_zones_census = gpd.read_file("%s/Spatial/%s" % (context.config("data_path"), context.config("shapefile_name")))
    df_zones_census.crs = {"init":"epsg:4326"}
    df_zones_census_dissolved = df_zones_census#.dissolve(by='AP_2010_CH') 
    df_zones_census_dissolved = df_zones_census_dissolved[['geometry', 'AP_2010_CH']]
    df_zones_census_dissolved.columns = [ "geometry", "zone_id"]
    df_zones_census_dissolved = df_zones_census_dissolved.to_crs({"init":"epsg:29183"})
    df_zones_census_dissolved["zone_id"] = df_zones_census_dissolved["zone_id"].astype(np.int)

    return df_zones_census_dissolved
