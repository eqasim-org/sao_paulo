import pandas as pd
import numpy as np
import geopandas as gpd
import shapely.geometry as geo
from collections import Counter
import analysis.myplottools

def build_activity_chain(larr, arr, actual = False):
    # getting last activity
    lact = []
    for chain in larr:
        try:
            lact.append(chain[-1][0])
        except:
            # if the very last one is empty for some reason
            lact.append("")

    # make a string describing the activity chain
    str_chain = []
    for chain in arr:
        str_chain.append('-'.join([word[0] for word in chain]))

    # append the return activity to the str_chain
    str_chain = [i + "-" + j for i, j in zip(str_chain, lact) ]

    return str_chain


def process_synthetic_activity_chain_counts(df_syn):
    # Multiindexing
    mdf_syn = df_syn.set_index(["person_id","trip_id"])
    mdf_syn.sort_index(inplace=True)

    # Split followingPurpose into subarrays grouped by person_id
    larr = np.split(mdf_syn["following_purpose"].values, np.cumsum(mdf_syn["following_purpose"].groupby(['person_id']).size()))

    # Split preceedingPurpose into subarrays grouped by person_id
    arr = np.split(mdf_syn["preceeding_purpose"].values, np.cumsum(mdf_syn["preceeding_purpose"].groupby(['person_id']).size()))
 
    # Create activity chains
    str_chain = build_activity_chain(larr, arr)

    # Create new data frame
    data_tuples = list(zip(Counter(str_chain).keys(),Counter(str_chain).values()))
    CC = pd.DataFrame(data_tuples, columns=['Chain','synthetic Count'])
    CC = CC.sort_values(by=['synthetic Count'],ascending=False)
    return CC


def process_actual_activity_chain_counts(df_act, df3):
    # Split followingPurpose into subarrays grouped by person_id
    alarr = np.split(df_act["destination_purpose"].values,np.cumsum(df_act["destination_purpose"].groupby(["person_id"]).size()))
    
    # Split preceedingPurpose into subarrays grouped by person_id
    aarr = np.split(df_act["origin_purpose"].values,np.cumsum(df_act["origin_purpose"].groupby(["person_id"]).size()))

    # Create activity chains
    astr_chain = build_activity_chain(alarr, aarr)

    # Create new data frame
    adata_tuples = list(zip(Counter(astr_chain).keys(),Counter(astr_chain).values()))

    aCC = pd.DataFrame(adata_tuples, columns=['Chain','actual Count'])
    aCC = aCC.sort_values(by=['actual Count'],ascending=False)

    aCC_df3 = df3[["weight_person", "chain"]].groupby("chain").sum().reset_index().sort_values(
    by = "weight_person", ascending = False
).rename(columns = { "chain": "Chain", "weight_person": "actual Count" })

    aCC = aCC_df3

    return aCC


def impute_geo(df, df_zones, origin):
    if origin:
        colx = "origin_x"
        coly = "origin_y"
        target = "ori_geoloc"
    else:
        colx = "destination_x"
        coly = "destination_y"
        target = "dest_geoloc"

    df["geometry"] = [geo.Point(*xy) for xy in zip(df[colx], df[coly])]
    df_geo = gpd.GeoDataFrame(df, crs = {"init" : "epsg:29183"})
    df_geo = df_geo.to_crs({"init" : "epsg:4326"})
    # only take necessary rows into account to speed up process
    pt_zones = gpd.sjoin(df_geo[["person_id","person_trip_id","geometry"]], df_zones[["c_1_633_","geometry"]], op = "within",how="left")
    # we ensure with the sjoin how="left" parameter, that GEOID is in the correct order
    df[target] = pt_zones["c_1_633_"]

    return df


def add_geo_location_to_origin_and_destination(df_syn, amdf):
    # load shapefile and convert to correct projection
    df_zones = gpd.read_file("spatial_df.shp")
    df_zones = df_zones.to_crs({"init" : "epsg:4326"})

    # in synthetic data
    df_syn = impute_geo(df_syn, df_zones, origin = True)
    df_syn = impute_geo(df_syn, df_zones, origin = False)
    df_syn.drop(columns=["geometry"],inplace=True)

    # in actual data
    amdf['person_id'] = amdf.index
    amdf = impute_geo(amdf, origin = True)
    amdf = impute_geo(amdf, origin = False)

    return df_syn, amdf


def pipeline_menwomen(df_syn, df_act_trips, df_act_persons, gender, context):
    # Comparing men and women activity chains
    CC = process_synthetic_activity_chain_counts(df_syn)

    act_CC, amdf = process_actual_activity_chain_counts(df_act_trips, df_act_persons)

    # Merging together
    all_CC = CC.merge(act_CC, on = "Chain", how = "left")

    # Get percentages, prepare for plotting
    all_CC["synthetic Count"] = all_CC ["synthetic Count"] / all_CC["synthetic Count"].sum() *100
    all_CC["actual Count"] = all_CC["actual Count"] / all_CC["actual Count"].sum() *100
    all_CC = all_CC.sort_values(by=['actual Count'], ascending=False)

    # First step done: plot activity chain counts
    myplottools.plot_comparison_bar(context, imtitle = "activitychains_"+gender+".png", 
                                    plottitle = "Synthetic and HTS activity chain comparison - " + gender,
                                    ylabel = "Percentage", xlabel = "Activity chain", 
                                    lab = all_CC["Chain"], actual = all_CC["actual Count"],
                                    synthetic = all_CC["synthetic Count"])

    # first in the synthetic data
    types = df_syn.groupby(["mode","following_purpose"]).count()["person_id"]
    syn = types / types.sum()

    # then in the actual data
    amdf.loc[amdf["mode"]=='car_passanger', "mode"] = 'car_passenger'
    which = ["car","car_passenger","pt", "taxi","walk"]
    atypes = amdf.groupby(["mode","destination_purpose"]).sum().loc[which,"weight_person"].reindex(index=which, level=0)
    act = atypes / atypes.sum()
    
    lista = [item for item in list(types.index.levels[0]) for i in range(len(types.index.levels[1]))]
    listb = list(types.index.levels[1]) * len(types.index.levels[0])
    labels = [a + " " + b for a, b in zip(lista,listb)]

    # already ready to plot!
    myplottools.plot_comparison_bar(context, imtitle = "modepurpose_"+gender+".png", 
                                    plottitle = "Synthetic and HTS Mode-Purpose Distribution - " + gender,
                                    ylabel = "Percentage", xlabel = "", 
                                    lab = labels, actual = act.values.tolist(), 
                                    synthetic = syn.values.tolist(), t = 10, xticksrot = True )

    # Third step: look into the crowfly distances

    # Compute the distances
    amdf["crowfly_distance"] = 0.001 * np.sqrt(
        (amdf["origin_x"] - amdf["destination_x"])**2 + (amdf["origin_y"] - amdf["destination_y"])**2
    )
    df_syn["crowfly_distance"] = df_syn.geometry.length
    df_syn["crowfly_distance"] = df_syn["crowfly_distance"] *0.001

    # Only consider crowfly distances shorter than 25 km
    df2 = df_syn[df_syn["crowfly_distance"] < 25]
    amdf2 = amdf[amdf["crowfly_distance"] < 25]

    # Finish to prepare for plotting
    amdf2["x"] = amdf2["weight_person"] * amdf2["crowfly_distance"]

    act = amdf2.groupby(["destination_purpose"]).sum()["x"] / amdf2.groupby(["destination_purpose"]).sum()["weight_person"]
    syn = df2.groupby(["following_purpose"]).mean()["crowfly_distance"] 

    # Ready to plot!
    myplottools.plot_comparison_bar(context, imtitle = "distancepurpose_"+gender+".png", 
                                    plottitle = "Crowfly distance - "+gender, 
                                    ylabel = "Mean crowfly distance [km]", xlabel = "",
                                    lab = syn.index, actual = act, synthetic = syn, 
                                    t = None, xticksrot = True )

    myplottools.plot_comparison_hist_purpose(context, "distance_purpose_hist_"+gender+".png",
                                             amdf2, df2, bins = np.linspace(0,25,120), 
                                             dpi = 300, cols = 3, rows = 2)
    myplottools.plot_comparison_hist_mode(context,"distance_mode_hist_"+gender+".png", 
                                          amdf2, df2, bins = np.linspace(0,25,120), 
                                          dpi = 300, cols = 3, rows = 2)

    myplottools.plot_comparison_cdf_purpose(context,"distance_purpose_cdf_"+gender+".png", 
                                            amdf2, df2, bins = np.linspace(0,25,120),
                                            dpi = 300, cols = 3, rows = 2)
    myplottools.plot_comparison_cdf_mode(context,"distance_mode_cdf_"+gender+".png", 
                                         amdf2, df2, bins = np.linspace(0,25,120),
                                         dpi = 300, cols = 3, rows = 2)












