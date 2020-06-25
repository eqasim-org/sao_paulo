import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np
#import data.constants as c
import shapely.geometry as geo
import multiprocessing as mp
from sklearn.neighbors import KDTree
import matplotlib.pyplot as plt
import geopandas as gpd
from scipy.spatial import cKDTree
from functools import partial
import time

#import data.spatial.pt_zone

def configure(context):
    context.stage("synthesis.population.spatial.by_person.primary_zones")
    context.stage("data.spatial.zones")
    context.stage("synthesis.destinations")
    context.stage("synthesis.population.sociodemographics")
    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.trips")
    context.stage("synthesis.destinations")
    context.config("processes")
    context.stage("data.hts.cleaned")

SAMPLE_SIZE = 1000

def initialize_parallel(_df_persons, _df_locations):
    global df_persons, df_locations
    df_persons = pd.DataFrame(_df_persons, copy = True)
    df_locations = pd.DataFrame(_df_locations, copy = True) if _df_locations is not None else None

def define_ordering(df_persons, commute_coordinates):
    if "home_x" in df_persons.columns:
        home_coordinates = df_persons[["home_x", "home_y"]].values
        commute_distances = df_persons["commute_distance_work"].values
        indices = heuristic_ordering(home_coordinates, commute_coordinates, commute_distances)
        assert((np.sort(np.unique(indices)) == np.arange(len(commute_distances))).all())
        return indices
    else:
        return np.arange(len(commute_coordinates)) # Random ordering

def heuristic_ordering(home_coordinates, commute_coordinates, commute_distances):
    indices = []
    commute_indices = np.arange(len(commute_coordinates))

    for home_coordinate, commute_distance in zip(home_coordinates, commute_distances):
        distances = np.sqrt(np.sum((commute_coordinates - home_coordinate)**2, axis = 1))
        costs = np.abs(distances - commute_distance)
        costs[indices] = np.inf
        indices.append(np.argmin(costs))

    return indices

def bipartite_ordering(home_coordinates, commute_coordinates, commute_distances):
    import munkres
    x = commute_coordinates[:,0][np.newaxis, :] - home_coordinates[:,0][:, np.newaxis]
    y = commute_coordinates[:,1][np.newaxis, :] - home_coordinates[:,1][:, np.newaxis]
    distances = np.sqrt(x**2 + y**2)
    costs = np.abs(distances - commute_distances[:, np.newaxis])
    return [index[1] for index in munkres.Munkres().compute(costs)]

def run_parallel(args):
    i, chunk = args
    person_dfs = []

    for zone_id, count, shape in tqdm(
        chunk, desc = "Sampling coordinates", position = i):

        if count > 0:
            points = []
            ids = []

            if df_locations is None:
                while len(points) < count:
                    minx, miny, maxx, maxy = shape.bounds
                    candidates = np.random.random(size = (SAMPLE_SIZE, 2))
                    candidates[:,0] = minx + candidates[:,0] * (maxx - minx)
                    candidates[:,1] = miny + candidates[:,1] * (maxy - miny)
                    candidates = [geo.Point(*point) for point in candidates]
                    candidates = [point for point in candidates if shape.contains(point)]
                    points += candidates
                    ids += [np.nan] * len(candidates)

                points, ids = points[:count], ids[:count]
                points = np.array([np.array([point.x, point.y]) for point in points])
                ids = np.array([np.nan] * len(points))
            else:
                if np.count_nonzero(df_locations["zone_id"] == zone_id) == 0:
                    raise RuntimeError("Requested destination for a zone without discrete destinations")

                df_zone_locations = df_locations[df_locations["zone_id"] == zone_id]
                selector = np.random.randint(len(df_zone_locations), size = count)

                points = df_zone_locations.iloc[selector][["x", "y"]].values
                ids = df_zone_locations.iloc[selector]["location_id"].values

            f = df_persons["zone_id"] == zone_id
            ordering = define_ordering(df_persons[f], points)
            points, ids = points[ordering], ids[ordering]
            df_persons.loc[f, "x"] = points[:,0]
            df_persons.loc[f, "y"] = points[:,1]
            df_persons.loc[f, "location_id"] = ids
            person_dfs.append(df_persons[f])

    print() # Clean tqdm progress
    return pd.concat(person_dfs) if len(person_dfs) > 0 else pd.DataFrame()


def impute_locations(df_persons, df_zones, df_locations, threads, identifier = "person_id"):
    df_counts = df_persons[["zone_id"]].groupby("zone_id").size().reset_index(name = "count")
    df_zones = pd.merge(df_zones, df_counts, on = "zone_id", how = "inner")

    with mp.Pool(processes = threads, initializer = initialize_parallel, initargs = (df_persons, df_locations)) as pool:
        chunks = np.array_split(df_zones[["zone_id", "count", "geometry"]].values, threads)
        df_locations = pd.concat(pool.map(run_parallel, enumerate(chunks)))
        df_locations = df_locations[[identifier, "x", "y", "zone_id", "location_id"]]
        return df_locations

def deg_to_rad(angle):
    return angle * np.pi / 180


def impute_education_locations_same_zone(df_ag, hts_trips, df_candidates, df_travel, age_min, age_max, name):
    hts_educ = hts_trips.copy()
    hts_educ_cp = hts_educ[hts_educ["mode"]=="car_passenger"]
    hts_educ_ncp = hts_educ[hts_educ["mode"]!="car_passenger"]

    dist_educ_cp = hts_educ_cp
    hist_cp, bins_cp = np.histogram(dist_educ_cp["commute_distance_education"], weights = dist_educ_cp["weight"], bins = 500)

    dist_educ_ncp = hts_educ_ncp
    hist_ncp, bins_ncp = np.histogram(dist_educ_ncp["commute_distance_education"], weights = dist_educ_ncp["weight"], bins = 500)

    df_trips = df_travel.copy()

    cp_ids = list(set(df_trips[df_trips["mode"]=="car_passenger"]["hts_person_id"].values))

    df_agents = df_ag.copy()
    df_agents_cp  = df_agents[np.isin(df_agents["hts_person_id"], cp_ids)]
    df_agents_ncp  = df_agents[np.logical_not(np.isin(df_agents["hts_person_id"], df_agents_cp["hts_person_id"]))]

    assert len(df_agents_cp) + len(df_agents_ncp) == len(df_agents)

    home_coordinates_cp = list(zip(df_agents_cp["home_x"], df_agents_cp["home_y"]))
    home_coordinates_ncp = list(zip(df_agents_ncp["home_x"], df_agents_ncp["home_y"]))
    education_coordinates = np.array(list(zip(df_candidates["x"], df_candidates["y"])))

    bin_midpoints = bins_cp[:-1] + np.diff(bins_cp)/2
    cdf = np.cumsum(hist_cp)
    cdf = cdf / cdf[-1]
    values = np.random.rand(len(df_agents_cp))
    value_bins = np.searchsorted(cdf, values)
    random_from_cdf_cp = bin_midpoints[value_bins] # in meters
    
    tree = KDTree(education_coordinates)
    indices_cp, distances_cp = tree.query_radius(home_coordinates_cp, r=random_from_cdf_cp, return_distance = True, sort_results=True)

    bin_midpoints = bins_ncp[:-1] + np.diff(bins_ncp)/2
    cdf = np.cumsum(hist_ncp)
    cdf = cdf / cdf[-1]
    values = np.random.rand(len(df_agents_ncp))
    value_bins = np.searchsorted(cdf, values)
    random_from_cdf_ncp = bin_midpoints[value_bins] # in meters
    
    indices_ncp, distances_ncp = tree.query_radius(home_coordinates_ncp, r=random_from_cdf_ncp, return_distance = True, sort_results=True)

    # In some cases no education facility was found within the given radius. In this case select the nearest facility.
    for i in range(len(indices_cp)):
        l = indices_cp[i] 
        if len(l) == 0:
            dist, ind = tree.query(np.array(home_coordinates_cp[i]).reshape(1,-1), 2, return_distance = True, sort_results=True)
            fac = ind[0][1]
            indices_cp[i] = [fac]
            distances_cp[i] = [dist[0][1]]

    indices_cp = [l[-1] for l in indices_cp]
    distances_cp = [d[-1] for d in distances_cp]

    for i in range(len(indices_ncp)):
        l = indices_ncp[i] 
        if len(l) == 0:
            dist, ind = tree.query(np.array(home_coordinates_ncp[i]).reshape(1,-1), 2, return_distance = True, sort_results=True)
            fac = ind[0][1]
            indices_ncp[i] = [fac]
            distances_ncp[i] = [dist[0][1]]

    indices_ncp = [l[-1] for l in indices_ncp]
    distances_ncp = [d[-1] for d in distances_ncp]

    df_return_cp = df_agents_cp
    df_return_cp["x"] = df_candidates.iloc[indices_cp]["x"].values
    df_return_cp["y"] = df_candidates.iloc[indices_cp]["y"].values
    df_return_cp["location_id"]  = df_candidates.iloc[indices_cp]["location_id"].values

    df_return_ncp = df_agents_ncp
    df_return_ncp["x"] = df_candidates.iloc[indices_ncp]["x"].values
    df_return_ncp["y"] = df_candidates.iloc[indices_ncp]["y"].values
    df_return_ncp["location_id"]  = df_candidates.iloc[indices_ncp]["location_id"].values

    df_return = pd.concat([df_return_cp, df_return_ncp])
    assert len(df_return) == len(df_agents)
    return df_return
    
def impute_education_locations_same_zone_new(df_ag, hts_trips, df_candidates, df_travel, age_min, age_max, name):
    hts_educ = hts_trips.copy()
    hts_educ_cp = hts_educ[hts_educ["mode"]=="car_passenger"]
    hts_educ_ncp = hts_educ[hts_educ["mode"]!="car_passenger"]

    dist_educ_cp = hts_educ
    hist_cp, bins_cp = np.histogram(dist_educ_cp["commute_distance_education"], weights = dist_educ_cp["weight"], bins = 500)
    
    df_trips = df_travel.copy()

    cp_ids = list(set(df_trips["hts_person_id"].values))

    df_agents = df_ag.copy()
    df_agents_cp  = df_agents[np.isin(df_agents["hts_person_id"], cp_ids)]

    assert len(df_agents_cp) == len(df_agents)

    home_coordinates_cp = list(zip(df_agents_cp["home_x"], df_agents_cp["home_y"]))
    education_coordinates = np.array(list(zip(df_candidates["x"], df_candidates["y"])))

    bin_midpoints = bins_cp[:-1] + np.diff(bins_cp)/2
    cdf = np.cumsum(hist_cp)
    cdf = cdf / cdf[-1]
    values = np.random.rand(len(df_agents_cp))
    value_bins = np.searchsorted(cdf, values)
    random_from_cdf_cp = bin_midpoints[value_bins] # in meters
    
    tree = KDTree(education_coordinates)
    indices_cp, distances_cp = tree.query_radius(home_coordinates_cp, r=random_from_cdf_cp, return_distance = True, sort_results=True)

    # In some cases no education facility was found within the given radius. In this case select the nearest facility.
    for i in range(len(indices_cp)):
        l = indices_cp[i] 
        if len(l) == 0:
            dist, ind = tree.query(np.array(home_coordinates_cp[i]).reshape(1,-1), 2, return_distance = True, sort_results=True)
            fac = ind[0][1]
            indices_cp[i] = [fac]
            distances_cp[i] = [dist[0][1]]

    indices_cp = [l[-1] for l in indices_cp]
    distances_cp = [d[-1] for d in distances_cp]

    df_return_cp = df_agents_cp
    df_return_cp["x"] = df_candidates.iloc[indices_cp]["x"].values
    df_return_cp["y"] = df_candidates.iloc[indices_cp]["y"].values
    df_return_cp["location_id"]  = df_candidates.iloc[indices_cp]["location_id"].values

    df_return = df_return_cp
    assert len(df_return) == len(df_agents)
    return df_return    

def parallelize_dataframe(hts_trips, df_ag, df_candidates, df_travel, age_min, age_max, name, func, n_cores=24):
    df_split = np.array_split(df_ag, n_cores)
    print("parallelize")
    pool = mp.Pool(n_cores)
    prod_x = partial(func, hts_trips = hts_trips, df_candidates = df_candidates, df_travel = df_travel, age_min = age_min, age_max = age_max, name=name)
    df_locations = pd.concat(pool.map(prod_x, df_split))
    pool.close()
    pool.join()
    return df_locations
    

def impute_work_locations_same_zone(hts_trips, df_ag, df_candidates, df_travel, name):
    hts_work = hts_trips.copy()

    hist_cp, bins_cp = np.histogram(hts_work["crowfly_distance"], weights = hts_work["weight"], bins = 500)

    df_trips = df_travel.copy()

    df_agents = df_ag.copy()
    df_agents_cp  = df_agents#[np.isin(df_agents["hts_person_id"], cp_ids)]

    home_coordinates_cp = list(zip(df_agents_cp["home_x"], df_agents_cp["home_y"]))
    work_coordinates = np.array(list(zip(df_candidates["x"], df_candidates["y"])))

    bin_midpoints = bins_cp[:-1] + np.diff(bins_cp)/2
    cdf = np.cumsum(hist_cp)
    cdf = cdf / cdf[-1]
    values = np.random.rand(len(df_agents_cp))
    value_bins = np.searchsorted(cdf, values)
    random_from_cdf_cp = bin_midpoints[value_bins] # in meters
    
    tree = KDTree(work_coordinates)
    indices_cp, distances_cp = tree.query_radius(home_coordinates_cp, r=random_from_cdf_cp, return_distance = True, sort_results=True)

    
    # In some cases no work facility was found within the given radius. In this case select the nearest facility.
    for i in range(len(indices_cp)):
        l = indices_cp[i] 
        if len(l) == 0:
            dist, ind = tree.query(np.array(home_coordinates_cp[i]).reshape(1,-1), 2, return_distance = True, sort_results=True)
            fac = ind[0][1]
            indices_cp[i] = [fac]
            distances_cp[i] = [dist[0][1]]

    indices_cp = [l[-1] for l in indices_cp]
    distances_cp = [d[-1] for d in distances_cp]    

    df_return_cp = df_agents_cp.copy()
    df_return_cp["x"] = df_candidates.iloc[indices_cp]["x"].values
    df_return_cp["y"] = df_candidates.iloc[indices_cp]["y"].values
    df_return_cp["location_id"]  = df_candidates.iloc[indices_cp]["location_id"].values
    
    df_return = df_return_cp
    assert len(df_return) == len(df_agents)
    return df_return


def execute(context):
    threads = context.config("processes")
    df_zones = context.stage("data.spatial.zones")[["zone_id", "geometry"]]
    df_commune_zones = context.stage("data.spatial.zones")
    df_zones["zone_id"] = df_zones["zone_id"].astype(np.int)
    
    df_opportunities = context.stage("synthesis.destinations")
    df_opportunities["zone_id"] = df_opportunities["zone_id"].astype(np.int)
    
    df_commute = context.stage("synthesis.population.sociodemographics")[["person_id", "commute_distance_work", "commute_distance_education", "hts_person_id"]]
    
    print("Imputing home locations ...")
    df_households = context.stage("synthesis.population.spatial.by_person.primary_zones")[0].copy()
    df_hhl = context.stage("synthesis.population.sampled").drop_duplicates("household_id")[[
        "household_id", "zone_id"
    ]].copy()

    df_hhl.rename(columns={"household_id":"person_id"}, inplace = True)
    df_home_opportunities = df_opportunities[df_opportunities["offers_home"]]

    df_home = impute_locations(df_hhl, df_zones, df_home_opportunities, threads, "person_id")[["person_id", "x", "y", "location_id"]]
    df_home.rename(columns = {"person_id":"household_id"}, inplace = True)
    df_hhl = context.stage("synthesis.population.sampled")
    df_home = pd.merge(df_hhl, df_home, on = ["household_id"], how = "left")

    df_home = pd.merge(df_home, df_households[["person_id", "household_id"]], on = ["person_id", "household_id"], how = 'left')

    print("Imputing work locations ...")
    df_households =  context.stage("synthesis.population.spatial.by_person.primary_zones")[0].copy()
    df_work_zones =  context.stage("synthesis.population.spatial.by_person.primary_zones")[1].copy()
    df_hw =  pd.merge(df_work_zones.rename(columns = {"zone_id":"work_id"}) , df_households.rename(columns = {"zone_id":"home_id"}), on=["person_id"], how='left')
    
    df_work_zones = pd.merge(df_hw, df_commute)
    df_work_zones = pd.merge(df_work_zones, df_home.rename({"x" : "home_x", "y" : "home_y"}, axis = 1))
    df_work_different_zone = df_work_zones.copy()

    df_work_different_zone = df_work_different_zone[df_work_different_zone["work_id"]!=df_work_different_zone["home_id"]]
    del(df_work_different_zone["zone_id"])
    df_work_different_zone.rename(columns={"work_id" : "zone_id"},inplace=True)

    df_work_locations = df_opportunities[df_opportunities["offers_work"]]

    df_work = impute_locations(df_work_different_zone, df_zones, df_work_locations, 24)[["person_id", "x", "y", "location_id"]]
    
    print("Imputing same zone work locations ...")
    df_work_same_zone = df_work_zones.copy()
    df_work_same_zone = df_work_same_zone[df_work_same_zone["work_id"]==df_work_same_zone["home_id"]]
    f_persons = (df_work_same_zone["work_id"] == df_work_same_zone["home_id"])
        
    df_candidates = df_work_locations
    work_coordinates = list(zip(df_candidates["x"], df_candidates["y"]))
    home_coordinates = list(zip(df_work_same_zone.loc[f_persons, "home_x"], df_work_same_zone.loc[f_persons, "home_y"]))    
    
    df_hts_trips = context.stage("data.hts.cleaned")[1]
    df_hts_persons = context.stage("data.hts.cleaned")[0]
    df_hts = pd.merge(df_hts_trips, df_hts_persons, on=["person_id"])
    hts_trips_work = df_hts[df_hts["following_purpose"] == "work"]
    hts_trips_work = hts_trips_work[hts_trips_work["origin_zone"] == hts_trips_work["destination_zone"]]
    df_agents = df_work_same_zone.copy()
    df_trips = context.stage("synthesis.population.trips")

    work_locations = impute_work_locations_same_zone(hts_trips_work, df_agents, df_candidates, df_trips, "/home/asallard/Scenarios/work.png")
    df_work_same_zone = work_locations[["person_id", "x", "y", "location_id"]]    

    df_work = df_work.append(df_work_same_zone, sort = False)        

    print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    print("Imputing education locations ...")
    df_persons = context.stage("synthesis.population.spatial.by_person.primary_zones")[2]
    df_persons.rename(columns = {"zone_id":"education_id"}, inplace = True) 

    df_persons = pd.merge(df_persons, df_commute)
    df_persons = pd.merge(df_persons, df_home.rename({"x" : "home_x", "y" : "home_y"}, axis = 1), on = ["person_id"])
    df_persons["age"] = df_persons["age_x"]
    df_persons["residence_area_index"] = df_persons["residence_area_index_x"]
    
    df_persons_same_zone = pd.merge(df_persons, df_households, on=["person_id", "household_id"], how='left')
    df_persons_same_zone = df_persons_same_zone.drop(columns = ["age_x", "age_y", "residence_area_index_x", "residence_area_index_y"])

    df_education_locations = context.stage("synthesis.destinations")
    df_candidates = df_education_locations[df_education_locations["offers_education"]]
        
    df_hts_trips = context.stage("data.hts.cleaned")[1]
    df_hts_persons = context.stage("data.hts.cleaned")[0]
    df_hts = pd.merge(df_hts_trips, df_hts_persons, on=["person_id"])
    hts_trips_educ = df_hts[df_hts["following_purpose"]=="education"]

    df_agents = df_persons_same_zone.copy()
    df_trips = context.stage("synthesis.population.trips")

    categories = {"age":[[0, 14], [15, 18], [19, 24], [25, 1000]], "gender":["male", "female"], "residence_area_index":[1,2,3]}
    dflist_educ = []
    for a_cat in categories["age"]:
        for sex_cat in categories["gender"]:
            for res_cat in categories["residence_area_index"]:
                a_min = a_cat[0]
                a_max = a_cat[1]

                df_travel = df_trips.copy()
                df_travel = df_travel[np.logical_and(df_travel["age"] >= a_min, df_travel["age"] <= a_max)]
                df_travel = df_travel[df_travel["sex"] == sex_cat]
                df_travel = df_travel[df_travel["residence_area_index"] == res_cat]

                df_ag = df_agents.copy()
                df_ag = df_ag[np.logical_and(df_ag["age"] >= a_min, df_ag["age"] <= a_max)]
                df_ag = df_ag[df_ag["sex"] == sex_cat]
                df_ag = df_ag[df_ag["residence_area_index"] == res_cat] 

                hts_trips = hts_trips_educ[np.logical_and(hts_trips_educ["age"] >= a_min, hts_trips_educ["age"] <= a_max)]
                hts_trips = hts_trips[hts_trips["sex"] == sex_cat]
                hts_trips = hts_trips[hts_trips["residence_area_index"] == res_cat]

                educ_current = parallelize_dataframe(hts_trips, df_ag, df_candidates, df_travel, a_min,  a_max, "/home/asallard/Scenarios/educ014.png", impute_education_locations_same_zone_new, 3)
                dflist_educ.append(educ_current)

    education_locations = pd.concat(dflist_educ)
    df_persons_same_zone = education_locations[["person_id", "x", "y", "location_id"]]

    df_education = df_persons_same_zone    
    
    return df_home, df_work, df_education
