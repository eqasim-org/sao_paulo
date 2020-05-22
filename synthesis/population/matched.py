import pandas as pd
import numpy as np
import synthesis.population.algo.hot_deck_matching

def configure(context):
    context.stage("synthesis.population.sampled")
    context.stage("data.hts.cleaned")
    context.config("processes")

MINIMUM_SOURCE_SAMPLES = 20

def execute(context):
    df_hts = context.stage("data.hts.cleaned")[0]
    number_of_threads = context.config("processes")

    # Source: HTS
    df_source = df_hts

    # Target: Census
    df_census = context.stage("synthesis.population.sampled").sort_values(by = "person_id")
    number_of_census_persons = len(np.unique(df_census["person_id"]))

    df_target = df_census

    AGE_BOUNDARIES = [6, 10, 14, 18, 24, 30, 42, 54, 66, 78, np.inf]
    df_target["age_class"] = np.digitize(df_target["age"], AGE_BOUNDARIES, right = True)
    df_source["age_class"] = np.digitize(df_source["age"], AGE_BOUNDARIES, right = True)

    INCOME_BOUNDARIES = [ 2000.0, 2900.0, 4150.0, 6580.0, np.inf]
    df_target["income_class"] = np.digitize(df_target["household_income"], INCOME_BOUNDARIES, right = True)
    df_source["income_class"] = np.digitize(df_source["household_income"], INCOME_BOUNDARIES, right = True)

    synthesis.population.algo.hot_deck_matching.run(
        df_target, "person_id",
        df_source, "person_id",
        "weight",
        ["age_class", "sex", "binary_car_availability","employment"],
        ["residence_area_index"],
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

    print("Matching is done. In total, the following observations were removed from the census because they cannot be matched: ")
    print("  Persons: %d (%.2f%%)" % ( len(removed_person_ids), 100.0 * len(removed_person_ids) / number_of_census_persons ))
    
    # Return
    return df_matching, removed_person_ids
