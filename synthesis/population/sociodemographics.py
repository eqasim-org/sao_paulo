import pandas as pd
import numpy as np
#import data.constants as c

def configure(context):
    context.stage("synthesis.population.matched")
    context.stage("synthesis.population.sampled")
    context.stage("data.hts.cleaned")

def execute(context):
    df_matching, unmatched_ids = context.stage("synthesis.population.matched")
    df_persons = context.stage("synthesis.population.sampled")

    df_hts = pd.DataFrame(context.stage("data.hts.cleaned")[0], copy = True)
    df_hts["hts_person_id"] = df_hts["person_id"]
    del df_hts["person_id"]

    df_persons = df_persons[[
        "person_id", "household_id",
        "age", "sex", "employment", 
        "census_person_id",
        "zone_id", "household_income", "binary_car_availability"
    ]]

    df_hts = df_hts[[
        "hts_person_id", "has_pt_subscription",
        "is_passenger", "commute_mode_work", "commute_distance_work",
        "commute_mode_education", "commute_distance_education",
        "has_work_trip", "has_education_trip"
    ]]

    assert(len(df_matching) == len(df_persons) - len(unmatched_ids))

    # Merge in attributes from HTS
    df_persons = pd.merge(df_persons, df_matching, on = "person_id", how = "inner")
    df_persons = pd.merge(df_persons, df_hts, on = "hts_person_id", how = "left")
    
    df_persons.loc[df_persons["age"] < 18, "has_pt_subscription"] = True
    df_persons.loc[df_persons["age"] >= 60, "has_pt_subscription"] = True

    return df_persons
