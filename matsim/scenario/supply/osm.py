import os.path

import matsim.runtime.pt2matsim as pt2matsim

def configure(context):
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.pt2matsim")

    context.config("data_path")

def execute(context):
    content = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE config SYSTEM "http://www.matsim.org/files/dtd/config_v2.dtd">
    <config>
	<module name="OsmConverter" >
		<!-- Sets whether the detailed geometry of the roads should be retained in the conversion or not.
		Keeping the detailed paths results in a much higher number of nodes and links in the resulting MATSim network.
		Not keeping the detailed paths removes all nodes where only one road passes through, thus only real intersections
		or branchings are kept as nodes. This reduces the number of nodes and links in the network, but can in some rare
		cases generate extremely long links (e.g. for motorways with only a few ramps every few kilometers).
		Defaults to <code>false</code>. -->
		<param name="keepPaths" value="false" />
		<!-- If true: The osm tags for ways and containing relations are saved as link attributes in the network. Increases filesize. Default: true. -->
		<param name="keepTagsAsAttributes" value="true" />
		<!-- Keep all ways (highway=* and railway=*) with public transit even if they don't have wayDefaultParams defined -->
		<param name="keepWaysWithPublicTransit" value="true" />
		<param name="maxLinkLength" value="500.0" />
		<!-- The path to the osm file. -->
		<param name="osmFile" value="/nas/balacm/Data_SP/osm/sao_paulo.osm.gz" />
		<param name="outputCoordinateSystem" value="EPSG:29183" />
		<param name="outputNetworkFile" value="network.xml.gz" />
		<!-- In case the speed limit allowed does not represent the speed a vehicle can actually realize, e.g. by constrains of
		traffic lights not explicitly modeled, a kind of "average simulated speed" can be used.
		Defaults to false. Set true to scale the speed limit down by the value specified by the wayDefaultParams) -->
		<param name="scaleMaxSpeed" value="false" />
		<parameterset type="routableSubnetwork" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="subnetworkMode" value="car" />
		</parameterset>
		<parameterset type="routableSubnetwork" >
			<param name="allowedTransportModes" value="bus,car,car_passenger,taxi" />
			<param name="subnetworkMode" value="bus" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="33.3333" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1800.0" />
			<param name="lanes" value="3.0" />
			<param name="oneway" value="true" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="motorway" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="19.44" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1500.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="true" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="motorway_link" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="19.44" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1800.0" />
			<param name="lanes" value="2.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="trunk" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="16.67" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1500.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="trunk_link" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="16.67" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1500.0" />
			<param name="lanes" value="2.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="primary" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="16.67" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1500.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="primary_link" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="11.11" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1000.0" />
			<param name="lanes" value="2.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="secondary" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="11.11" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="1000.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="secondary_link" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="8.33" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="800.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="tertiary" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="8.33" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="800.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="tertiary_link" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="8.33" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="600.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="minor" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="8.33" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="600.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="unclassified" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="8.33" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="600.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="residential" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="car,car_passenger,taxi" />
			<param name="freespeed" value="5.55" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="600.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="highway" />
			<param name="osmValue" value="living_street" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="rail" />
			<param name="freespeed" value="44.44" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="9999.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="railway" />
			<param name="osmValue" value="rail" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="rail" />
			<param name="freespeed" value="11.11" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="9999.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="true" />
			<param name="osmKey" value="railway" />
			<param name="osmValue" value="tram" />
		</parameterset>
		<parameterset type="wayDefaultParams" >
			<param name="allowedTransportModes" value="rail" />
			<param name="freespeed" value="22.22" />
			<param name="freespeedFactor" value="1.0" />
			<param name="laneCapacity" value="9999.0" />
			<param name="lanes" value="1.0" />
			<param name="oneway" value="false" />
			<param name="osmKey" value="railway" />
			<param name="osmValue" value="light_rail" />
		</parameterset>
	</module>

    </config>
    """


    with open("%s/config.xml" % context.path(), "w+") as f_write:
        f_write.write(content)

    pt2matsim.run(context, "org.matsim.pt2matsim.run.Osm2MultimodalNetwork", [
        "config.xml"
    ])

    assert(os.path.exists("%s/network.xml.gz" % context.path()))
    return "network.xml.gz"

def validate(context):
    if not os.path.exists("%s/osm/sao_paulo.osm.gz" % context.config("data_path")):
        raise RuntimeError("OSM data is not available")

    return os.path.getsize("%s/osm/sao_paulo.osm.gz" % context.config("data_path"))
