from tqdm import tqdm
import pandas as pd
import numpy as np
import geopandas as gpd
import pyreadstat
def configure(context, require):
    require.stage("data.census.raw")
    require.stage("data.spatial.zones")


def execute(context):
    df_census = context.stage("data.census.raw")
    df_census["zone_id"] = df_census["zone_id"].astype(np.int)
    #read the zonal system and remove those outside of the area
    df_zones = context.stage("data.spatial.zones")[0]
    df_zones["zone_id"] = df_zones["zone_id"].astype(np.int)

    
    df = pd.merge(df_census, df_zones, how = "left", on = "zone_id")
    
    f = df["geometry"].isna()
    print("Removing %d/%d (%.2f%%) persons from census (outside of area)" % (
        np.sum(f), len(df), 100.0 * np.sum(f) / len(df)
    ))
    df = df[~f]
    zone_id = df["zone_id"].values.tolist()
    

    # Import shapefiles defining the different zones
    center = gpd.read_file("%s/Spatial/SC2010_RMSP_CEM_V3_merged_center.shp" % context.config["raw_data_path"])
    center = center["AP_2010_CH"].values.tolist()
    city = gpd.read_file("%s/Spatial/SC2010_RMSP_CEM_V3_merged_city.shp" % context.config["raw_data_path"])
    city = city["AP_2010_CH"].values.tolist()
    county = gpd.read_file("%s/Spatial/SC2010_RMSP_CEM_V3_merged_all_state.shp" % context.config["raw_data_path"])
    county = county["AP_2010_CH"].values.tolist()

    # New localization variable: 3 in the city center, 2 in the Sao-Paulo city and 1 otherwise
    sp_area = [3 * (z in center) + 2 * (z in city and z not in center) + 1 * (z in county and z not in city) for z in zone_id]
    df["area_id"] = sp_area

    # Attributes
    df.loc[df["gender"] == 1, "sex"] = "male"
    df.loc[df["gender"] == 2, "sex"] = "female"
    df["sex"] = df["sex"].astype("category")

    df["__employment"] = df["employment"]
    df.loc[df["__employment"] == 1, "employment"] = "yes"
    df.loc[df["__employment"] == 2, "employment"] = "no"
    df.loc[df["__employment"] == 3, "employment"] = "student"
    df["employment"] = df["employment"].astype("category")

    df["age"] = df["age"].astype(np.int)
    df["binary_car_availability"] = (df["carAvailability"] == 1) | (df["motorcycleAvailability"] == 1)
    #df["income"] = np.round(df["householdIncome"] / df["numberOfMembers"])
    df["hhlIncome"] = df["householdIncome"]

    # Create household ID
    i = 0
    hhl_number = 1
    hhl_id = []
    while i < len(df):
        nom = df.iloc[i]["numberOfMembers"]
        nom = int(nom)
        for j in range(nom):
            hhl_id.append(hhl_number)
        hhl_number += 1
        i += nom

    df["household_id"] = hhl_id
    
    # Clean up
    df = df[[
        "person_id", "weight", "hhlIncome",
        "zone_id", "age", "sex", "employment", "binary_car_availability",
        "area_id", 
        "household_id", "numberOfMembers"
    ]]


    return df
