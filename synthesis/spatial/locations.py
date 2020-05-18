import gzip
from tqdm import tqdm
import numpy as np
import io
import matsim.writers
import pandas as pd

def configure(context, require):
    require.stage("population.activities")
    require.stage("population.spatial.by_person.primary_locations")

def execute(context):
    df_activities = context.stage("population.activities")
    df_home, df_work, df_education = context.stage("population.spatial.by_person.primary_locations")

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
    df_home = context.stage("population.spatial.by_person.primary_locations")[0]

    df_home["home_x"] = df_home["x"]
    df_home["home_y"] = df_home["y"]
    df_home = df_home[["person_id", "home_x", "home_y"]]

    df_locations = pd.merge(df_locations, df_home, on = "person_id")

    f = df_locations["location_id"].isna()
    df_locations.loc[f, "x"] = df_locations.loc[f, "home_x"]
    df_locations.loc[f, "y"] = df_locations.loc[f, "home_y"]

    df_locations = df_locations[["person_id", "activity_id", "x", "y", "location_id"]]
    
    return df_locations
