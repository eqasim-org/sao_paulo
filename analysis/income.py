import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tck

def configure(context, require):
    pass

def plot_cdf(cases, boundaries, minimum):
    plt.figure(dpi = 120, figsize = (6, 4))

    for df, column, weight_column, label in cases:
        f = ~df[column].isna()
        f &= df[column] > minimum

        values = df[f][column].values
        weights = df[f][weight_column].values

        cdf = np.array([np.sum(weights[values <= boundary]) for boundary in boundaries], dtype = np.float)
        cdf /= np.sum(weights)
        plt.plot(boundaries, cdf, label = label)

    plt.xlim([0, np.max(boundaries)])
    plt.grid()
    plt.legend()
    plt.xlabel("Income [> %d]" % minimum)
    plt.ylabel("CDF")
    plt.tight_layout()

def plot_poor(cases, boundary, show_nan = False):
    plt.figure(dpi = 120, figsize = (6, 4))

    for index, (df, column, weight_column, label) in enumerate(cases):
        f = ~df[column].isna()

        smaller = np.sum(df[f & (df[column] <= boundary) & (df[column] > 0)][weight_column])
        larger = np.sum(df[f & (df[column] > boundary)][weight_column])
        zero = np.sum(df[f & (df[column] == 0.0)][weight_column])
        nan = np.sum(df[~f][weight_column])

        if not show_nan:
            nan = 0

        total = smaller + larger + nan + zero

        smaller /= total
        larger /= total
        nan /= total
        zero /= total

        plt.barh(y = index, height = 0.5, width = nan, color = "C%d" % index, alpha = 0.0)
        plt.barh(y = index, height = 0.5, width = zero, left = nan, color = "C%d" % index, alpha = 0.33)
        plt.barh(y = index, height = 0.5, width = smaller, left = zero + nan, color = "C%d" % index, alpha = 0.66)
        plt.barh(y = index, height = 0.5, width = larger, left = zero + smaller + nan, color = "C%d" % index)

    plt.xlim([0, 1.0])
    plt.gca().yaxis.set_major_locator(tck.FixedLocator(np.arange(len(cases))))
    plt.gca().yaxis.set_major_formatter(tck.FixedFormatter([case[3] for case in cases]))

    if show_nan:
        plt.barh(y = [0], width = [0], color = "k", alpha = 0.0, label = "NaN")

    plt.barh(y = [0], width = [0], color = "k", alpha = 0.33, label = "== 0")
    plt.barh(y = [0], width = [0], color = "k", alpha = 0.66, label = "<= %d" % boundary)
    plt.barh(y = [0], width = [0], color = "k", alpha = 1.0, label = "> %d" % boundary)

    plt.ylim([-0.5, len(cases)])
    plt.legend(loc = "best", ncol = 4)
    plt.tight_layout()

def execute(context):
    df_hts = pd.read_csv("%s/HTS/persons_clean_allworkdays_alltogether.csv" % context.config["raw_data_path"])
    df_census = pd.read_csv("%s/Census/census_cleaned.csv" % context.config["raw_data_path"])
    df_census["ratio"] = df_census["householdIncome"] / df_census["numberOfMembers"]

    cases = [
        (df_hts, "personal_income", "weight_person", "HTS personal_income"),
        (df_census, "salaryAMount", "personWeight", "Census salaryAMount"),
        (df_census, "totalIncome", "personWeight", "Census totalIncome"),
        #(df_census, "householdIncome", "personWeight", "Census householdIncome"),
        (df_census, "ratio", "personWeight", "Census householdIncome \n/ numberOfMembers")
    ]

    boundaries = np.arange(0, 5 * 1e3, 1e2)
    plot_cdf(cases, boundaries, 500.0)
    plt.savefig("%s/distribution.png" % context.cache_path)

    boundary = 500
    plot_poor(cases, boundary, show_nan = True)
    plt.savefig("%s/poor_with_nan.png" % context.cache_path)

    boundary = 500
    plot_poor(cases, boundary, show_nan = False)
    plt.savefig("%s/poor_without_nan.png" % context.cache_path)
