import pandas as pd
import geopandas as gpd
import numpy as np
import shapely.geometry as geo

def configure(context):
    context.stage("synthesis.population.spatial.by_person.primary_locations")
    context.stage("synthesis.population.spatial.by_person.secondary.locations")

    context.stage("synthesis.population.activities")
    context.stage("synthesis.population.sampled")

def execute(context):
    df_home, df_work, df_education = context.stage("synthesis.population.spatial.by_person.primary_locations")
    df_secondary = context.stage("synthesis.population.spatial.by_person.secondary.locations")[0]

    df_persons = context.stage("synthesis.population.sampled")[["person_id", "household_id"]]
    df_locations = context.stage("synthesis.population.activities")[["person_id", "activity_id", "purpose"]]

    # Home locations
    df_home_locations = df_locations[df_locations["purpose"] == "home"]
    df_home_locations = pd.merge(df_home_locations, df_persons, on = "person_id", how = 'left')
    df_home_locations = pd.merge(df_home_locations, df_home[["household_id", "x", "y"]].drop_duplicates(), on = "household_id", how = 'left')
    df_home_locations["destination_id"] = -1
    df_home_locations = df_home_locations[["person_id", "activity_id", "destination_id", "x", "y"]]
    df_home_locations["geometry"] = [geo.Point(px, py) for px, py in list(zip(df_home_locations["x"], df_home_locations["y"]))]

    # Work locations
    df_work_locations = df_locations[df_locations["purpose"] == "work"]
    df_work_locations = pd.merge(df_work_locations, df_work[["person_id", "location_id", "x", "y"]], on = "person_id")
    df_work_locations = df_work_locations[["person_id", "activity_id", "location_id", "x", "y"]]
    df_work_locations["geometry"] = [geo.Point(px, py) for px, py in list(zip(df_work_locations["x"], df_work_locations["y"]))]

    # Education locations
    df_education_locations = df_locations[df_locations["purpose"] == "education"]
    df_education_locations = pd.merge(df_education_locations, df_education[["person_id", "location_id", "x", "y"]], on = "person_id")
    df_education_locations = df_education_locations[["person_id", "activity_id", "location_id", "x", "y"]]
    df_education_locations["geometry"] = [geo.Point(px, py) for px, py in list(zip(df_education_locations["x"], df_education_locations["y"]))]

    # Secondary locations
    df_secondary_locations = df_locations[~df_locations["purpose"].isin(("home", "work", "education"))].copy()
    df_secondary["activity_id"] = df_secondary["trip_index"] + 1
    df_secondary_locations = pd.merge(df_secondary_locations, df_secondary[[
        "person_id", "activity_id", "destination_id", "geometry"
    ]], on = ["person_id", "activity_id"], how = "left")
    df_secondary_locations = df_secondary_locations[["person_id", "activity_id", "destination_id", "geometry"]]

    

    # Validation
    initial_count = len(df_locations)
    df_locations = pd.concat([df_home_locations, df_work_locations, df_education_locations, df_secondary_locations])

    df_locations = df_locations.sort_values(by = ["person_id", "activity_id"])
    final_count = len(df_locations)

    assert initial_count == final_count

    df_locations = gpd.GeoDataFrame(df_locations, crs = dict(init = "epsg:29183"))

    return df_locations
