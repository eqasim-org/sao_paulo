import gzip
from tqdm import tqdm
import numpy as np
import io
import matsim.writers

def configure(context, require):
    require.stage("population.opportunities")
    require.stage("population.spatial.by_person.primary_locations")

FIELDS = [
    "location_id", "x", "y",
    "offers_work", "offers_education", "offers_other", "offers_leisure", "offers_shop"
]

def make_options(item):
    options = []
    if item[4]: options.append("work")
    if item[5]: options.append("education")
    if item[6]: options.append("other")
    if item[7]: options.append("leisure")
    if item[8]: options.append("shop")
    return options

def execute(context):
    cache_path = context.cache_path

    with gzip.open("%s/facilities.xml.gz" % cache_path, "w+") as f:
        with io.BufferedWriter(f, buffer_size = 1024  * 1024 * 1024 * 2) as raw_writer:
            writer = matsim.writers.FacilitiesWriter(raw_writer)
            writer.start_facilities()

            # First, write actual facilities (from BPE)
            df_statent = context.stage("population.opportunities")
            df_statent = df_statent[FIELDS]

            for item in tqdm(df_statent.itertuples(), total = len(df_statent), desc = "Facilities"):
                writer.start_facility(item[1], item[2], item[3])
                if item[4]: writer.add_activity("work")
                if item[5]: writer.add_activity("education")
                if item[6]: writer.add_activity("other")
                if item[7]: writer.add_activity("leisure")
                if item[8]: writer.add_activity("shop")
                writer.end_facility()

            # Second, write household facilities
            df_households = context.stage("population.spatial.by_person.primary_locations")[0][[
                "person_id", "x", "y"
            ]]

            for item in tqdm(df_households.itertuples(), total = len(df_households), desc = "Homes"):
                writer.start_facility("home%s" % item[1], item[2], item[3])
                writer.add_activity("home")
                writer.end_facility()

            writer.end_facilities()

    return "%s/facilities.xml.gz" % cache_path
