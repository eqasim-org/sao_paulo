import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import shapely.geometry as geo
from collections import Counter

def configure(context):
    context.config("output_path")
    context.config("data_path")
    context.config("analysis_path")


def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{:.2f}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


def build_activity_chain(larr, arr):
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


def process_actual_activity_chain_counts(adf, adf_annot):
    adf.rename(columns = {"following_purpose": "destination_purpose", "preceeding_purpose": "origin_purpose"}, inplace = True)
    adf.loc[adf["destination_purpose"].isna(), "destination_purpose"] = "other"

    # Creating last trip dataframe to exclude activity chains not ending at home
    lmax = adf.groupby(["person_id"])["trip_id"].apply(list).to_dict()
    index = [adf["trip_id"][i] == max(lmax[adf["person_id"][i]] )  for i in range(len(adf)) ]
    adf_bis_il = adf.index[np.logical_and(index, adf["destination_purpose"]!= "Home")]
    adf_bis_i = adf.index.isin(adf_bis_il)
    adf_bis = adf[~adf_bis_i]

    # Fixing purposes and transport modes, excluding not modelled modes (bike and other)
    adf.loc[adf["destination_purpose"] == "errand", "destination_purpose"] ="other"
    adf.loc[adf["origin_purpose"] == "errand", "origin_purpose"] ="other"
    adf.loc[adf["mode"] == "motorcycle", "mode"] = "car"
    adf.loc[adf["mode"] == "taxi", "mode"] = "taxi"
    adf.loc[adf["mode"] == "ride_hailing", "mode"] = "taxi"
    adf = adf[~(adf["mode"] == "bike")]
    adf = adf[~(adf["mode"] == "other")]

    # Merging with person information, correcting trips with erroneous purpose
    adf_annot.rename(columns = {"weight":"weight_person", "sex":"gender", "employment":"employed", "binary_car_availability":"number_of_cars"}, inplace = True)
    adf = adf.merge(adf_annot[["person_id", "weight_person", "employed", "age", "household_income", "gender", "number_of_cars"]],on=["person_id"],how='left')
    adf.loc[(adf["destination_purpose"]=='work') & (adf["age"] < 16), "destination_purpose"]="other"
    adf.loc[(adf["origin_purpose"]=='work') & (adf["age"] < 16), "origin_purpose"]="other"

    # Only keep the persons that could have been used in activity chain matching
    adf = adf[~adf["weight_person"].isna()]
    amdf = adf.set_index(["person_id"])
    amdf.sort_index(inplace=True)

    amdf["origin_purpose_first"] = amdf["origin_purpose"].apply(lambda x: x[0])
    amdf["destination_purpose_first"] = amdf["destination_purpose"].apply(lambda x: x[0])

    df2 = amdf[["origin_purpose_first", "destination_purpose_first", "weight_person"]].groupby("person_id")[
    ["origin_purpose_first", "destination_purpose_first"]
].apply(lambda x: "-".join(x["origin_purpose_first"]) + "-" + x["destination_purpose_first"].iloc[-1]).reset_index(name = "chain")

    df3 = pd.merge(amdf["weight_person"].reset_index(), df2).drop_duplicates("person_id")

    alarr = np.split(amdf["destination_purpose"].values,np.cumsum(amdf["destination_purpose"].groupby(["person_id"]).size()))
    aarr = np.split(amdf["origin_purpose"].values,np.cumsum(amdf["origin_purpose"].groupby(["person_id"]).size()))

    astr_chain = build_activity_chain(alarr, aarr)

    adata_tuples = list(zip(Counter(astr_chain).keys(),Counter(astr_chain).values()))

    aCC = pd.DataFrame(adata_tuples, columns=['Chain','actual Count'])
    aCC = aCC.sort_values(by=['actual Count'],ascending=False)

    aCC_df3 = df3[["weight_person", "chain"]].groupby("chain").sum().reset_index().sort_values(
    by = "weight_person", ascending = False
).rename(columns = { "chain": "Chain", "weight_person": "actual Count" })

    dfm = pd.merge(aCC, aCC_df3, on = "Chain", suffixes = ["_old", "_new"])

    aCC = aCC_df3

    return aCC, amdf

def plot_comparison_bar(context, imtitle, plottitle, ylabel, xlabel, lab, actual, synthetic, lablist = ['HTS', 'Synthetic'], t = 15, figsize = [12,7], dpi = 300, w = 0.35, xticksrot = False):

    plt.rcParams['axes.facecolor'] = "#ffffff"
    plt.rcParams['figure.figsize'] = figsize
    plt.rcParams['figure.dpi'] = dpi

    top = t
    if not t is None:
        labels = lab[:top]
        actual_means = actual[:top]
        synthetic_means = synthetic[:top]
    else:
       labels = lab
       actual_means = actual
       synthetic_means = synthetic

    x = np.arange(len(labels))  # the label locations
    width = w  # the width of the bars

    fig, ax = plt.subplots()
    fig.set_facecolor("#ffffff")

    rects1 = ax.bar(x - width/2, actual_means, width, label = lablist[0], color="#00205B")
    rects2 = ax.bar(x + width/2, synthetic_means, width, label = lablist[1], color="#D3D3D3")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel(ylabel)
    ax.set_title(plottitle)
    ax.set_xlabel(xlabel)
    ax.set_xticks(x)

    if xticksrot:
        ax.set_xticklabels(labels, rotation = 45, ha = "right")
    else:
        ax.set_xticklabels(labels)

    ax.legend()
    plt.xticks(rotation=45)
    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") + imtitle)


def add_small_hist(axes, r, c, act, x, y, bins, lab = ["Synthetic", "HTS"]):
    axes[r,c].hist(x, bins, alpha=0.5, label=lab[0], density=True)
    axes[r,c].hist(y["crowfly_distance"], bins, weights=y["weight_person"], alpha=0.5, label=lab[1], density=True)
    axes[r,c].set_ylabel("Percentage")
    axes[r,c].set_xlabel("Crowfly Distance [km]")
    axes[r,c].set_title("Activity: " + act.capitalize())
    axes[r,c].legend(loc="best")
    return axes


def plot_comparison_hist_purpose(context, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
    modelist = synthetic_df["following_purpose"].unique()
    plt.rcParams['figure.dpi'] = dpi
    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    idx=0
    for r in range(rows):
        for c in range(cols):
            x = synthetic_df[synthetic_df["following_purpose"]==modelist[idx]]["crowfly_distance"]
            y = actual_df[actual_df["destination_purpose"]==modelist[idx]][["crowfly_distance", "weight_person"]]
            axes = add_small_hist(axes, r, c, modelist[idx], x, y, bins)
            idx = idx + 1   
     
    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") + "distancepurposehist.png")


def plot_comparison_hist_mode(context, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
    modelist = synthetic_df["mode"].unique()
    plt.rcParams['figure.dpi'] = dpi
    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    idx=0
    for r in range(rows):
        for c in range(cols):
            x = synthetic_df[synthetic_df["mode"]==modelist[idx]]["crowfly_distance"]
            y = actual_df[actual_df["mode"]==modelist[idx]][["crowfly_distance", "weight_person"]]        
            axes = add_small_hist(axes, r, c, modelist[idx], x, y, bins)
            idx=idx+1
            if idx==5:
                break

    fig.delaxes(axes[1,2])        
    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") +"distancemodehist.png")


def add_small_cdf(axes, r, c, act, x, y, bins, lab = ["Synthetic", "HTS"]):
    axes[r,c].hist(x, bins, alpha=0.5, label=lab[0], density=True, cumulative = True, histtype='step')
    axes[r,c].hist(y["crowfly_distance"], bins, weights=y["weight_person"], alpha=0.5, label=lab[1], density=True, cumulative = True, histtype='step')
    axes[r,c].set_ylabel("Percentage")
    axes[r,c].set_xlabel("Crowfly Distance [km]")
    axes[r,c].set_title("Activity: " + act.capitalize())
    axes[r,c].legend(loc="best")
    return axes

def plot_comparison_cdf_purpose(context, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
    modelist = synthetic_df["following_purpose"].unique()
    plt.rcParams['figure.dpi'] = dpi
    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    idx=0
    for r in range(rows):
        for c in range(cols):
            x = synthetic_df[synthetic_df["following_purpose"]==modelist[idx]]["crowfly_distance"]
            y = actual_df[actual_df["destination_purpose"]==modelist[idx]][["crowfly_distance", "weight_person"]]
            axes = add_small_cdf(axes, r, c, modelist[idx], x, y, bins)
            idx = idx + 1   
     
    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") +"distancepurposecdf.png")


def plot_comparison_cdf_mode(context, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
    modelist = synthetic_df["mode"].unique()
    plt.rcParams['figure.dpi'] = dpi
    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    idx=0
    for r in range(rows):
        for c in range(cols):
            x = synthetic_df[synthetic_df["mode"]==modelist[idx]]["crowfly_distance"]
            y = actual_df[actual_df["mode"]==modelist[idx]][["crowfly_distance", "weight_person"]]        
            axes = add_small_cdf(axes, r, c, modelist[idx], x, y, bins)
            idx=idx+1
            if idx==5:
                break

    fig.delaxes(axes[1,2])        
    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") +"distancemodecdf.png")


def plot_mode_share(context, df_syn, amdf2, dpi = 300):
    modelist=list(zip(np.sort(df_syn["mode"].unique()),["car","car_passenger","pt", "taxi", "walk"]))
    plt.rcParams['figure.dpi'] = dpi
    y1 = []
    y2 = []
    for mode,mode_cat in modelist:
        y1.append(df2[df2["mode"]==mode]["crowfly_distance"].count() / len(df))
        # use person weight for weigthing instead
        y2.append(amdf2[amdf2["mode"]==mode_cat]["weight_person"].sum() / amdf["weight_person"].sum())
    
    labels = [i[0] for i in modelist]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, y2, width, label='HTS',color="#00205B")
    rects2 = ax.bar(x + width/2, y1, width, label='Synthetic',color="#D3D3D3")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Percentage')
    ax.set_title('Mode-share')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") +"modeshare.png")
    plt.show()

def impute_geo(df, origin):
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
    df_syn = impute_geo(df_syn, origin = True)
    df_syn = impute_geo(df_syn, origin = False)
    df_syn.drop(columns=["geometry"],inplace=True)

    # in actual data
    amdf['person_id'] = amdf.index
    amdf = impute_geo(amdf, origin = True)
    amdf = impute_geo(amdf, origin = False)

    return df_syn, amdf


def execute(context):
    # Import data, merging

    # Synthetic data
    df_trips = gpd.read_file("%s/trips.gpkg" % context.config("output_path"))
    df_persons = pd.read_csv("%s/persons.csv" % context.config("output_path"), sep = ";")

    # Actual data
    df_act_trips = pd.read_csv("%s/HTS/tripsHTS.csv" % context.config("data_path"), sep=",")
    df_act_persons = pd.read_csv("%s/HTS/personsHTS.csv" % context.config("data_path"), sep=",")
    
    # Getting IDs
    trips_id = df_trips["person_id"].values.tolist()
    pers_id = df_persons["person_id"].values.tolist()

    # Merging trips with persons
    df_syn = df_trips.merge(df_persons, left_on="person_id", right_on="person_id")

    # Creating the new dataframes with activity chain counts
    CC = process_synthetic_activity_chain_counts(df_syn)
    act_CC, amdf = process_actual_activity_chain_counts(df_act_trips, df_act_persons)

    # Merging together
    all_CC = CC.merge(act_CC, on = "Chain", how = "left")

    # Get percentages, prepare for plotting
    all_CC["synthetic Count"] = all_CC ["synthetic Count"] / all_CC["synthetic Count"].sum() *100
    all_CC["actual Count"] = all_CC["actual Count"] / all_CC["actual Count"].sum() *100
    all_CC = all_CC.sort_values(by=['actual Count'], ascending=False)

    # First step done: plot activity chain counts
    plot_comparison_bar(context, imtitle = "activitychains.png", plottitle = "Synthetic and HTS activity chain comparison", ylabel = "Percentage", xlabel = "Activity chain", lab = all_CC["Chain"], actual = all_CC["actual Count"], synthetic = all_CC["synthetic Count"])

    # Second step: group by mode and destination purpose

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
    plot_comparison_bar(context, imtitle = "modepurpose.png", plottitle = "Synthetic and HTS Mode-Purpose Distribution", ylabel = "Percentage", xlabel = "", lab = labels, actual = act.values.tolist(), synthetic = syn.values.tolist(), t = 10, xticksrot = True )

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
    plot_comparison_bar(context, imtitle = "distancepurpose.png", plottitle = "Crowfly distance", ylabel = "Mean crowfly distance [km]", xlabel = "", lab = syn.index, actual = act, synthetic = syn, t = None, xticksrot = True )

    plot_comparison_hist_purpose(context, amdf2, df2, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2)
    plot_comparison_hist_mode(context, amdf2, df2, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2)

    plot_comparison_cdf_purpose(context, amdf2, df2, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2)
    plot_comparison_cdf_mode(context, amdf2, df2, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2)
    

    # Zipping modes in correct order
    #modes = zip(np.sort(df_syn["mode"].unique()),["car","car_passenger","pt", "taxi", "walk"])


    # Fourth step: mode share
    #plot_mode_share(df_syn, amdf2, dpi = 300)

    ## TODO: overall percentage of mode share by share
    
    #df_syn, amdf = add_geo_location_to_origin_and_destination(df_syn, amdf)
   






    
    












