

def overall_percentage_of_mode_share_for_modes():
    df["crowfly_distance_km"]=df["crowfly_distance"]*0.001
    bins = np.linspace(0, 20, 21)

    data = []
    adata = []
    for mode,mode_cat in modelist:
        data.append(np.histogram(df[df["mode"]==mode]["crowfly_distance_km"],bins=bins)[0])
        # weight by person weight for actual data
        # from docu: "Each value only contributes its associated weight towards the bin count (instead of 1)"
        adata.append(np.histogram(amdf[amdf["mode"]==mode_cat]["crowfly_distance"], bins=bins, weights = amdf[amdf["mode"]==mode_cat]["weight_person"])[0])
    data = np.array(data)
    adata = np.array(adata)

    totals = [data[:,i].sum() for i in range(len(data[0]))]
    atotals = [adata[:,i].sum() for i in range(len(adata[0]))]

    # normalize and reformat
    dn = np.array([(data[:,i]/totals[i]*100) for i in range(len(data[0]))])
    adn = np.array([(adata[:,i]/atotals[i]*100) for i in range(len(adata[0]))])

    r = bins[:-1]
    for i,mode in enumerate(modelist):
        plt.bar(r,dn[:,i],bottom=dn[:,:i].sum(axis=1),label=mode[0])
    plt.xlabel("Crowfly Distance [km]")    
    plt.ylabel("Percentage [%]")
    plt.title("Share of different modes Synthetic")
    plt.legend(loc="best")
    plt.show()

    r = bins[:-1]
    for i,mode in enumerate(modelist):
        plt.bar(r,adn[:,i],bottom=adn[:,:i].sum(axis=1),label=mode[0])
    plt.xlabel("Crowfly Distance [km]")    
    plt.ylabel("Percentage [%]")
    plt.title("Share of different modes Actual")
    plt.legend(loc="best")
    plt.show()

    # now plotting each mode on its own

    modelist=list(zip(np.sort(df["mode"].unique()),["car","car_passenger","pt", "walk", "taxi"]))
    plt.rcParams['figure.dpi'] = 300

    cols = 2
    rows = 3

    x = bins[:-1]

    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    width = 0.45
    idx=0
    for r in range(rows):
        for c in range(cols):
            y1 = dn[:,idx]
            y2 = adn[:,idx]     
            axes[r,c].bar(x - width/2, y1, width, label='synthetic')
            axes[r,c].bar(x + width/2, y2, width, label='actual')
            axes[r,c].set_ylabel("Percentage")
            axes[r,c].set_xlabel("Crowfly Distance [km]")
        
            axes[r,c].set_title("Mode: "+modelist[idx][0])
            axes[r,c].legend(loc="best")
        
            idx=idx+1
            if idx==5:
                break
    fig.delaxes(axes[2,1])   
    fig.tight_layout()
    fig.show()
    plt.savefig("SP_ModeShare_DistanceBins_Shopping_4.png")

    df[(df["mode"]=="car") & (df["age"]>70)]


def county_county_mode_share():
    # create county-county dataframes
    cdf = df[df["ori_geoloc"] == df["dest_geoloc"]]
    camdf = amdf[amdf["ori_geoloc"] == amdf["dest_geoloc"]]

    #Mode-share 

    modelist=list(zip(np.sort(df["mode"].unique()),["car","car_passenger","pt", "taxi", "walk"]))
    plt.rcParams['figure.dpi'] = 300

    y1 = []
    y2 = []
    for mode,mode_cat in modelist:
        y1.append(cdf[cdf["mode"]==mode]["crowfly_distance"].count() / len(cdf))
        # use person weight for weigthing instead
        y2.append(camdf[camdf["mode"]==mode_cat]["weight_person"].sum() / camdf["weight_person"].sum())

    labels = [i[0] for i in modelist]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, y2, width, label='HTS',color="#00205B")
    rects2 = ax.bar(x + width/2, y1, width, label='Synthetic',color="#D3D3D3")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Percentage')
    ax.set_title('Zone-Zone Mode-share')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    plt.savefig("SP_WithinZone_ModeShare.png")

    plt.show()

    # share diagrams for county-county share km wise
    bins = np.linspace(0, 50, 51)

    data = []
    adata = []
    for mode,mode_cat in modelist:
        data.append(np.histogram(cdf[cdf["mode"]==mode]["crowfly_distance"],bins=bins)[0])
        # weight by person weight for actual data
        # from docu: "Each value only contributes its associated weight towards the bin count (instead of 1)"
        adata.append(np.histogram(camdf[camdf["mode"]==mode_cat]["crowfly_distance"],bins=bins, weights = camdf[camdf["mode"]==mode_cat]["weight_person"])[0])

    data = np.array(data)
    adata = np.array(adata)

    totals = [data[:,i].sum() for i in range(len(data[0]))]
    atotals = [adata[:,i].sum() for i in range(len(adata[0]))]

    # normalize and reformat
    dn = np.array([(data[:,i]/totals[i]*100) for i in range(len(data[0]))])
    adn = np.array([(adata[:,i]/atotals[i]*100) for i in range(len(adata[0]))])

    r = bins[:-1]
    for i,mode in enumerate(modelist):
        plt.bar(r,dn[:,i],bottom=dn[:,:i].sum(axis=1),label=mode[0])

    plt.xlabel("Crowfly Distance [km]")    
    plt.ylabel("Percentage [%]")
    plt.title("Share of different modes Synthetic")
    plt.legend(loc="best")
plt.show()

    r = bins[:-1]
    for i,mode in enumerate(modelist):
        plt.bar(r,adn[:,i],bottom=adn[:,:i].sum(axis=1),label=mode[0])

    plt.xlabel("Crowfly Distance [km]")    
    plt.ylabel("Percentage [%]")
    plt.title("Share of different modes Actual")
    plt.legend(loc="best")
    plt.show()

    # now plotting each mode on its own

    modelist=list(zip(np.sort(df["mode"].unique()),["car_alone","carpooled","pt","bicycle_walk"]))
    plt.rcParams['figure.dpi'] = 100

    cols = 2
    rows = 2

    x = bins[:-1]

    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    width = 0.35
    idx=0
    for r in range(rows):
        for c in range(cols):
            y1 = dn[:,idx]
            y2 = adn[:,idx]

            axes[r,c].bar(x - width/2, y1, width, label='synthetic')
            axes[r,c].bar(x + width/2, y2, width, label='actual')
            axes[r,c].set_ylabel("Percentage")
            axes[r,c].set_xlabel("Crowfly Distance [km]")
        
            axes[r,c].set_title("Mode: "+modelist[idx][0])
            axes[r,c].legend(loc="best")
        
            idx=idx+1
        
    fig.tight_layout()
    fig.show()


def mode_share_dep_time():
    # comparing different modes for actual and synthetic

    modelist=list(zip(np.sort(df["mode"].unique()),["car","car_passenger","pt", "taxi", "walk"]))
    plt.rcParams['figure.dpi'] = 300

    cols = 2
    rows = 2

    fig, axes = plt.subplots(nrows=rows, ncols=cols)

    bins=np.linspace(0, 24, 25)
    idx=0

    for r in range(rows):
        for c in range(cols):
            x = df[df["mode"]==modelist[idx][0]]["start_time"]/3600    # divide by 3600 to get hours
            # for amdf need to convert from local format hh:mm:ss to hours
            hours = pd.to_timedelta(amdf[amdf["mode"]==modelist[idx][1]]["departure_h"], unit='h')
            minutes = pd.to_timedelta(amdf[amdf["mode"]==modelist[idx][1]]["departure_m"], unit='m')
            y = pd.to_timedelta(hours + minutes).dt.total_seconds().to_numpy() / 3600

            # need to set weigths manually
            x_w = np.empty(x.shape)
            x_w.fill(1/x.shape[0])
            y_w = np.empty(y.shape)
            y_w.fill(1/y.shape[0])
        
            axes[r,c].hist(y,bins,alpha=0.5,weights=y_w,label='HTS')
            axes[r,c].hist(x,bins,alpha=0.5,weights=x_w,label="Synthetic")
            axes[r,c].set_ylabel("Percentage")
            axes[r,c].set_xlabel("Daytime [h]")
            axes[r,c].set_title("Mode: "+modelist[idx][0])
            axes[r,c].legend(loc="best")
        
            idx=idx+1
        
    fig.tight_layout()
    fig.show()
    plt.savefig("SP_DepartureTime.png")

    df_home = pd.read_csv("home.csv")
    df_work = pd.read_csv("work_differentzone.csv")
    df_work_zones = pd.read_csv("work_zones.csv")
    df_work_zones=df_work_zones.rename({"zone_id" : "work_zone_id"}, axis = 1)

    df_homework = df_home.merge(df_work, on="person_id").dropna()
    df_homework = df_homework.merge(df_work_zones, on="person_id")
    df_homework["distance"] = np.sqrt((df_homework["x_x"] - df_homework["x_y"])**2 + (df_homework["y_x"] - df_homework["y_y"])**2)

    print(len(df_homework[['zone_id', 'work_zone_id', 'distance', 'household_id']]['zone_id'].unique()))

    df_work[df_work["person_id"]==25363]
    df_homework["distance"].mean()
    df_opportunities = pd.read_csv("opportunities.csv")
    df_opportunities[df_opportunities["location_id"]==67365]

