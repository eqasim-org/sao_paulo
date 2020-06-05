import os.path
from gtfsmerger import GTFSMerger
import matsim.runtime.pt2matsim as pt2matsim
import zipfile
import pandas as pd

def configure(context):
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.pt2matsim")
    context.config("data_path")

def execute(context):
    n = GTFSMerger()
    gtfs_1 = open("%s/gtfs/emtu.zip" % context.config("data_path"), 'rb').read()
    gtfs_2 = open("%s/gtfs/sptrans.zip" % context.config("data_path"), 'rb').read()
    n.merge_from_bytes_list([ gtfs_1, gtfs_2 ])

    n.get_zipfile("%s/gtfs/gtfs_merged.zip" % context.config("data_path"))
    with zipfile.ZipFile("%s/gtfs/gtfs_merged.zip" % context.config("data_path"), 'r') as zip_ref:
        zip_ref.extractall("%s/gtfs/gtfs_merged/" % context.config("data_path"))
        
    data = pd.read_csv("%s/gtfs/gtfs_merged/calendar.txt" % context.config("data_path"))
    data["end_date"] = data["end_date"].str.replace("-","")
    data["start_date"] = data["start_date"].str.replace("-","")
    data.to_csv("%s/gtfs/gtfs_merged/calendar.txt" % context.config("data_path"))

    data = pd.read_csv("%s/gtfs/gtfs_merged/calendar_dates.txt" % context.config("data_path"))
    data["date"] = data["date"].str.replace("-","")
    data.to_csv("%s/gtfs/gtfs_merged/calendar_dates.txt" % context.config("data_path"))

    
    pt2matsim.run(context, "org.matsim.pt2matsim.run.Gtfs2TransitSchedule", [
        "%s/gtfs/gtfs_merged" % context.config("data_path"),
        "dayWithMostServices", "EPSG:29183", # TODO: dayWithMostServices should be made explicit and configurable!
        "%s/transit_schedule.xml.gz" % context.path(),
        "%s/transit_vehicles.xml.gz" % context.path()
    ])

    assert(os.path.exists("%s/transit_schedule.xml.gz" % context.path()))
    assert(os.path.exists("%s/transit_vehicles.xml.gz" % context.path()))

    return dict(
        schedule_path = "transit_schedule.xml.gz",
        vehicles_path = "transit_vehicles.xml.gz"
    )

def validate(context):
    if not os.path.exists("%s/gtfs/emtu.zip" % context.config("data_path")) or not os.path.exists("%s/gtfs/sptrans.zip" % context.config("data_path")):
        raise RuntimeError("GTFS data is not available")

    return os.path.getsize("%s/gtfs/emtu.zip" % context.config("data_path"))
