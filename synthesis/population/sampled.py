import pandas as pd
import numpy as np

def configure(context):
    context.stage("data.census.cleaned")

def execute(context):
    df_census = context.stage("data.census.cleaned").sort_values(by = "household_id")
    df_census["numberOfMembers"] = df_census["numberOfMembers"].astype(np.int)
    # Find rounded multiplicators for the households
    df_weighting = df_census[[
        "household_id", "weight", "numberOfMembers"
    ]].groupby("household_id").first().reset_index()
    df_weighting["multiplicator"] = np.round(df_weighting["weight"]).astype(np.int)
    df_weighting = df_weighting[["household_id", "multiplicator", "numberOfMembers"]]

    household_multiplicators = df_weighting["multiplicator"].values
    household_sizes = df_weighting["numberOfMembers"].values

    person_muliplicators = np.repeat(household_multiplicators, household_sizes)
    df_census = df_census.iloc[np.repeat(np.arange(len(df_census)), person_muliplicators)]

    # Create new houeshold and person IDs
    df_census.loc[:, "census_person_id"] = df_census["person_id"]
    df_census.loc[:, "census_household_id"] = df_census["household_id"]
    df_census.loc[:, "person_id"] = np.arange(len(df_census))

    multiplied_household_sizes = np.repeat(household_sizes, household_multiplicators)
    multiplied_household_count = int(np.sum(household_multiplicators))
    df_census.loc[:, "household_id"] = np.repeat(np.arange(multiplied_household_count), multiplied_household_sizes)

    if "input_downsampling" in context.config:
        probability = context.config["input_downsampling"]
        print("Downsampling (%f)" % probability)

        household_ids = np.unique(df_census["household_id"])
        print("  Initial number of households:", len(household_ids))

        f = np.random.random(size = (len(household_ids),)) < probability
        remaining_household_ids = household_ids[f]
        print("  Sampled number of households:", len(remaining_household_ids))

        df_census = df_census[df_census["household_id"].isin(remaining_household_ids)]

    return df_census

