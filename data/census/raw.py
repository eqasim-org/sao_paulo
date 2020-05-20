from tqdm import tqdm
import pandas as pd
import numpy as np
import geopandas as gpd
import pyreadstat

def configure(context):
    context.config("data_path")    

def execute(context):

    columns = ['V0001', 'V0011', 'V0221', 'V0222', 'V0601', 'V6036', 'V0401', 'V1004', 'V0010', 'V0641', 'V0642', 'V0643', 'V0644', 'V0628', 'V6529', 'V0504']

    reader = pyreadstat.read_file_in_chunks(pyreadstat.read_sav, "%s/Census/Censo.2010.brasil.amostra.10porcento.sav" % context.config("data_path"), chunksize= 500000, usecols=columns)

    df, meta = pyreadstat.read_sav("%s/Census/Censo.2010.brasil.amostra.10porcento.sav" % context.config("data_path"), row_offset=1, row_limit=1,usecols=columns)

    df_census = pd.DataFrame(columns = df.columns)
    
    i = 500000

    for df, meta in reader:
        print(df.groupby(["V0001"]).count())
    	#keep only those in Sao Paulo state
        df1 = df[df["V0001"] == '35']
        df_census = pd.concat([df_census, df1])
        print("Processed " + repr(i) + " samples.")
        i = i + 500000

    df_census.columns = ["federationCode", "areaCode", "householdWeight", "metropolitanRegion", "personNumber", "gender", "age", "goingToSchool", "employment", "onLeave", "helpsInWork", "farmWork",
	"householdIncome", "motorcycleAvailability", "carAvailability", "numberOfMembers"]
    df_census['employment'] = df_census['employment'].fillna(2.0) #these are only children
    df_census['carAvailability'] = df_census['carAvailability'].fillna(2.0) #assume households do not have access to a car if not reported
    df_census['motorcycleAvailability'] = df_census['motorcycleAvailability'].fillna(2.0) #assume households do not have access to a motorcycle if not reported   
    total_weight = df_census["householdWeight"].sum()
    df_census = df_census.dropna(subset=['householdIncome', 'age', 'gender', 'carAvailability', 'motorcycleAvailability' ])
    new_weight = df_census["householdWeight"].sum()
    df_census["householdWeight"] = df_census["householdWeight"] * (total_weight / new_weight)
    df_census.loc[((df_census["goingToSchool"] == 1) | (df_census["goingToSchool"] == 2)) & ~(df_census["employment"] == 1), "employment"] = 3
    # Put person IDs
    df_census.loc[:, "person_id"] = df_census.index
    df_census.loc[:, "weight"] = df_census["householdWeight"]

    # Spatial
    df_census["zone_id"] = df_census["areaCode"]
    return df_census
