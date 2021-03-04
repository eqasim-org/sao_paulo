import shutil
import os.path

import matsim.runtime.eqasim as eqasim

def configure(context):
    context.stage("matsim.simulation.prepare")

    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

def execute(context):
    config_path = "%s/%s" % (
        context.path("matsim.simulation.prepare"),
        context.stage("matsim.simulation.prepare")
    )

    # Run routing
    eqasim.run(context, "org.eqasim.sao_paulo.RunSimulation", [
        "--config-path", config_path,
        "--config:controler.lastIteration", str(90),
        "--config:controler.writeEventsInterval", str(10),
        "--config:controler.writePlansInterval", str(10),
        "--config:strategy.strategysettings[strategyName=DiscreteModeChoice].weight", str(0.1),
        "--config:strategy.strategysettings[strategyName=KeepLastSelected].weight", str(0.9),
    ])
