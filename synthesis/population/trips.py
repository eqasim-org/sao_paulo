import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np
#import data.constants as c

def configure(context):
    context.stage("synthesis.population.sociodemographics")
    context.stage("data.hts.cleaned")

def execute(context):
    df_persons = context.stage("synthesis.population.sociodemographics")[[
        "person_id", "hts_person_id", "age", "sex", "residence_area_index"
    ]]

    df_trips = pd.DataFrame(context.stage("data.hts.cleaned")[1], copy = True)

    df_trips = df_trips[[
        "person_id", "trip_id", "departure_time", "arrival_time", "mode", "preceeding_purpose", "following_purpose"
    ]]
    df_trips.to_csv("%s/HTS/trips.csv" %  context.config("data_path"))
    assert(len(df_trips) == len(df_trips.dropna()))

    df_trips = df_trips.sort_values(by = ["person_id", "trip_id"])
    
    df_trip_counts = df_trips[["person_id"]].groupby("person_id").size().reset_index(name = "count")
    df_trips["trip_id"] = np.hstack([np.arange(n) for n in df_trip_counts["count"].values])

    df_trips.columns = ["hts_person_id", "trip_id", "departure_time", "arrival_time", "mode", "preceeding_purpose", "following_purpose"]

    # Merge trips to persons
    df_trips = pd.merge(df_persons, df_trips)

    df_trips.loc[df_trips["arrival_time"] < df_trips["departure_time"], "arrival_time"] += 24.0 * 3600.0
    df_trips.loc[:, "travel_time"] = df_trips.loc[:, "arrival_time"] - df_trips.loc[:, "departure_time"]

    df_trips = df_trips[[
        "person_id", "trip_id", "departure_time", "arrival_time", "travel_time", "mode", "preceeding_purpose", "following_purpose", "age", "hts_person_id", "residence_area_index", "sex"
    ]]

    df_trips = df_trips.sort_values(by = ["person_id", "trip_id"])

    # Diversify departure times
    counts = df_trips[["person_id", "trip_id"]].groupby("person_id").size().reset_index(name = "count")["count"].values

    interval = df_trips[["person_id", "departure_time"]].groupby("person_id").min().reset_index()["departure_time"].values
    interval = np.minimum(1800.0, interval) # If first departure time is just 5min after midnight, we only add a deviation of 5min

    offset = np.random.random(size = (len(counts), )) * interval * 2.0 - interval
    offset = np.repeat(offset, counts)

    df_trips["departure_time"] += offset
    df_trips["arrival_time"] += offset
    df_trips["departure_time"] = np.round(df_trips["departure_time"])
    df_trips["arrival_time"] = np.round(df_trips["arrival_time"])
    
    return df_trips


