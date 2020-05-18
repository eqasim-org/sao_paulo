from tqdm import tqdm
import pandas as pd
import numpy as np
import simpledbf
import itertools
import shapely.geometry as geo
import geopandas as gpd

def configure(context, require):
    require.stage("data.spatial.zones")
    require.stage("data.hts.cleaned")



def execute(context):
    
    df_zones = context.stage("data.spatial.zones")[0]
    df_persons = context.stage("data.hts.cleaned")[0]
    df_trips = context.stage("data.hts.cleaned")[1].copy()
    zone_ids = set(np.unique(df_zones["zone_id"]))
    
    # origin GEOID
    df_trips["geometry"] = [geo.Point(*xy) for xy in zip(df_trips["origin_x"], df_trips["origin_y"])]
    df_geo = gpd.GeoDataFrame(df_trips, crs = {"init" : "epsg:29183"})
    # only take necessary rows into account to speed up process
    merged_zones = gpd.sjoin(df_geo[["person_id","trip_id","geometry"]], df_zones[["zone_id","geometry"]], op = "within",how="left")
    # we ensure with the sjoin how="left" parameter, that GEOID is in the correct order
    df_trips["ori_geoloc"] = merged_zones["zone_id"]

    # destination GEOID
    df_trips["geometry"] = [geo.Point(*xy) for xy in zip(df_trips["destination_x"], df_trips["destination_y"])]
    df_geo = gpd.GeoDataFrame(df_trips, crs = {"init" : "epsg:29183"})
    merged_zones = gpd.sjoin(df_geo[["person_id","trip_id","geometry"]], df_zones[["zone_id","geometry"]], op = "within",how="left")
    # we ensure with the sjoin how="left" parameter, that GEOID is in the correct order
    df_trips["dest_geoloc"] = merged_zones["zone_id"]
   
    df_trips_persons = pd.merge(df_trips,df_persons,on=["person_id"],how='left')
    df_trips_persons = df_trips_persons[ (df_trips_persons["purpose"]=='work')]
    #drop duplicate persons
    df_trips_persons.drop_duplicates(subset=["person_id"])
    
    df_trips_persons = df_trips_persons.groupby(["home_zone", "dest_geoloc"]).sum()["weight"].reset_index()
    df_work = df_trips_persons
    df_work.columns = ["origin_id", "destination_id", "weight"]
    
    df_trips_persons = pd.merge(df_trips,df_persons,on=["person_id"],how='left')
    df_trips_persons = df_trips_persons[ (df_trips_persons["purpose"]=='education')]
    #drop duplicate persons
    df_trips_persons.drop_duplicates(subset=["person_id"])
    
    df_trips_persons = df_trips_persons.groupby(["home_zone", "dest_geoloc"]).sum()["weight"].reset_index()
    df_education = df_trips_persons
    df_education.columns = ["origin_id", "destination_id", "weight"]
    
    
    
    # Compute totals
    df_work_totals = df_work[["origin_id", "weight"]].groupby("origin_id").sum().reset_index()
    df_work_totals["total"] = df_work_totals["weight"]
    del df_work_totals["weight"]

    df_education_totals = df_education[["origin_id", "weight"]].groupby("origin_id").sum().reset_index()
    df_education_totals["total"] = df_education_totals["weight"]
    del df_education_totals["weight"]
   

    # Impute totals
    #df_work = pd.merge(df_work, df_work_totals, on = ["origin_id", "commute_mode"])
    df_work = pd.merge(df_work, df_work_totals, on = "origin_id")
    df_education = pd.merge(df_education, df_education_totals, on = "origin_id")

    # Compute probabilities
    df_work["weight"] /= df_work["total"]
    df_education["weight"] /= df_education["total"]

    assert(sum(df_work_totals["total"] == 0.0) == 0)
    assert(sum(df_education_totals["total"] == 0.0) == 0)

    # Cleanup
    df_work = df_work[["origin_id", "destination_id", "weight"]]
    df_education = df_education[["origin_id", "destination_id", "weight"]]

    # Fix missing zones
    existing_work_ids = set(np.unique(df_work["origin_id"]))
    missing_work_ids = zone_ids - existing_work_ids
    existing_education_ids = set(np.unique(df_education["origin_id"]))
    missing_education_ids = zone_ids - existing_education_ids
    
    # TODO: Here we could take the zones of nearby zones in the future. Right now
    # we just distribute evenly (after all these zones don't seem to have a big impact
    # if there is nobody in the data set).

    work_rows = []
    for origin_id in missing_work_ids:
        #for destination_id in existing_work_ids:
            work_rows.append((origin_id, origin_id, 1.0 / len(existing_work_ids)))
    df_work = pd.concat([df_work, pd.DataFrame.from_records(work_rows, columns = ["origin_id", "destination_id", "weight"])])

    education_rows = []
    for origin_id in missing_education_ids:
        #for destination_id in existing_education_ids:
        education_rows.append((origin_id, origin_id, 1.0 / len(existing_education_ids)))
    df_education = pd.concat([df_education, pd.DataFrame.from_records(education_rows, columns = ["origin_id", "destination_id", "weight"])])

   
    df_total = df_work[["origin_id", "weight"]].groupby("origin_id").sum().rename({"weight" : "total"}, axis = 1)
    df_work = pd.merge(df_work, df_total, on = "origin_id")
    df_work["weight"] /= df_work["total"]
    del df_work["total"]

    df_total = df_education[["origin_id", "weight"]].groupby("origin_id").sum().rename({"weight" : "total"}, axis = 1)
    df_education = pd.merge(df_education, df_total, on = "origin_id")
    df_education["weight"] /= df_education["total"]
    del df_education["total"]
    
    df_work = df_work.astype({'origin_id': 'int64'})
    df_work = df_work.astype({'destination_id': 'int64'})
    df_education = df_education.astype({'origin_id': 'int64'})
    df_education = df_education.astype({'destination_id': 'int64'})    
    return df_work, df_education
