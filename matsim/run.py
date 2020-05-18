import shutil
import os.path

def configure(context, require):
    require.stage("matsim.population")
    require.stage("matsim.households")
    require.stage("matsim.facilities")
    require.stage("matsim.java.eqasim")
    require.stage("matsim.secondary_locations")
    require.stage("utils.java")
    require.stage("matsim.network.mapped")

def execute(context):
    # Some files we just copy
    transit_schedule_path = context.stage("matsim.network.mapped")["schedule"]
    shutil.copyfile(transit_schedule_path, "%s/sao_paulo_transit_schedule.xml.gz" % context.cache_path)

    transit_vehicles_path = context.stage("matsim.network.mapped")["vehicles"]
    shutil.copyfile(transit_vehicles_path, "%s/sao_paulo_transit_vehicles.xml.gz" % context.cache_path)

    households_path = context.stage("matsim.households")
    shutil.copyfile(households_path, "%s/sao_paulo_households.xml.gz" % context.cache_path)

    # Some files we send through the preparation script
    network_input_path = context.stage("matsim.network.mapped")["network"]
    network_fixed_path = "%s/sao_paulo_fixed_network.xml.gz" % context.cache_path
    network_output_path = "%s/sao_paulo_network.xml.gz" % context.cache_path

    facilities_input_path = context.stage("matsim.facilities")
    facilities_output_path = "%s/sao_paulo_facilities.xml.gz" % context.cache_path

    population_input_path = context.stage("matsim.secondary_locations")
    population_prepared_path = "%s/prepared_population.xml.gz" % context.cache_path
    population_output_path = "%s/sao_paulo_population.xml.gz" % context.cache_path

    config_output_path = "%s/sao_paulo_config.xml" % context.cache_path

    # Call preparation script
    java = context.stage("utils.java")
    
    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.sao_paulo.scenario.RunNetworkFixer", [
        "--input-path", network_input_path,
        "--output-path", network_fixed_path
    ], cwd = context.cache_path)

    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.core.scenario.preparation.RunPreparation", [
        "--input-facilities-path", facilities_input_path,
        "--output-facilities-path", facilities_output_path,
        "--input-population-path", population_input_path,
        "--output-population-path", population_prepared_path,
        "--input-network-path", network_fixed_path,
        "--output-network-path", network_output_path,
        "--threads", str(context.config["threads"])
    ], cwd = context.cache_path)

    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.core.scenario.config.RunGenerateConfig", [
        "--output-path", config_output_path,
        "--prefix", "sao_paulo_",
        "--sample-size", str(context.config["input_downsampling"]),
        "--random-seed", str(0),
        "--threads", str(context.config["threads"])
    ], cwd = context.cache_path)

    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.sao_paulo.scenario.RunAdaptConfig", [
        "--input-path", config_output_path,
        "--output-path", config_output_path
    ], cwd = context.cache_path)
    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.core.scenario.routing.RunPopulationRouting", [
        "--config-path", config_output_path,
        "--output-path", population_output_path,
        "--threads", str(context.config["threads"]),
        "--config:plans.inputPlansFile", population_prepared_path
    ], cwd = context.cache_path)

    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.core.scenario.validation.RunScenarioValidator", [
        "--config-path", config_output_path
    ], cwd = context.cache_path)

    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.sao_paulo.RunSimulation", [
        "--config-path", config_output_path,
        "--config:controler.lastIteration", str(30),
        "--config:controler.writeEventsInterval", str(10),
        "--config:controler.writePlansInterval", str(10),
        "--mode-parameter:walk.alpha_u", str(2.0),
        "--mode-parameter:pt.alpha_u", str(-0.2),
        "--mode-parameter:pt.betaInVehicleTime_u_min", str(-0.0142),
        "--mode-parameter:spPT.alpha_age", str(0.0),
        "--mode-parameter:spTaxi.alpha_u", str(-3.0),
        "--mode-parameter:spTaxi.beta_TravelTime_u_min", str(-0.25),
        "--cost-parameter:taxiPickUpFee_BRL", str(3.44),
        "--cost-parameter:taxiCostPerMin_BRL", str(0.35),
        "--cost-parameter:taxiCostPerkm_BRL", str(1.66),
        "--cost-parameter:ptCostPerTrip_0Transfers_BRL", str(3.6),
        "--config:eqasim.crossingPenalty", str(8.0),
        "--config:transitRouter.searchRadius", str(1300.0),
        "--config:transitRouter.directWalkFactor", str(100.0),
        "--config:transitRouter.maxBeelineWalkConnectionDistance", str(400.0),
        "--cost-parameter:carCost_BRL_km", str(0.51),        
        "--config:strategy.strategysettings[strategyName=DiscreteModeChoice].weight", str(0.1),
        "--config:strategy.strategysettings[strategyName=KeepLastSelected].weight", str(0.9)
    ], cwd = context.cache_path)

    return context.cache_path