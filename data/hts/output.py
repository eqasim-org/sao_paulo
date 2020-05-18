from tqdm import tqdm
import pandas as pd
import numpy as np

def configure(context, require):
    require.stage("data.hts.cleaned")

def execute(context):
    df_persons, df_trips = context.stage("data.hts.cleaned")

    df_persons.to_csv("%s/sp_persons.csv" % context.cache_path)
    df_trips.to_csv("%s/sp_trips.csv" % context.cache_path)
