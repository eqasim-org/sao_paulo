import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import KDTree

def configure(context):
    context.config("data_path")

def execute(context):
    
    df_zones_census = gpd.read_file("%s/Spatial/SC2010_RMSP_CEM_V3_all_state.shp" % context.config("data_path"))
    df_zones_census.crs = {"init":"epsg:4326"}
    df_zones_census_dissolved = df_zones_census#.dissolve(by='AP_2010_CH') 
    df_zones_census_dissolved = df_zones_census_dissolved[['geometry', 'AP_2010_CH']]
    df_zones_census_dissolved.columns = [ "geometry", "zone_id"]
    df_zones_census_dissolved = df_zones_census_dissolved.to_crs({"init":"epsg:29183"})
    df_zones_census_dissolved["zone_id"] = df_zones_census_dissolved["zone_id"].astype(np.int)

    return df_zones_census_dissolved
