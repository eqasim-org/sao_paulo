import numpy as np
import matplotlib.pyplot as plt

def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{:.2f}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')



def add_small_hist(axes, r, c, act, x, y, bins, lab = ["Synthetic", "HTS"]):
    axes[r,c].hist(x, bins, alpha=0.5, label=lab[0], density=True)
    axes[r,c].hist(y["crowfly_distance"], bins, weights=y["weight_person"], alpha=0.5, label=lab[1], density=True)
    axes[r,c].set_ylabel("Percentage")
    axes[r,c].set_xlabel("Crowfly Distance [km]")
    axes[r,c].set_title("Activity: " + act.capitalize())
    axes[r,c].legend(loc="best")
    return axes


def add_small_cdf(axes, r, c, act, x, y, lab = ["Synthetic", "HTS"]):
    x_data = np.array(x, dtype=np.float64)
    x_sorted = np.argsort(x_data)
    x_weights = np.array([1.0 for i in range(len(x))], dtype=np.float64)
    x_cdf = np.cumsum(x_weights[x_sorted])
    x_cdf /= x_cdf[-1]

    y_data = np.array(y["crowfly_distance"], dtype=np.float64)
    y_sorted = np.argsort(y_data)
    y_weights = np.array(y["weight_person"], dtype=np.float64)
    y_cdf = np.cumsum(y_weights[y_sorted])
    y_cdf /= y_cdf[-1]

    axes[r,c].plot(y_data[y_sorted], y_cdf, label=lab[1], color = "#A3A3A3")
    axes[r,c].plot(x_data[x_sorted], x_cdf, label=lab[0], color="#00205B")   

    axes[r,c].set_ylabel("Percentage")
    axes[r,c].set_xlabel("Crowfly Distance [km]")
    axes[r,c].set_title("Activity: " + act.capitalize())
    axes[r,c].legend(loc="best")
    return axes


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

    ax.bar(x - width/2, actual_means, width, label = lablist[0], color="#00205B")
    ax.bar(x + width/2, synthetic_means, width, label = lablist[1], color="#D3D3D3")

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


def plot_comparison_hist_purpose(context, title, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
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
    plt.savefig("%s/" % context.config("analysis_path") + title)



def plot_comparison_hist_mode(context, title, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
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
    plt.savefig("%s/" % context.config("analysis_path") + title)



def plot_comparison_cdf_purpose(context, title, actual_df, synthetic_df, dpi = 300, cols = 3, rows = 2):
    modelist = synthetic_df["following_purpose"].unique()
    plt.rcParams['figure.dpi'] = dpi
    fig, axes = plt.subplots(nrows=rows, ncols=cols)
    idx=0
    for r in range(rows):
        for c in range(cols):
            x = synthetic_df[synthetic_df["following_purpose"]==modelist[idx]]["crowfly_distance"]
            y = actual_df[actual_df["destination_purpose"]==modelist[idx]][["crowfly_distance", "weight_person"]]
            axes = add_small_cdf(axes, r, c, modelist[idx], x, y)
            idx = idx + 1   
     
    fig.tight_layout()
    plt.savefig("%s/" % context.config("analysis_path") + title)


def plot_comparison_cdf_mode(context, title, actual_df, synthetic_df, bins = np.linspace(0,25,120), dpi = 300, cols = 3, rows = 2):
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
    plt.savefig("%s/" % context.config("analysis_path") + title)




def plot_mode_share(context, title, df_syn, df2, amdf2, dpi = 300):
    modelist=list(zip(np.sort(df_syn["mode"].unique()),["car","car_passenger","pt", "taxi", "walk"]))
    plt.rcParams['figure.dpi'] = dpi
    y1 = []
    y2 = []
    for mode,mode_cat in modelist:
        y1.append(df2[df2["mode"]==mode]["crowfly_distance"].count() / len(df2))
        # use person weight for weigthing instead
        y2.append(amdf2[amdf2["mode"]==mode_cat]["weight_person"].sum() / amdf2["weight_person"].sum())
    
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
    plt.savefig("%s/" % context.config("analysis_path") + title)
    plt.show()






