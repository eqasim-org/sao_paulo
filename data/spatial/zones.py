import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import KDTree

def configure(context, require):
    pass

def execute(context):
    df_zones_hts = gpd.read_file("%s/Spatial/Zonas_2017_region.shp" % context.config["raw_data_path"])
    df_zones_hts.crs = {"init" : "EPSG:29183"}    
    df_zones_hts = df_zones_hts[['NumeroZona', 'geometry']]
    df_zones_hts.columns = ["zone_id", "geometry"]
    
    df_zones_census = gpd.read_file("%s/Spatial/SC2010_RMSP_CEM_V3_merged.shp" % context.config["raw_data_path"])
    df_zones_census.crs = {"init" : "EPSG:4326"}
    df_zones_census = df_zones_census[['geometry', 'AP_2010_CH']]
    df_zones_census.columns = [ "geometry", "zone_id"]
    df_zones_census = df_zones_census.to_crs({"init" : "EPSG:29183"})
    df_zones_census["zone_id"] = df_zones_census["zone_id"].astype(np.int)

    return df_zones_census,df_zones_hts
