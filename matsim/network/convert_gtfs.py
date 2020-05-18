import subprocess as sp
import os.path
from gtfsmerger import GTFSMerger
import zipfile
import pandas as pd

def configure(context, require):
    require.stage("matsim.java.pt2matsim")
    require.stage("utils.java")
    require.config("raw_data_path")

def execute(context):
    jar = context.stage("matsim.java.pt2matsim")
    java = context.stage("utils.java")

    #first merge gtfs schedules
    n = GTFSMerger()
    gtfs_1 = open("%s/gtfs/emtu.zip" % context.config["raw_data_path"], 'rb').read()
    gtfs_2 = open("%s/gtfs/sptrans.zip" % context.config["raw_data_path"], 'rb').read()
    n.merge_from_bytes_list([ gtfs_1, gtfs_2 ])
    n.get_zipfile("%s/gtfs/gtfs_merged.zip" % context.config["raw_data_path"])
    with zipfile.ZipFile("%s/gtfs/gtfs_merged.zip" % context.config["raw_data_path"], 'r') as zip_ref:
        zip_ref.extractall("%s/gtfs/gtfs_merged/" % context.config["raw_data_path"])
        
    data = pd.read_csv("%s/gtfs/gtfs_merged/calendar.txt" % context.config["raw_data_path"])
    data["end_date"] = data["end_date"].str.replace("-","")
    data["start_date"] = data["start_date"].str.replace("-","")
    data.to_csv("%s/gtfs/gtfs_merged/calendar.txt" % context.config["raw_data_path"])
    data = pd.read_csv("%s/gtfs/gtfs_merged/calendar_dates.txt" % context.config["raw_data_path"])
    data["date"] = data["date"].str.replace("-","")
    data.to_csv("%s/gtfs/gtfs_merged/calendar_dates.txt" % context.config["raw_data_path"])
    # Create MATSim schedule
    temp_path = "%s/__java_tmp" % context.cache_path
    java(jar, "org.matsim.pt2matsim.run.Gtfs2TransitSchedule", [
        "%s/gtfs/gtfs_merged" % context.config["raw_data_path"],
        "20180314", "EPSG:29183",
        "%s/transit_schedule_test.xml.gz" % context.cache_path,
        "%s/transit_vehicles_test.xml.gz" % context.cache_path
    ], cwd = context.cache_path)

    assert(os.path.exists("%s/transit_schedule_test.xml.gz" % context.cache_path))
    assert(os.path.exists("%s/transit_vehicles_test.xml.gz" % context.cache_path))

    return {
        "schedule" : "%s/transit_schedule_test.xml.gz" % context.cache_path,
        "vehicles" : "%s/transit_vehicles_test.xml.gz" % context.cache_path
    }
