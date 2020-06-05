import shutil

def configure(context):
    context.stage("matsim.simulation.run")
    context.stage("matsim.simulation.prepare")
    context.stage("matsim.runtime.eqasim")

    context.config("output_path")

def execute(context):
    config_path = "%s/%s" % (
        context.path("matsim.simulation.prepare"),
        context.stage("matsim.simulation.prepare")
    )

    for name in [
        "sao_paulo_households.xml.gz",
        "sao_paulo_population.xml.gz",
        "sao_paulo_facilities.xml.gz",
        "sao_paulo_network.xml.gz",
        "sao_paulo_transit_schedule.xml.gz",
        "sao_paulo_transit_vehicles.xml.gz",
        "sao_paulo_config.xml"
    ]:
        shutil.copy(
            "%s/%s" % (context.path("matsim.simulation.prepare"), name),
            "%s/%s" % (context.config("output_path"), name)
        )

    shutil.copy(
        "%s/%s" % (context.path("matsim.runtime.eqasim"), context.stage("matsim.runtime.eqasim")),
        context.config("output_path")
    )
