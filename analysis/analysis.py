import pandas as pd
import numpy as np
import geopandas as gpd
import analysis.myutils as myutils
import analysis.myplottools as myplottools
import matplotlib.pyplot as plt

def configure(context):
    context.config("output_path")
    context.config("data_path")
    context.config("analysis_path")
    
    
def import_data_synthetic(context):
    # Synthetic data
    df_trips = gpd.read_file("%s/trips.gpkg" % context.config("output_path"))
    df_persons = pd.read_csv("%s/persons.csv" % context.config("output_path"), sep = ";")
    
    # Merging trips with persons - synthetic
    df_syn = df_trips.merge(df_persons, left_on="person_id", right_on="person_id")
    t_id = df_syn["person_id"].values.tolist()
    df_persons_no_trip = df_persons[np.logical_not(df_persons["person_id"].isin(t_id))]
    df_persons_no_trip = df_persons_no_trip.set_index(["person_id"])

    return df_syn, df_persons_no_trip


def import_data_actual(context):
    # Actual data
    df_act_trips = pd.read_csv("%s/HTS/tripsHTS.csv" % context.config("data_path"), sep=",")
    df_act_persons = pd.read_csv("%s/HTS/personsHTS.csv" % context.config("data_path"), sep=",")
  
    # Processing actual data
    df_act_trips.rename(columns = {"following_purpose": "destination_purpose", "preceeding_purpose": "origin_purpose"}, inplace = True)
    df_act_trips.loc[df_act_trips["destination_purpose"].isna(), "destination_purpose"] = "other"

    # Creating last trip dataframe to exclude activity chains not ending at home
    number_of_trips_per_agent = df_act_trips.groupby(["person_id"], sort=False)["trip_id"].max()
    is_last_trip_index = [df_act_trips["trip_id"].iloc[i] == number_of_trips_per_agent[df_act_trips["person_id"].iloc[i]]  for i in range(len(df_act_trips)) ]
    last_index_list = df_act_trips.index[np.logical_and(is_last_trip_index, df_act_trips["destination_purpose"]!="home")] 
    last_index = df_act_trips.index.isin(last_index_list)
    df_act_trips = df_act_trips[~last_index]

    # Fixing purposes and transport modes, excluding not modelled modes (bike and other)
    df_act_trips.loc[df_act_trips["destination_purpose"] == "errand", "destination_purpose"] ="other"
    df_act_trips.loc[df_act_trips["origin_purpose"] == "errand", "origin_purpose"] ="other"
    df_act_trips.loc[df_act_trips["mode"] == "motorcycle", "mode"] = "car"
    df_act_trips.loc[df_act_trips["mode"] == "taxi", "mode"] = "taxi"
    df_act_trips.loc[df_act_trips["mode"] == "ride_hailing", "mode"] = "taxi"
    df_act_trips = df_act_trips[~(df_act_trips["mode"] == "bike")]
    df_act_trips = df_act_trips[~(df_act_trips["mode"] == "other")]
    
    # Merging with person information, correcting trips with erroneous purpose
    df_act_persons.rename(columns = {"weight":"weight_person", "employment":"employed", "binary_car_availability":"number_of_cars"}, inplace = True)
    df_act = df_act_trips.merge(df_act_persons[["person_id", "weight_person", "employed", 
                                                "age", "household_income", "sex", "number_of_cars"]],
                                on=["person_id"], how='left')
    df_act.loc[(df_act["destination_purpose"]=='work') & (df_act["age"] < 16), "destination_purpose"]="other"
    df_act.loc[(df_act["origin_purpose"]=='work') & (df_act["age"] < 16), "origin_purpose"]="other"

    # Only keep the persons that could have been used in activity chain matching
    df_act = df_act[~df_act["weight_person"].isna()]
    df_act = df_act.set_index(["person_id"])
    df_act.sort_index(inplace=True)
    
    t_id = df_act_trips["person_id"].values.tolist()
    df_persons_no_trip = df_act_persons[np.logical_not(df_act_persons["person_id"].isin(t_id))]
    df_persons_no_trip = df_persons_no_trip.set_index(["person_id"])
    return df_act, df_persons_no_trip


def aux_data_frame(df_act):
    df_act["origin_purpose_first"] = df_act["origin_purpose"].apply(lambda x: x[0])
    df_act["destination_purpose_first"] = df_act["destination_purpose"].apply(lambda x: x[0])
    df2 = df_act[["origin_purpose_first", "destination_purpose_first", "weight_person"]].groupby("person_id")[
    ["origin_purpose_first", "destination_purpose_first"]
].apply(lambda x: "-".join(x["origin_purpose_first"]) + "-" + x["destination_purpose_first"].iloc[-1]).reset_index(name = "chain")

    df_aux = pd.merge(df_act["weight_person"].reset_index(), df2).drop_duplicates("person_id")
    return df_aux


def activity_chains_comparison(context, all_CC, suffix = None):
    # Get percentages, prepare for plotting
    all_CC["synthetic Count"] = all_CC ["synthetic Count"] / all_CC["synthetic Count"].sum() *100
    all_CC["actual Count"] = all_CC["actual Count"] / all_CC["actual Count"].sum() *100
    all_CC = all_CC.sort_values(by=['actual Count'], ascending=False)

    # First step done: plot activity chain counts
    title_plot = "Synthetic and HTS activity chain comparison"
    title_figure = "activitychains"
    if suffix:
        title_plot += " - " + suffix
        title_figure += "_" + suffix
        
    title_figure += ".png"
    
    myplottools.plot_comparison_bar(context, imtitle = title_figure, plottitle = title_plot, ylabel = "Percentage", xlabel = "Activity chain", lab = all_CC["Chain"], actual = all_CC["actual Count"], synthetic = all_CC["synthetic Count"])


def activity_counts_comparison(context, all_CC, suffix = None):
    all_CC_dic = all_CC.to_dict('records')
    counts_dic = {}
    for actchain in all_CC_dic:
        chain = actchain["Chain"]
        s = actchain["synthetic Count"]
        a = actchain["actual Count"]
        if np.isnan(s):
            s = 0
        if np.isnan(a):
            a = 0
        if chain == "-" or chain == "h":
            x = 0
        else:
            act = chain.split("-")
            x = len(act) - 2
        x = min(x, 7)
        if x not in counts_dic.keys():
            counts_dic[x] = [s, a]
        else:
            counts_dic[x][0] += s
            counts_dic[x][1] += a
    
    counts = pd.DataFrame(columns = ["number", "synthetic Count", "actual Count"])
    for k in range(8):
        v = counts_dic[k]
        if k == 7:
            l = "7+"
        else:
            l = str(int(k))
        counts.loc[k] = pd.Series({"number": l, 
                                      "synthetic Count": v[0],
                                      "actual Count": v[1]
                                          })
    
    # Get percentages, prepare for plotting
    counts["synthetic Count"] = counts["synthetic Count"] / counts["synthetic Count"].sum() *100
    counts["actual Count"] = counts["actual Count"] / counts["actual Count"].sum() *100
    #counts = counts.sort_values(by=['actual Count'], ascending=False)

    # First step done: plot activity chain counts
    title_plot = "Synthetic and HTS activity counts comparison"
    title_figure = "activitycounts"
    if suffix:
        title_plot += " - " + suffix
        title_figure += "_" + suffix
        
    title_figure += ".png"
    
    myplottools.plot_comparison_bar(context, imtitle = title_figure, plottitle = title_plot, 
                                    ylabel = "Percentage", xlabel = "Number of activities in the activity chain",
                                    lab = counts["number"], actual = counts["actual Count"], 
                                    synthetic = counts["synthetic Count"])
    
    
def activity_counts_per_purpose(context, all_CC, suffix = None):
    all_CC_dic = all_CC.to_dict('records')
    purposes = ['h', 'w', 'e', 's', 'l', 'o']
    counts_dic = {}
    cpt = 0
    for actchain in all_CC_dic:
        chain = actchain["Chain"]
        s = actchain["synthetic Count"]
        a = actchain["actual Count"]
        if np.isnan(s):
            s = 0
        if np.isnan(a):
            a = 0
        if chain == "-" or chain == "h":
            pass
        else:
            act = chain.split("-")
            act = act[1:-1]
            for p in purposes:
                cpt_purpose = act.count(p)
                if cpt_purpose > 0 :
                    identifier = p + " - " + str(cpt_purpose) 
                    if cpt_purpose > 1:
                        identifier += " times"
                    else:
                        identifier += " time"
                    if cpt_purpose >= 3 or (cpt_purpose == 2 and p not in ['h', 'w', 'e']):
                        identifier = "Other"
                    if identifier not in counts_dic.keys():
                        counts_dic[identifier] = [s, a]
                    else:
                        counts_dic[identifier][0] += s
                        counts_dic[identifier][1] += a
    
    counts = pd.DataFrame(columns = ["number", "synthetic Count", "actual Count"])

    for k, v in counts_dic.items():
        counts.loc[k] = pd.Series({"number": k, 
                                      "synthetic Count": v[0],
                                      "actual Count": v[1]
                                          })
            

    # Get percentages, prepare for plotting
    counts["synthetic Count"] = counts["synthetic Count"] / counts["synthetic Count"].sum() *100
    counts["actual Count"] = counts["actual Count"] / counts["actual Count"].sum() *100
    counts = counts.sort_values(by=['actual Count'], ascending=False)
    val = "Other"
    idx = counts.index.drop(val).tolist() + [val]
    counts = counts.reindex(idx)

    # First step done: plot activity chain counts
    title_plot = "Activity counts per purpose comparison"
    title_figure = "activitycountspurpose"
    if suffix:
        title_plot += " - " + suffix
        title_figure += "_" + suffix
        
    title_figure += ".png"
    
    myplottools.plot_comparison_bar(context, imtitle = title_figure, plottitle = title_plot, 
                                    ylabel = "Percentage", xlabel = "Activities with the same purpose in the activity chain",
                                    lab = counts["number"], actual = counts["actual Count"], 
                                    synthetic = counts["synthetic Count"], t = 20)
    



def mode_purpose_comparison(context, df_syn, df_act, suffix = None):
    # first in the synthetic data
    types = df_syn.groupby(["mode","following_purpose"]).count()["person_id"]
    syn = types / types.sum()

    # then in the actual data
    df_act.loc[df_act["mode"]=='car_passanger', "mode"] = 'car_passenger'
    which = ["car","car_passenger","pt", "taxi","walk"]
    atypes = df_act.groupby(["mode","destination_purpose"]).sum().loc[which,"weight_person"].reindex(index=which, level=0)
    act = atypes / atypes.sum()
    
    lista = [item for item in list(types.index.levels[0]) for i in range(len(types.index.levels[1]))]
    listb = list(types.index.levels[1]) * len(types.index.levels[0])
    labels = [a + " " + b for a, b in zip(lista,listb)]

    # already ready to plot!
    title_plot = "Synthetic and HTS Mode-Purpose Distribution"
    title_figure = "modepurpose"
    
    if suffix:
        title_plot += " - " + suffix
        title_figure += "_" + suffix
        
    title_figure += ".png"
    
    myplottools.plot_comparison_bar(context, imtitle = title_figure, plottitle = title_plot,
                                    ylabel = "Percentage", xlabel = "", lab = labels, 
                                    actual = act.values.tolist(), synthetic = syn.values.tolist(), 
                                    t = 10, xticksrot = True )


def compute_distances_synthetic(df_syn, threshold = 25):
    df_syn["crowfly_distance"] = df_syn.geometry.length
    df_syn["crowfly_distance"] = df_syn["crowfly_distance"] *0.001

    # Only consider crowfly distances shorter than <threshold> km
    df_syn_dist = df_syn[df_syn["crowfly_distance"] < threshold]
    return df_syn_dist


def compute_distances_actual(df_act, threshold = 25):
    # Compute the distances
    df_act["crowfly_distance"] = 0.001 * np.sqrt(
        (df_act["origin_x"] - df_act["destination_x"])**2 + 
        (df_act["origin_y"] - df_act["destination_y"])**2
    )
    
    df_act_dist = df_act[df_act["crowfly_distance"] < threshold]
    return df_act_dist


def compare_dist_educ(context, df_syn, df_act, suffix = None):
    pers_educ_syn = list(set(df_syn[df_syn["following_purpose"] == "education"]["person_id"].values))
    pers_educ_act = list(set(df_act[df_act["destination_purpose"] == "education"].index.values))

    df_syn_educ = df_syn[np.isin(df_syn["person_id"], pers_educ_syn)]
    df_act_educ = df_act[np.isin(df_act.index, pers_educ_act)]

    df_syn_h_e = df_syn_educ[np.logical_or( np.logical_and( df_syn_educ["preceeding_purpose"] == "home",  df_syn_educ["following_purpose"] == "education" ), np.logical_and(df_syn_educ["following_purpose"] == "home",  df_syn_educ["preceeding_purpose"] == "education")     )]
    pers_he_syn = list(set(df_syn_h_e["person_id"].values))

    df_act_h_e = df_act_educ[np.logical_or( np.logical_and( df_act_educ["origin_purpose"] == "home",  df_act_educ["destination_purpose"] == "education" ), np.logical_and(df_act_educ["destination_purpose"] == "home",  df_act_educ["origin_purpose"] == "education")     )]
    pers_he_act = list(set(df_syn_h_e.index.values))

    dic_syn = {"person_id": pers_educ_syn, "dist_home_educ": [0 for i in range(len(pers_educ_syn))]}
    dic_act = {"person_id": pers_educ_act, "weight_person": [0 for i in range(len(pers_educ_act))], "dist_home_educ": [0 for i in range(len(pers_educ_act))]}

    for i in range(len(pers_educ_syn)):
        pid = pers_educ_syn[i]
        df_pers = df_syn_educ[df_syn_educ["person_id"] == pid]
        home_coord = None
        educ_coord = None
        for index, row in df_pers.iterrows():
            if row["preceeding_purpose"] == "home":
                home_coord = row["geometry"].coords[0]
            if row["following_purpose"] == "home":
                home_coord = row["geometry"].coords[1]
            if row["preceeding_purpose"] == "education":
                educ_coord = row["geometry"].coords[0]
            if row["following_purpose"] == "education":
                educ_coord = row["geometry"].coords[1]
            if home_coord is not None and educ_coord is not None:
                break
        dic_syn["dist_home_educ"][i] = 0.001 * np.sqrt(((home_coord[0] - educ_coord[0]) ** 2 + (home_coord[1] - educ_coord[1]) ** 2))
            

    for i in range(len(pers_educ_act)):
        pid = pers_educ_act[i]
       
        df_pers = df_act_educ[df_act_educ.index == pid]
        home_x = None
        educ_y = None
        for index, row in df_pers.iterrows():
            if row["origin_purpose"] == "home":
                home_x = row["origin_x"]
                home_y = row["origin_y"]
            elif row["destination_purpose"] == "home":
                home_x = row["destination_x"]
                home_y = row["destination_y"]
            if row["origin_purpose"] == "education":
                educ_x = row["origin_x"]
                educ_y = row["origin_y"]
            elif row["destination_purpose"] == "education":
                educ_x = row["destination_x"]
                educ_y = row["destination_y"]
            if educ_y is not None and home_y is not None:
                break
        dic_act["dist_home_educ"][i] = 0.001 * np.sqrt(((home_x - educ_x) ** 2 + (home_y - educ_y) ** 2))
        dic_act["weight_person"][i] = row["weight_person"]

    dist_df_syn = pd.DataFrame.from_dict(dic_syn)
    dist_df_act = pd.DataFrame.from_dict(dic_act)

    syn = dist_df_syn["dist_home_educ"].values
    act = dist_df_act["dist_home_educ"].values
    act_w = dist_df_act["weight_person"].values

    fig, ax = plt.subplots(1,1)
    x_data = np.array(syn, dtype=np.float64)
    x_sorted = np.argsort(x_data)
    x_weights = np.array([1.0 for i in range(len(syn))], dtype=np.float64)
    x_cdf = np.cumsum(x_weights[x_sorted])
    x_cdf /= x_cdf[-1]

    y_data = np.array(act, dtype=np.float64)
    y_sorted = np.argsort(y_data)
    y_weights = np.array(act_w, dtype=np.float64)
    y_cdf = np.cumsum(y_weights[y_sorted])
    y_cdf /= y_cdf[-1]

    ax.plot(y_data[y_sorted], y_cdf, label="Actual", color = "#A3A3A3")
    ax.plot(x_data[x_sorted], x_cdf, label="Synthetic", color="#00205B")  

    imtitle = "dist_home_educ"
    plottitle = "Distance from home to education"
    if suffix:
        imtitle += "_" + suffix
        plottitle  += " - " + suffix 
    imtitle += ".png"

    ax.set_ylabel("Probability")
    ax.set_xlabel("Crowfly Distance [km]")
    ax.legend(loc="best")
    ax.set_title(plottitle)
    plt.savefig("%s/" % context.config("analysis_path") + imtitle)
    return syn, act, act_w


def all_the_plot_distances(context, df_act_dist, df_syn_dist, suffix = None):
    dph_title = "distance_purpose_hist"
    dmh_title = "distance_mode_hist"
    dpc_title = "distance_purpose_cdf"
    dmc_title = "distance_mode_cdf"
    
    if suffix:
        dph_title += "_" + suffix
        dmh_title += "_" + suffix
        dpc_title += "_" + suffix
        dmc_title += "_" + suffix
        
    dph_title += ".png"
    dph_title += ".png"
    dpc_title += ".png"
    dmc_title += ".png"
    
    myplottools.plot_comparison_hist_purpose(context, dph_title, df_act_dist, df_syn_dist, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2)
    myplottools.plot_comparison_hist_mode(context, dmh_title, df_act_dist, df_syn_dist, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2)

    myplottools.plot_comparison_cdf_purpose(context, dpc_title, df_act_dist, df_syn_dist, dpi = 300, cols = 3, rows = 2)
    myplottools.plot_comparison_cdf_mode(context, dmc_title, df_act_dist, df_syn_dist, dpi = 300, cols = 3, rows = 2)

    
def execute(context):
    # Import data, merging
    df_syn, df_syn_no_trip = import_data_synthetic(context)
    df_act, df_act_no_trip = import_data_actual(context)
    df_aux = aux_data_frame(df_act)

    # 1. ACTIVITY CHAINS

    
    # Creating the new dataframes with activity chain counts
    syn_CC = myutils.process_synthetic_activity_chain_counts(df_syn)
    syn_CC.loc[len(syn_CC) + 1] = pd.Series({"Chain": "h", "synthetic Count": df_syn_no_trip.shape[0] })
    
    act_CC = myutils.process_actual_activity_chain_counts(df_act, df_aux)
    act_CC.loc[len(act_CC) + 1] = pd.Series({"Chain": "h", "actual Count": np.sum(df_act_no_trip["weight_person"].values.tolist())})

    # Merging together, comparing
    all_CC = pd.merge(syn_CC, act_CC, on = "Chain", how = "left")
    activity_chains_comparison(context, all_CC)
    
    # Number of activities    
    activity_counts_comparison(context, all_CC)
    
    # Number of activities per purposes
    activity_counts_per_purpose(context, all_CC)

    # 2. MODE AND DESTINATION PURPOSE
    mode_purpose_comparison(context, df_syn, df_act)


    # 3. CROWFLY DISTANCES
    
    # 3.1. Compute the distances
    df_syn_dist = compute_distances_synthetic(df_syn)
    df_act_dist = compute_distances_actual(df_act) 

    # 3.2 Prepare for plotting
    df_act_dist["x"] = df_act_dist["weight_person"] * df_act_dist["crowfly_distance"]

    act = df_act_dist.groupby(["destination_purpose"]).sum()["x"] / df_act_dist.groupby(["destination_purpose"]).sum()["weight_person"]
    syn = df_syn_dist.groupby(["following_purpose"]).mean()["crowfly_distance"] 

    # 3.3 Ready to plot!
    myplottools.plot_comparison_bar(context, imtitle = "distancepurpose.png", plottitle = "Crowfly distance", ylabel = "Mean crowfly distance [km]", xlabel = "", lab = syn.index, actual = act, synthetic = syn, t = None, xticksrot = True )
    all_the_plot_distances(context, df_act_dist, df_syn_dist)

    # 3.4 Distance from home to education
    syn_0, act_0, act_w0 = compare_dist_educ(context, df_syn, df_act)
    
    
    # 4. Do the same for men and women separated, aged 18 to 40
    
    # 4.1 Create the dataframes
    df_syn_men = df_syn[df_syn["sex"] == "male"]
    df_syn_men = df_syn_men[np.logical_and(df_syn_men["age"] >= 18,
                                           df_syn_men["age"] <= 40)]
    df_syn_no_trip_men = df_syn_no_trip[df_syn_no_trip["sex"] == "male"]
    df_syn_no_trip_men = df_syn_no_trip_men[np.logical_and(df_syn_no_trip_men["age"] >= 18,
                                           df_syn_no_trip_men["age"] <= 40)]
        
    df_syn_women = df_syn[df_syn["sex"] == "female"]
    df_syn_women = df_syn_women[np.logical_and(df_syn_women["age"] >= 18,
                                           df_syn_women["age"] <= 40)]
    df_syn_no_trip_women = df_syn_no_trip[df_syn_no_trip["sex"] == "female"]
    df_syn_no_trip_women = df_syn_no_trip_women[np.logical_and(df_syn_no_trip_women["age"] >= 18,
                                           df_syn_no_trip_women["age"] <= 40)]
        
    df_act_men = df_act[df_act["sex"] == "male"]
    df_act_men = df_act_men[np.logical_and(df_act_men["age"] >= 18,
                                           df_act_men["age"] <= 40)]
    df_aux_men = aux_data_frame(df_act_men)
    df_act_no_trip_men = df_act_no_trip[df_act_no_trip["sex"] == "male"]
    df_act_no_trip_men = df_act_no_trip_men[np.logical_and(df_act_no_trip_men["age"] >= 18,
                                           df_act_no_trip_men["age"] <= 40)]
    
        
    df_act_women = df_act[df_act["sex"] == "female"]
    df_act_women = df_act_women[np.logical_and(df_act_women["age"] >= 18,
                                           df_act_women["age"] <= 40)]
    df_aux_women = aux_data_frame(df_act_women)
    df_act_no_trip_women = df_act_no_trip[df_act_no_trip["sex"] == "female"]
    df_act_no_trip_women = df_act_no_trip_women[np.logical_and(df_act_no_trip_women["age"] >= 18,
                                           df_act_no_trip_women["age"] <= 40)]
        
    # 4.2 Activity chains
    # Creating the new dataframes with activity chain counts
    M_syn_CC = myutils.process_synthetic_activity_chain_counts(df_syn_men)
    M_syn_CC.loc[len(M_syn_CC) + 1] = pd.Series({"Chain": "h", 
                                          "synthetic Count": df_syn_no_trip_men.shape[0]
                                          })
    M_act_CC = myutils.process_actual_activity_chain_counts(df_act_men, df_aux_men)
    M_act_CC.loc[len(M_act_CC) + 1] = pd.Series({"Chain": "h", 
                                          "actual Count": np.sum(df_act_no_trip_men["weight_person"].values.tolist())
                                          })
    
    W_syn_CC = myutils.process_synthetic_activity_chain_counts(df_syn_women)
    W_syn_CC.loc[len(W_syn_CC) + 1] = pd.Series({"Chain": "h", 
                                          "synthetic Count": df_syn_no_trip_women.shape[0]
                                          })
    W_act_CC = myutils.process_actual_activity_chain_counts(df_act_women, df_aux_women)
    W_act_CC.loc[len(W_act_CC) + 1] = pd.Series({"Chain": "h", 
                                          "actual Count": np.sum(df_act_no_trip_women["weight_person"].values.tolist())
                                          })
    
    # Merging together, comparing
    M_all_CC = pd.merge(M_syn_CC, M_act_CC, on = "Chain", how = "left")
    activity_chains_comparison(context, M_all_CC, "men")
    
    W_all_CC = pd.merge(W_syn_CC, W_act_CC, on = "Chain", how = "left")
    activity_chains_comparison(context, W_all_CC, "women")
    
    activity_counts_comparison(context, M_all_CC, "men")
    activity_counts_comparison(context, W_all_CC, "women")
    
    activity_counts_per_purpose(context, M_all_CC, "men")
    activity_counts_per_purpose(context, W_all_CC, "women")

    # 4.3 Mode-purpose comparison
    mode_purpose_comparison(context, df_syn_men, df_act_men, "men")
    mode_purpose_comparison(context, df_syn_women, df_act_women, "women")
    
    # 4.4 Distance-purpose comparison
    df_syn_distM = compute_distances_synthetic(df_syn_men)
    df_act_distM = compute_distances_actual(df_act_men) 
    df_act_distM["x"] = df_act_distM["weight_person"] * df_act_distM["crowfly_distance"]
    actM = df_act_distM.groupby(["destination_purpose"]).sum()["x"] / df_act_distM.groupby(["destination_purpose"]).sum()["weight_person"]
    synM = df_syn_distM.groupby(["following_purpose"]).mean()["crowfly_distance"] 
    myplottools.plot_comparison_bar(context, imtitle = "distancepurpose_men.png", 
                                    plottitle = "Crowfly distances - men", 
                                    ylabel = "Mean crowfly distance [km]", xlabel = "", 
                                    lab = synM.index, actual = actM, synthetic = synM, t = None, xticksrot = True )
    all_the_plot_distances(context, df_act_distM, df_syn_distM, suffix = "men")
    
    df_syn_distW = compute_distances_synthetic(df_syn_women)
    df_act_distW = compute_distances_actual(df_act_women) 
    df_act_distW["x"] = df_act_distW["weight_person"] * df_act_distW["crowfly_distance"]
    actW = df_act_distW.groupby(["destination_purpose"]).sum()["x"] / df_act_distW.groupby(["destination_purpose"]).sum()["weight_person"]
    synW = df_syn_distW.groupby(["following_purpose"]).mean()["crowfly_distance"] 
    myplottools.plot_comparison_bar(context, imtitle = "distancepurpose_women.png", 
                                    plottitle = "Crowfly distances - women", 
                                    ylabel = "Mean crowfly distance [km]", xlabel = "", 
                                    lab = synM.index, actual = actW, synthetic = synW, 
                                    t = None, xticksrot = True )
    all_the_plot_distances(context, df_act_distW, df_syn_distW, suffix = "women")


    # 4.5 Distance from home to education
    compare_dist_educ(context, df_syn_women, df_act_women, suffix = "women")
    compare_dist_educ(context, df_syn_men, df_act_men, suffix = "men")


    # 5 Distance from home to education according to age
    ages = [[0, 14], [15, 18], [19, 24], [25, 1000]]

    syn_means = [np.mean(syn_0)]
    act_means = [np.average(act_0, weights = act_w0)]
    labels = ["All"]
    for age in ages:
        df_syn_age = df_syn[np.logical_and(df_syn["age"] >= age[0],
                                           df_syn["age"] <= age[1] )]
        df_act_age = df_act[np.logical_and(df_act["age"] >= age[0],
                                           df_act["age"] <= age[1] )]
        suf = "aged " + str(age[0]) + " to " + str(age[1])
        lab = str(age[0]) + " to " + str(age[1]) + " y. o."
        syn, act, act_w = compare_dist_educ(context, df_syn_age, df_act_age, suffix = suf)

        syn_means.append(np.average(syn))
        act_means.append(np.average(act, weights = act_w))
        labels.append(lab)

    myplottools.plot_comparison_bar(context,"avdisthomeeduc.png", "Average distances from home to education", "Average distance [km]", "Population group", labels, act_means, syn_means)

    # Zipping modes in correct order
    #modes = zip(np.sort(df_syn["mode"].unique()),["car","car_passenger","pt", "taxi", "walk"])


    # Fourth step: mode share
    #plot_mode_share(df_syn, amdf2, dpi = 300)

    ## TODO: overall percentage of mode share by share
    
    #df_syn, amdf = add_geo_location_to_origin_and_destination(df_syn, amdf)
   






    
    












