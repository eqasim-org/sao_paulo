import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np
#import data.constants as c
import shapely.geometry as geo
import multiprocessing as mp
import time

def configure(context):
    context.stage("data.od.cleaned")
    context.stage("synthesis.population.sociodemographics")
    context.stage("synthesis.population.trips")

def execute(context):
    df_persons = pd.DataFrame(context.stage("synthesis.population.sociodemographics")[["person_id", "zone_id", "census_person_id", "has_work_trip", "has_education_trip", "age", "household_id"]], copy = True)
    df_persons = df_persons

    df_trips = context.stage("synthesis.population.trips")[["person_id", "following_purpose"]]
    df_work_od, df_education_od = context.stage("data.od.cleaned")

    df_home = df_persons[["person_id", "zone_id", "household_id"]]

    # Second, work zones
    df_work = []

    for origin_id in tqdm(np.unique(df_persons["zone_id"]), desc = "Sampling work zones"):
        f = (df_persons["zone_id"] == origin_id) & df_persons["has_work_trip"]
        df_origin = pd.DataFrame(df_persons[f][["person_id", "age"]], copy = True)
        df_destination = df_work_od[df_work_od["origin_id"] == origin_id]

        if len(df_origin) > 0:
            counts = np.random.multinomial(len(df_origin), df_destination["weight"].values)
            indices = np.repeat(np.arange(len(df_destination)), counts)
            df_origin.loc[:, "zone_id"] = df_destination.iloc[indices]["destination_id"].values
            df_work.append(df_origin[["person_id", "zone_id", "age"]])

    df_work = pd.concat(df_work)


    # Third, education zones
    df_education = []

    for origin_id in tqdm(np.unique(df_persons["zone_id"]), desc = "Sampling education zones"):
        f = (df_persons["zone_id"] == origin_id) & df_persons["has_education_trip"]
        df_origin = pd.DataFrame(df_persons[f][["person_id", "age"]], copy = True)
        df_destination = df_education_od[df_education_od["origin_id"] == origin_id]

        if len(df_origin) > 0:
            counts = np.random.multinomial(len(df_origin), df_destination["weight"].values)
            indices = np.repeat(np.arange(len(df_destination)), counts)
            df_origin.loc[:, "zone_id"] = df_destination.iloc[indices]["destination_id"].values
            df_education.append(df_origin[["person_id", "zone_id", "age"]])
           
    df_education = pd.concat(df_education)

    return df_home, df_work, df_education
