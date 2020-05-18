import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np

def configure(context, require):
    require.stage("population.sociodemographics")
    require.stage("population.trips")

def execute(context):
    df_trips = pd.DataFrame(context.stage("population.trips"), copy = True)
    df_trips.loc[:, "previous_trip_id"] = df_trips.loc[:, "trip_id"] - 1

    df_activities = pd.merge(
        df_trips, df_trips, left_on = ["person_id", "previous_trip_id"], right_on = ["person_id", "trip_id"],
        suffixes = ["_following_trip", "_previous_trip"], how = "left"
    )

    df_activities.loc[:, "start_time"] = df_activities.loc[:, "arrival_time_previous_trip"]
    df_activities.loc[:, "end_time"] = df_activities.loc[:, "departure_time_following_trip"]
    df_activities.loc[:, "purpose"] = df_activities.loc[:, "following_purpose_previous_trip"]
    df_activities.loc[:, "activity_id"] = df_activities.loc[:, "trip_id_following_trip"]
    df_activities.loc[:, "is_last"] = False

    # We assume that the plans start at home
    df_activities.loc[:, "purpose"] = df_activities.loc[:, "purpose"].fillna("home")

    # We're still missing the last activity in the chain.
    df_last = df_activities.sort_values(by = ["person_id", "activity_id"])
    df_last = df_last.drop_duplicates("person_id", keep = "last")
    df_last.loc[:, "purpose"] = df_last.loc[:, "following_purpose_following_trip"]
    df_last.loc[:, "start_time"] = df_last.loc[:, "arrival_time_following_trip"]
    df_last.loc[:, "end_time"] = np.nan
    df_last.loc[:, "activity_id"] += 1
    df_last.loc[:, "is_last"] = True

    df_activities = pd.concat([df_activities, df_last])
    df_activities = df_activities.sort_values(by = ["person_id", "activity_id"])

    # We're still missing activities for people who don't have a any trips
    df_persons = context.stage("population.sociodemographics")[["person_id"]]

    missing_ids = set(np.unique(df_persons["person_id"])) - set(np.unique(df_activities["person_id"]))
    print("Found %d persons without activities" % len(missing_ids))

    df_missing = pd.DataFrame.from_records([
        (person_id, 1, "home", True) for person_id in missing_ids
    ], columns = ["person_id", "activity_id", "purpose", "is_last"])

    # Impute household id in the missing ones
    #df_missing = pd.merge(df_missing, df_persons[["person_id"]])

    df_activities = pd.concat([df_activities, df_missing], sort = True)
    assert(len(np.unique(df_persons["person_id"])) == len(np.unique(df_activities["person_id"])))

    # Some cleanup
    df_activities = df_activities.sort_values(by = ["person_id", "activity_id"])
    df_activities.loc[:, "duration"] = df_activities.loc[:, "end_time"] - df_activities.loc[:, "start_time"]

    df_activities = df_activities[[
        "person_id", "activity_id", "start_time", "end_time", "duration", "purpose", "is_last"
    ]]

    return df_activities
