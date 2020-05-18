import pandas as pd
import numpy as np
#import data.constants as c

def configure(context, require):
    require.stage("population.matching")
    require.stage("population.upscaled")
    require.stage("data.hts.cleaned")
    #require.stage("population.income")

def execute(context):
    df_matching, unmatched_ids = context.stage("population.matching")
    df_persons = context.stage("population.upscaled")
    #df_income = context.stage("population.income")

    df_hts = pd.DataFrame(context.stage("data.hts.cleaned")[0], copy = True)
    df_hts["hts_person_id"] = df_hts["person_id"]
    del df_hts["person_id"]

    df_persons = df_persons[[
        "person_id", "household_id",
        "age", "sex", "employment", #"number_of_vehicles",
        "census_person_id", #, "household_size"
        "zone_id", "hhlIncome", "binary_car_availability"
    ]]

    df_hts = df_hts[[
        "hts_person_id", "has_pt_subscription", #"has_license",
        #"number_of_bikes",
        "is_passenger", "commute_mode", "commute_distance",
        "has_work_trip", "has_education_trip"
    ]]

    #df_income = df_income[[
    #    "household_id", "household_income"
    #]]

    assert(len(df_matching) == len(df_persons) - len(unmatched_ids))

    # Merge in attributes from HTS
    df_persons = pd.merge(df_persons, df_matching, on = "person_id", how = "inner")
    df_persons = pd.merge(df_persons, df_hts, on = "hts_person_id", how = "left")
    
    df_persons.loc[df_persons["age"] < 18, "has_pt_subscription"] = True
    df_persons.loc[df_persons["age"] >= 60, "has_pt_subscription"] = True

    #df_persons = pd.merge(df_persons, df_income, on = "household_id", how = "left")

    # Reset children
    #children_selector = df_persons["age"] < c.HTS_MINIMUM_AGE
    #df_persons.loc[children_selector, "has_license"] = False
    #df_persons.loc[children_selector, "has_pt_subscription"] = False

    # Add car availability
    #df_cars = df_persons[["household_id", "number_of_vehicles"]].drop_duplicates("household_id")
    #df_licenses = df_persons[["household_id", "has_license"]].groupby("household_id").sum().reset_index()
    #df_licenses.columns = ["household_id", "licenses"]

    #df_car_availability = pd.merge(df_cars, df_licenses)

    #df_car_availability.loc[:, "car_availability"] = "all"
    #df_car_availability.loc[df_car_availability["number_of_vehicles"] < df_car_availability["licenses"], "car_availability"] = "some"
    #df_car_availability.loc[df_car_availability["number_of_vehicles"] == 0, "car_availability"] = "none"

    #df_car_availability["car_availability"] = df_car_availability["car_availability"].astype("category")
    #df_persons = pd.merge(df_persons, df_car_availability[["household_id", "car_availability"]])

    # Add bike availability
    #df_persons.loc[:, "bike_availability"] = "all"
    #df_persons.loc[df_persons["number_of_bikes"] < df_persons["household_size"], "bike_availability"] = "some"
    #df_persons.loc[df_persons["number_of_bikes"] == 0, "bike_availability"] = "none"
    #df_persons["bike_availability"] = df_persons["bike_availability"].astype("category")

    return df_persons
