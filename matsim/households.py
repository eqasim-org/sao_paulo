import gzip
from tqdm import tqdm
import numpy as np
import matsim.writers
import pandas as pd
import io

def configure(context, require):
    require.stage("synthesis.sociodemographics")
    require.stage("synthesis.spatial.by_person.primary_locations")

FIELDS = ["person_id", "household_id", "binary_car_availability", "hhlIncome"]

def add_household(writer, household, member_ids):
    writer.start_household(household[1])
    writer.add_members(member_ids)
    writer.add_income(household[3])

    writer.start_attributes()
    #writer.add_attribute("numberOfCars", "java.lang.Integer", str(int(household[5])))
    writer.add_attribute("carAvailability", "java.lang.String", household[3])
    #writer.add_attribute("bikeAvailability", "java.lang.String", household[4])
   # writer.add_attribute("residenceZoneCategory", "java.lang.Integer", household[8])
   # writer.add_attribute("householdIncomePerConsumptionUnit", "java.lang.Double", str(household[3]))
   # writer.add_attribute("consumptionUnits", "java.lang.Double", str(household[9]))
   # writer.add_attribute("totalHouseholdIncome", "java.lang.Double", str(household[10]))
    writer.end_attributes()

    writer.end_household()

def execute(context):
    cache_path = context.cache_path

    df_persons = context.stage("population.sociodemographics").sort_values(by = ["household_id", "person_id"])
    #df_home = context.stage("population.spatial.by_person.primary_locations")[0][[
    #    "location_id", #"residence_zone_category"
    #]]

    #df_persons = pd.merge(df_persons, df_home, on = "household_id", how = "left")
    df_persons = df_persons[FIELDS]

    with gzip.open("%s/households.xml.gz" % cache_path, "w+") as f:
        with io.BufferedWriter(f, buffer_size = 1024  * 1024 * 1024 * 2) as raw_writer:
            writer = matsim.writers.HouseholdsWriter(raw_writer)
            writer.start_households()

            household = [None, None]
            member_ids = []

            for item in tqdm(df_persons.itertuples(), total = len(df_persons)):
                if not household[1] == item[1]:
                    if household[0] is not None: add_household(writer, household, member_ids)
                    household, member_ids = item, [item[2]]
                else:
                    member_ids.append(item[2])

            if household[0] is not None: add_household(writer, household, member_ids)

            writer.end_households()

    return "%s/households.xml.gz" % cache_path

