import subprocess as sp
import os.path

def configure(context, require):
    require.stage("matsim.java.pt2matsim")
    require.stage("utils.java")
    require.stage("matsim.network.convert_osm")
    require.stage("matsim.network.convert_gtfs")

def execute(context):
    jar = context.stage("matsim.java.pt2matsim")
    java = context.stage("utils.java")

    unmapped_network_path = context.stage("matsim.network.convert_osm")
    unmapped_schedule_path = context.stage("matsim.network.convert_gtfs")["schedule"]

    # Map schedule to MATSim network

    java(jar, "org.matsim.pt2matsim.run.CreateDefaultPTMapperConfig", [
        "map_network_template.xml"
    ], cwd = context.cache_path)

    content = open("%s/map_network_template.xml" % context.cache_path).read()

    content = content.replace(
        '<param name="inputNetworkFile" value="" />',
        '<param name="inputNetworkFile" value="%s" />' % unmapped_network_path
    )
    content = content.replace(
        '<param name="inputScheduleFile" value="" />',
        '<param name="inputScheduleFile" value="%s" />' % unmapped_schedule_path
    )
    content = content.replace(
        '<param name="numOfThreads" value="2" />',
        '<param name="numOfThreads" value="%d" />' % context.config["threads"]
    )
    content = content.replace(
        '<param name="outputNetworkFile" value="" />',
        '<param name="outputNetworkFile" value="%s/mapped_network.xml.gz" />' % context.cache_path
    )
    content = content.replace(
        '<param name="outputScheduleFile" value="" />',
        '<param name="outputScheduleFile" value="%s/mapped_schedule.xml.gz" />' % context.cache_path
    )
    content = content.replace(
        '<param name="outputStreetNetworkFile" value="" />',
        '<param name="outputStreetNetworkFile" value="%s/road_network.xml.gz" />' % context.cache_path
    )

    content = content.replace(
        '<param name="modesToKeepOnCleanUp" value="car" />',
        '<param name="modesToKeepOnCleanUp" value="car,car_passenger,truck" />'
    )

    with open("%s/map_network.xml" % context.cache_path, "w+") as f:
        f.write(content)

    java(jar, "org.matsim.pt2matsim.run.PublicTransitMapper", [
        "map_network.xml"
    ], cwd = context.cache_path)

    assert(os.path.exists("%s/mapped_network.xml.gz" % context.cache_path))
    assert(os.path.exists("%s/mapped_schedule.xml.gz" % context.cache_path))
    assert(os.path.exists("%s/road_network.xml.gz" % context.cache_path))
    assert(os.path.exists(context.stage("matsim.network.convert_gtfs")["vehicles"]))

    return {
        "network" : "%s/mapped_network.xml.gz" % context.cache_path,
        "schedule" : "%s/mapped_schedule.xml.gz" % context.cache_path,
        "road_network" : "%s/road_network.xml.gz" % context.cache_path,
        "vehicles" : context.stage("matsim.network.convert_gtfs")["vehicles"]
    }
