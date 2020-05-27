import geopandas as gpd
import pandas as pd
import shapely.geometry as geo
import os, datetime, json

def configure(context):
    context.stage("synthesis.population.sociodemographics")
    context.stage("synthesis.population.activities")
    context.stage("synthesis.population.trips")
    context.stage("synthesis.population.spatial.locations")

    for option in ("output_path", "sampling_rate", "random_seed"):
        context.config(option)

def validate(context):
    output_path = context.config("output_path")

    if not os.path.isdir(output_path):
        raise RuntimeError("Output directory must exist: %s" % output_path)

def execute(context):
    output_path = context.config("output_path")

    # Prepare households
    df_households = context.stage("synthesis.population.sociodemographics").rename(
        columns = { "hhlincome": "income" }
    ).drop_duplicates("household_id")

    df_households = df_households[[
        "household_id",
        "binary_car_availability",
        "household_income"
    ]]

    df_households.to_csv("%s/households.csv" % output_path, sep = ";", index = None)

    # Prepare persons
    df_persons = context.stage("synthesis.population.sociodemographics")#.rename(
        #columns = { "has_license": "has_driving_license" }
    #)

    df_persons = df_persons[[
        "person_id", "household_id",
        "age", "employment", "sex", "has_pt_subscription",
        "census_person_id", "hts_person_id"
    ]]

    df_persons.to_csv("%s/persons.csv" % output_path, sep = ";", index = None)

    # Prepare activities
    df_activities = context.stage("synthesis.population.activities")#.rename(
        #columns = { "trip_index": "following_trip_index" }
    #)

    #df_activities["preceeding_trip_index"] = df_activities["following_trip_index"].shift(1)
    #df_activities.loc[df_activities["is_first"], "preceeding_trip_index"] = -1
    #df_activities["preceeding_trip_index"] = df_activities["preceeding_trip_index"].astype(int)

    df_activities = df_activities[[
        "person_id", "activity_id",
        #"preceeding_trip_index", "following_trip_index",
        "purpose", "start_time", "end_time",
        #"is_first", 
        "is_last"
    ]]

    df_activities.to_csv("%s/activities.csv" % output_path, sep = ";", index = None)

    # Prepare trips
    df_trips = context.stage("synthesis.population.trips")#.rename(
        #columns = {
        #    "is_first_trip": "is_first",
        #    "is_last_trip": "is_last"
        #}
    #)

    df_trips["preceeding_activity_index"] = df_trips["trip_id"]
    df_trips["following_activity_index"] = df_trips["trip_id"] + 1

    df_trips = df_trips[[
        "person_id", "trip_id",
        "preceeding_activity_index", "following_activity_index",
        "departure_time", "arrival_time", "mode",
        "preceeding_purpose", 
        "following_purpose",
        #"is_first", "is_last"
    ]]

    df_trips.to_csv("%s/trips.csv" % output_path, sep = ";", index = None)

    # Prepare spatial data sets
    df_locations = context.stage("synthesis.population.spatial.locations")[[
        "person_id", "activity_id", "geometry"
    ]]
    #df_locations["geometry"] = [geo.Point(px, py) for px, py in list(zip(df_locations["x"].values.tolist(), df_locations["y"].values.tolist()))]

    df_activities = pd.merge(df_activities, df_locations[[
        "person_id", "activity_id", "geometry"
    ]], how = "left", on = ["person_id", "activity_id"])

    # Write spatial activities
    df_spatial = gpd.GeoDataFrame(df_activities, crs = dict(init = "epsg:29183"))
    df_spatial["purpose"] = df_spatial["purpose"].astype(str)
    df_spatial.to_file("%s/activities.gpkg" % output_path, driver = "GPKG")

    # Write spatial trips
    df_spatial = pd.merge(df_trips, df_locations[[
        "person_id", "activity_id", "geometry"
    ]].rename(columns = {
        "activity_id": "preceeding_activity_index",
        "geometry": "preceeding_geometry"
    }), how = "left", on = ["person_id", "preceeding_activity_index"])

    df_spatial = pd.merge(df_spatial, df_locations[[
        "person_id", "activity_id", "geometry"
    ]].rename(columns = {
        "activity_id": "following_activity_index",
        "geometry": "following_geometry"
    }), how = "left", on = ["person_id", "following_activity_index"])

    df_spatial["geometry"] = [
        geo.LineString(od)
        for od in zip(df_spatial["preceeding_geometry"], df_spatial["following_geometry"])
    ]

    df_spatial = df_spatial.drop(columns = ["preceeding_geometry", "following_geometry"])

    print(df_spatial.columns)

    df_spatial = gpd.GeoDataFrame(df_spatial, crs = dict(init = "epsg:29183"))
    df_spatial["following_purpose"] = df_spatial["following_purpose"].astype(str)
    df_spatial["preceeding_purpose"] = df_spatial["preceeding_purpose"].astype(str)
    df_spatial["mode"] = df_spatial["mode"].astype(str)
    df_spatial.to_file("%s/trips.gpkg" % output_path, driver = "GPKG")

    # Write meta information
    information = dict(
        sampling_rate = context.config("sampling_rate"),
        random_seed = context.config("random_seed"),
        created = datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    with open("%s/meta.json" % output_path, "w+") as f:
        json.dump(information, f, indent = 4)
