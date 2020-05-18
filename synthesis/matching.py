import pandas as pd
import numpy as np
import population.algo.hot_deck_matching

def configure(context, require):
    require.stage("population.upscaled")
    require.stage("data.hts.cleaned")

MINIMUM_SOURCE_SAMPLES = 20

def execute(context):
    df_hts = context.stage("data.hts.cleaned")[0]
    number_of_threads = context.config["hdm_threads"]

    # Source: HTS
    df_source = df_hts

    # Target: Census
    df_census = context.stage("population.upscaled").sort_values(by = "person_id")
    number_of_census_persons = len(np.unique(df_census["person_id"]))

    df_target = df_census

    # Match households
    #age_selector = df_census["age"] >= c.HTS_MINIMUM_AGE
    #df_target = pd.DataFrame(df_census[age_selector], copy = True)

    # Common attributes:
    # age, sex, couple, married, employed, nationality, studies
    # household_size, number_of_vehicles, household_type, household_income_class

    AGE_BOUNDARIES = [6, 10, 14, 18, 24, 30, 42, 54, 66, 78, np.inf]
    df_target["age_class"] = np.digitize(df_target["age"], AGE_BOUNDARIES, right = True)
    df_source["age_class"] = np.digitize(df_source["age"], AGE_BOUNDARIES, right = True)

    INCOME_BOUNDARIES = [ 2000.0, 2900.0, 4150.0, 6580.0, np.inf]
    df_target["income_class"] = np.digitize(df_target["hhlIncome"], INCOME_BOUNDARIES, right = True)
    df_source["income_class"] = np.digitize(df_source["household_income"], INCOME_BOUNDARIES, right = True)

    #HOUSEHOLD_SIZE_BOUNDARIES = [1, 2, 3, 4, np.inf]
    #df_target["household_size_class"] = np.digitize(df_target["household_size"], HOUSEHOLD_SIZE_BOUNDARIES, right = True)
    #df_source["household_size_class"] = np.digitize(df_source["household_size"], HOUSEHOLD_SIZE_BOUNDARIES, right = True)

    #NUMBER_OF_VEHICLES_BOUNDARIES = [1, 2, np.inf]
    #df_target["number_of_vehicles_class"] = np.digitize(df_target["number_of_vehicles"], NUMBER_OF_VEHICLES_BOUNDARIES, right = True)
    #df_source["number_of_vehicles_class"] = np.digitize(df_source["number_of_vehicles"], NUMBER_OF_VEHICLES_BOUNDARIES, right = True)

#    df_target["income_class_simple"] = 0
#    df_target.loc[df_target["household_income_class"] >= 2, "income_class_simple"] = 1
#    df_target.loc[df_target["household_income_class"] >= 3, "income_class_simple"] = 2
#    df_target.loc[df_target["household_income_class"] >= 4, "income_class_simple"] = 3
#    df_target.loc[df_target["household_income_class"] >= 6, "income_class_simple"] = 4

#    simple_income_classes = SIMPLE_ENTD_INCOME_CLASSES if context.config["hts"] == "entd" else SIMPLE_EGT_INCOME_CLASSES
#    df_source["income_class_simple"] = 0
#    df_source.loc[df_source["household_income_class"] >= simple_income_classes[0], "income_class_simple"] = 1
#    df_source.loc[df_source["household_income_class"] >= simple_income_classes[1], "income_class_simple"] = 2
#    df_source.loc[df_source["household_income_class"] >= simple_income_classes[2], "income_class_simple"] = 3
#    df_source.loc[df_source["household_income_class"] >= simple_income_classes[3], "income_class_simple"] = 4

    # age_class, sex, household_income_class, household_size_class,
    # number_of_vehicles_class, studies, employed, couple, zone_au

#    df_target["any_cars"] = df_target["number_of_vehicles"] > 0
#    df_source["any_cars"] = df_source["number_of_vehicles"] > 0

    #df_target["car_availability_class"] = df_target["binary_car_availability"]
    #df_source["car_availability_class"] = df_source["has_car_trip"]

    population.algo.hot_deck_matching.run(
        df_target, "person_id",
        df_source, "person_id",
        "weight",
        ["age_class", "sex", "binary_car_availability","employment"], #, "married"], MARRIED only available for ENTD, not EGT ?
        ["area_id"],#, "income_class"], #["household_size_class", "zone_au_simple", "income_class_simple", "number_of_vehicles_class"],
        runners = number_of_threads,
        minimum_source_samples = 5
    )

    # Remove and track unmatchable persons

    initial_census_length = len(df_census)
    initial_target_length = len(df_target)

    unmatchable_person_selector = df_target["hdm_source_id"] == -1
    umatchable_person_ids = set(df_target.loc[unmatchable_person_selector, "person_id"].values)
    unmatchable_member_selector = df_census["person_id"].isin(umatchable_person_ids)

    removed_person_ids = set(df_census.loc[unmatchable_member_selector, "person_id"].values)

    #print(df_target[
    #    unmatchable_person_selector
    #][["person_id", "age", "age_class", "sex", "married"]])

    #print(df_target[unmatchable_person_selector])

    df_target = df_target.loc[~unmatchable_person_selector, :]
    df_census = df_census.loc[~unmatchable_member_selector, :]

    removed_persons_count = sum(unmatchable_person_selector)
    removed_members_count = sum(unmatchable_member_selector)

    assert(len(df_target) == initial_target_length - removed_persons_count)
    assert(len(df_census) == initial_census_length - removed_members_count)

    # Extract only the matching information

    df_matching = pd.merge(
        df_census[[ "person_id" ]],
        df_target[[ "person_id", "hdm_source_id" ]],
        on = "person_id", how = "left")

    df_matching["hts_person_id"] = df_matching["hdm_source_id"]
    del df_matching["hdm_source_id"]

    assert(len(df_matching) == len(df_census))

    # Check that all person who don't have a MZ id now are under age
    #assert(np.all(df_census[
    #    df_census["person_id"].isin(
    #        df_matching.loc[df_matching["hts_person_id"] == -1]["person_id"]
    #    )
    #]["age"] < c.HTS_MINIMUM_AGE))

    print("Matching is done. In total, the following observations were removed from the census because they cannot be matched: ")
    #print("  Households: %d (%.2f%%)" % ( len(removed_household_ids), 100.0 * len(removed_household_ids) / number_of_census_households ))
    print("  Persons: %d (%.2f%%)" % ( len(removed_person_ids), 100.0 * len(removed_person_ids) / number_of_census_persons ))
    # Return
    return df_matching, removed_person_ids
