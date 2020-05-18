import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np
import shapely.geometry as geo
import multiprocessing as mp
import geopandas as gpd

def configure(context, require):
    require.stage("population.spatial.by_person.primary_locations")
    require.stage("population.sociodemographics")

def execute(context):
    df = context.stage("population.sociodemographics")[["person_id"]]
    df_home, df_work, df_education = context.stage("population.spatial.by_person.primary_locations")

    df_home["home_x"] = df_home["x"]
    df_home["home_y"] = df_home["y"]
    df_work["work_x"] = df_work["x"]
    df_work["work_y"] = df_work["y"]

    df = pd.merge(
        df, df_home[["person_id", "home_x", "home_y"]], on = "person_id"
    )

    df = pd.merge(
        df, df_work[["person_id", "work_x", "work_y"]], on = "person_id"
    )

    df = gpd.GeoDataFrame(df)

    lines = []
    for home_x, home_y, work_x, work_y in tqdm(df[["home_x", "home_y", "work_x", "work_y"]].values):
        home_point = geo.Point(home_x, home_y)
        work_point = geo.Point(work_x, work_y)
        line = geo.LineString([home_point, work_point])
        lines.append(line)

    df["geometry"] = lines
    df.crs = {"init" : "EPSG:29183"}

    df[["person_id", "home_x", "home_y", "work_x", "work_y"]].to_csv("%s/home_work.csv" % context.cache_path, index = None)
    df.to_file("%s/commute.shp" % context.cache_path)
