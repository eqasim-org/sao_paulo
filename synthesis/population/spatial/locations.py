import gzip
from tqdm import tqdm
import numpy as np
import io
import matsim.writers
import pandas as pd

def configure(context):
    context.stage("synthesis.population.activities")
    context.stage("synthesis.population.spatial.by_person.primary_locations")
    context.stage("synthesis.population.spatial.by_person.secondary.locations")

def execute(context):
    df_activities = context.stage("synthesis.population.activities")
    df_home, df_work, df_education = context.stage("synthesis.population.spatial.by_person.primary_locations")
    df_secondary = context.stage("synthesis.population.spatial.by_person.secondary.locations")

    df_home = pd.merge(df_activities[df_activities["purpose"] == "home"][[
        "person_id", "activity_id"
    ]], df_home, how = "inner", on = ["person_id"])#[["person_id", "activity_id", "x", "y"]]
    #df_home["location_id"] = np.nan
    assert(len(df_home) == np.count_nonzero(df_activities["purpose"] == "home"))

    df_work = pd.merge(df_activities[df_activities["purpose"] == "work"][[
        "person_id", "activity_id"
    ]], df_work, how = "inner", on = ["person_id"])
    assert(len(df_work) == np.count_nonzero(df_activities["purpose"] == "work"))

    df_education = pd.merge(df_activities[df_activities["purpose"] == "education"][[
        "person_id", "activity_id"
    ]], df_education, how = "inner", on = ["person_id"])
    assert(len(df_education) == np.count_nonzero(df_activities["purpose"] == "education"))

    df_locations = pd.concat([df_home, df_work, df_education])
    assert(len(df_locations) == len(df_locations.drop_duplicates(["person_id", "activity_id"])))

    df_locations = pd.merge(df_activities, df_locations, how = "left", on = ["person_id", "activity_id"])

    # Set unknown locations to home for the moment
    df_home = context.stage("synthesis.population.spatial.by_person.primary_locations")[0]

    df_home["home_x"] = df_home["x"]
    df_home["home_y"] = df_home["y"]
    df_home = df_home[["person_id", "home_x", "home_y"]]

    df_locations = pd.merge(df_locations, df_home, on = "person_id")

    f = df_locations["location_id"].isna()
    df_locations.loc[f, "x"] = df_locations.loc[f, "home_x"]
    df_locations.loc[f, "y"] = df_locations.loc[f, "home_y"]

    df_locations = df_locations[["person_id", "activity_id", "x", "y", "location_id"]]

    # Secondary locations
    df_secondary_locations = df_locations[~df_locations["purpose"].isin(("home", "work", "education"))].copy()
    df_secondary["activity_index"] = df_secondary["trip_index"] + 1
    df_secondary_locations = pd.merge(df_secondary_locations, df_secondary[[
        "person_id", "activity_index", "destination_id", "geometry"
    ]], on = ["person_id", "activity_index"], how = "left")
    df_secondary_locations = df_secondary_locations[["person_id", "activity_index", "destination_id", "geometry"]]

    # Validation
    initial_count = len(df_locations)
    df_locations = pd.concat([df_home_locations, df_work_locations, df_education_locations, df_secondary_locations])

    df_locations = df_locations.sort_values(by = ["person_id", "activity_index"])
    final_count = len(df_locations)

    assert initial_count == final_count

    df_locations = gpd.GeoDataFrame(df_locations, crs = dict(init = "epsg:2154"))

    return df_locations
    
    return df_locations
