import gzip
from tqdm import tqdm
import numpy as np
import io
import matsim.writers
import pandas as pd

def configure(context, require):
    require.stage("population.sociodemographics")
    require.stage("population.trips")
    require.stage("population.activities")
    require.stage("population.spatial.locations")

class PersonWriter:
    def __init__(self, person):
        self.person = person
        self.activities = []

    def add_activity(self, activity):
        self.activities.append(activity)

    def write(self, writer):
        writer.start_person(self.person[1])

        # Attributes
        writer.start_attributes()
        writer.add_attribute("age", "java.lang.Integer", str(self.person[2]))
        writer.add_attribute("sex", "java.lang.String", self.person[3][0])
        writer.add_attribute("employment", "java.lang.String", self.person[4])
        writer.add_attribute("censusId", "java.lang.Integer", str(self.person[5]))
        writer.add_attribute("htsId", "java.lang.String", str(self.person[6]))
        writer.add_attribute("isPassenger", "java.lang.Boolean", writer.true_false(self.person[7]))
        writer.add_attribute("carAvailability", "java.lang.String", "always" if self.person[8] else "never")
        writer.add_attribute("hhlIncome", "java.lang.Double", str(self.person[9]))
        writer.add_attribute("ptSubscription", "java.lang.Boolean", writer.true_false(self.person[10]))
        writer.end_attributes()

        # Plan
        writer.start_plan(selected = True)

        home_facility_id = "home%s" % self.person[1]
        home_location = writer.location(self.activities[0][8], self.activities[0][9], home_facility_id)

        for i in range(len(self.activities)):
            activity = self.activities[i]
            location = home_location if np.isnan(activity[10]) else writer.location(activity[8], activity[9], int(activity[10]))

            start_time = activity[3] if not np.isnan(activity[3]) else None
            end_time = activity[4] if not np.isnan(activity[4]) else None

            writer.add_activity(activity[6], location, start_time, end_time)

            if not activity[7]:
                next_activity = self.activities[i + 1]
                writer.add_leg(activity[11], activity[4], next_activity[3] - activity[4])

        writer.end_plan()
        writer.end_person()

PERSON_FIELDS = ["person_id", "age", "sex", "employment", "census_person_id", "hts_person_id", "is_passenger", "binary_car_availability", "hhlIncome", "has_pt_subscription"]
ACTIVITY_FIELDS = ["person_id", "activity_id", "start_time", "end_time", "duration", "purpose", "is_last", "x", "y", "location_id", "following_mode"] #, "location_id", "following_mode"]

def execute(context):
    cache_path = context.cache_path
    df_persons = context.stage("population.sociodemographics")
    df_activities = context.stage("population.activities")

    # Attach following modes to activities
    df_trips = pd.DataFrame(context.stage("population.trips"), copy = True)[["person_id", "trip_id", "mode"]]
    df_trips.columns = ["person_id", "activity_id", "following_mode"]
    df_activities = pd.merge(df_activities, df_trips, on = ["person_id", "activity_id"], how = "left")

    # Attach locations to activities
    df_locations = context.stage("population.spatial.locations")
    df_activities = pd.merge(df_activities, df_locations, on = ["person_id", "activity_id"], how = "left")

    # Bring in correct order (although it should already be)
    df_persons = df_persons.sort_values(by = "person_id")
    df_activities = df_activities.sort_values(by = ["person_id", "activity_id"])

    df_persons = df_persons[PERSON_FIELDS]
    df_activities = df_activities[ACTIVITY_FIELDS]

    person_iterator = iter(df_persons.itertuples())
    activity_iterator = iter(df_activities.itertuples())

    number_of_written_persons = 0
    number_of_written_activities = 0

    with gzip.open("%s/population.xml.gz" % cache_path, "w+") as f:
        with io.BufferedWriter(f, buffer_size = 1024  * 1024 * 1024 * 2) as raw_writer:
            writer = matsim.writers.PopulationWriter(raw_writer)
            writer.start_population()

            with tqdm(total = len(df_persons), desc = "Writing persons ...") as progress:
                try:
                    while True:
                        person = next(person_iterator)
                        is_last = False

                        person_writer = PersonWriter(person)

                        while not is_last:
                            activity = next(activity_iterator)
                            is_last = activity[7]
                            assert(person[1] == activity[1])

                            person_writer.add_activity(activity)
                            number_of_written_activities += 1

                        person_writer.write(writer)
                        number_of_written_persons += 1
                        progress.update()
                except StopIteration:
                    pass

            writer.end_population()

            assert(number_of_written_activities == len(df_activities))
            assert(number_of_written_persons == len(df_persons))

    return "%s/population.xml.gz" % cache_path
