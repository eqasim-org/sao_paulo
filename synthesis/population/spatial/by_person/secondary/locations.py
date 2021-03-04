import numpy as np
import pandas as pd
import multiprocessing as mp
import shapely.geometry as geo
import geopandas as gpd
import time
from synthesis.population.spatial.by_person.secondary.problems import find_assignment_problems

def configure(context):
    context.stage("synthesis.population.trips")
    context.stage("synthesis.population.sociodemographics")
    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.spatial.by_person.primary_locations")

    context.stage("synthesis.population.spatial.by_person.secondary.distance_distributions")
    context.stage("synthesis.destinations")

    context.config("random_seed")
    context.config("processes")

def prepare_locations(context):
    # Load persons and their primary locations
    df_home, df_work, df_education = context.stage("synthesis.population.spatial.by_person.primary_locations")

    df_home["home"] = [geo.Point(px,py) for px, py in list(zip(df_home["x"].values.tolist(), df_home["y"].values.tolist()))]

    df_work["work"] = [geo.Point(px,py) for px, py in list(zip(df_work["x"].values.tolist(), df_work["y"].values.tolist()))]

    df_education["education"] = [geo.Point(px,py) for px, py in list(zip(df_education["x"].values.tolist(), df_education["y"].values.tolist()))]

    df_persons = context.stage("synthesis.population.sampled")[["person_id", "household_id"]]
    df_locations = pd.merge(df_home, df_persons, how = "left", on = ["person_id", "household_id"])
    df_locations = pd.merge(df_locations, df_work[["person_id", "work"]], how = "left", on = "person_id")
    df_locations = pd.merge(df_locations, df_education[["person_id", "education"]], how = "left", on = "person_id")

    return df_locations[["person_id", "home", "work", "education"]].sort_values(by = "person_id")

def prepare_destinations(context):
    df_destinations = context.stage("synthesis.destinations")
    df_destinations.rename(columns = {"location_id": "destination_id"}, inplace = True)

    identifiers = df_destinations["destination_id"].values
    locations = np.vstack(df_destinations["geometry"].apply(lambda x: np.array([x.x, x.y])).values)

    data = {}

    for purpose in ("shop", "leisure", "other"):
        f = df_destinations["offers_%s" % purpose].values

        data[purpose] = dict(
            identifiers = identifiers[f],
            locations = locations[f]
        )

    return data

def resample_cdf(cdf, factor):
    if factor >= 0.0:
        cdf = cdf * (1.0 + factor * np.arange(1, len(cdf) + 1) / len(cdf))
    else:
        cdf = cdf * (1.0 + abs(factor) - abs(factor) * np.arange(1, len(cdf) + 1) / len(cdf))

    cdf /= cdf[-1]
    return cdf

def resample_distributions(distributions, factors):
    for mode, mode_distributions in distributions.items():
        for distribution in mode_distributions["distributions"]:
            distribution["cdf"] = resample_cdf(distribution["cdf"], factors[mode])

from synthesis.population.spatial.by_person.secondary.rda import AssignmentSolver, DiscretizationErrorObjective, GravityChainSolver
from synthesis.population.spatial.by_person.secondary.components import CustomDistanceSampler, CustomDiscretizationSolver

def execute(context):
    # Load trips and primary locations
    df_trips = context.stage("synthesis.population.trips").sort_values(by = ["person_id", "trip_id"])

    df_trips["travel_time"] = df_trips["arrival_time"] - df_trips["departure_time"]

    df_primary = prepare_locations(context)

    # Prepare data
    distance_distributions = context.stage("synthesis.population.spatial.by_person.secondary.distance_distributions")
    destinations = prepare_destinations(context)

    # Resampling for calibration
    resample_distributions(distance_distributions, dict(
        car = 0.0, car_passenger = 0.0, pt = 0.2, walk = -0.2, taxi = 0.0
    ))

    # Segment into subsamples
    processes = context.config("processes")

    unique_person_ids = df_trips["person_id"].unique()
    number_of_persons = len(unique_person_ids)
    unique_person_ids = np.array_split(unique_person_ids, processes)

    random = np.random.RandomState(context.config("random_seed"))
    random_seeds = random.randint(10000, size = processes)

    # Create batch problems for parallelization
    batches = []

    for index in range(processes):
        batches.append((
            df_trips[df_trips["person_id"].isin(unique_person_ids[index])],
            df_primary[df_primary["person_id"].isin(unique_person_ids[index])],
            random_seeds[index]
        ))

    # Run algorithm in parallel
    with context.progress(label = "Assigning secondary locations to persons", total = number_of_persons):
        with context.parallel(processes = processes, data = dict(
            distance_distributions = distance_distributions,
            destinations = destinations
        )) as parallel:
            df_locations, df_convergence = [], []

            for df_locations_item, df_convergence_item in parallel.imap_unordered(process, batches):
                df_locations.append(df_locations_item)
                df_convergence.append(df_convergence_item)

    df_locations = pd.concat(df_locations).sort_values(by = ["person_id", "trip_index"])
    df_convergence = pd.concat(df_convergence)

    print("Success rate:", df_convergence["valid"].mean())

    return df_locations, df_convergence

def process(context, arguments):
  df_trips, df_primary, random_seed = arguments
    

  # Set up RNG
  random = np.random.RandomState(context.config("random_seed"))

  # Set up distance sampler
  distance_distributions = context.data("distance_distributions")
  distance_sampler = CustomDistanceSampler(
        maximum_iterations = 1000,
        random = random,
        distributions = distance_distributions)

  # Set up relaxation solver; currently, we do not consider tail problems.
  relaxation_solver = GravityChainSolver(
    random = random, eps = 10.0, lateral_deviation = 10.0, alpha = 0.1
    )

  # Set up discretization solver
  destinations = context.data("destinations")
  discretization_solver = CustomDiscretizationSolver(destinations)

  # Set up assignment solver
  thresholds = dict(
    car = 200.0, car_passenger = 200.0, pt = 200.0,
    bike = 100.0, walk = 100.0, taxi = 200.0
  )

  assignment_objective = DiscretizationErrorObjective(thresholds = thresholds)
  assignment_solver = AssignmentSolver(
      distance_sampler = distance_sampler,
      relaxation_solver = relaxation_solver,
      discretization_solver = discretization_solver,
      objective = assignment_objective,
      maximum_iterations = 20
      )

  df_locations = []
  df_convergence = []

  last_person_id = None

  for problem in find_assignment_problems(df_trips, df_primary):    
      result = assignment_solver.solve(problem)

      starting_trip_index = problem["trip_index"]

      for index, (identifier, location) in enumerate(zip(result["discretization"]["identifiers"], result["discretization"]["locations"])):
          df_locations.append((
              problem["person_id"], starting_trip_index + index, identifier, geo.Point(location)
          ))

      df_convergence.append((
          result["valid"], problem["size"]
      ))

      if problem["person_id"] != last_person_id:
          last_person_id = problem["person_id"]
          context.progress.update()

  df_locations = pd.DataFrame.from_records(df_locations, columns = ["person_id", "trip_index", "destination_id", "geometry"])
  df_locations = gpd.GeoDataFrame(df_locations, crs = dict(init = "epsg:29183"))

  df_convergence = pd.DataFrame.from_records(df_convergence, columns = ["valid", "size"])
  return df_locations, df_convergence
