import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np
from sklearn.neighbors import KDTree
import numpy.linalg as la
import data.spatial.utils

def configure(context):
    context.stage("data.spatial.zones")
    context.stage("data.opportunities.extract_roads_osm")


def execute(context):   
    df_zones = context.stage("data.spatial.zones")[0]
	
    df_opportunities = context.stage("data.opportunities.extract_roads_osm") 
    df_opportunities = df_opportunities[["x", "y"]]
    df_opportunities.columns = ["x", "y"]    
    
    df_opportunities["offers_work"] = True
    df_opportunities["offers_other"] = True
    df_opportunities["offers_leisure"] = True
    df_opportunities["offers_shop"] = True 
    df_opportunities["offers_education"] = False
    df_opportunities["offers_home"] = True
    
    df_opportunities = data.spatial.utils.to_gpd(df_opportunities, crs = {"init" : "EPSG:4326"}).to_crs({"init" : "EPSG:29183"})
    
    ## read the educational facilities and attach them to the opportunities
    
    df_education = pd.read_csv("%s/escolas_enderecos.csv" % context.config["raw_data_path"])
    df_education.rename(columns={'LATITUDE':'y', 'LONGITUDE':'x'}, inplace=True)
    df_facilities_education = df_education[['x', 'y']].copy()

    df_facilities_education["offers_work"] = True
    df_facilities_education["offers_other"] = True
    df_facilities_education["offers_leisure"] = False
    df_facilities_education["offers_shop"] = False
    df_facilities_education["offers_education"] = True
    df_facilities_education["offers_home"] = False

    df_facilities_education = data.spatial.utils.to_gpd(df_facilities_education, crs = {"init" : "EPSG:4326"}).to_crs({"init" : "EPSG:29183"})
    
    df_opportunities = pd.concat([df_opportunities, df_facilities_education], sort = True)
    df_opportunities["x"] = df_opportunities["geometry"].x
    df_opportunities["y"] = df_opportunities["geometry"].y
    df_opportunities["location_id"] = np.arange(len(df_opportunities)) 
    df_opportunities = data.spatial.utils.impute(df_opportunities, df_zones, "location_id", "zone_id", fix_by_distance = False).dropna()
    
    return df_opportunities
