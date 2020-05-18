import shutil
import os.path
def configure(context, require):
    require.stage("matsim.run")
    require.stage("utils.java")


def execute(context):
    java = context.stage("utils.java")

    scenario_path = context.stage("matsim.run")
    java(
        context.stage("matsim.java.eqasim"),
        "org.eqasim.sao_paulo.RunSimulation", [
        "--config-path", "%s/sao_paulo_config.xml" % scenario_path,
        "--config:controler.outputDirectory", "/nas/balacm/Airbus/SF/Sebastian/V1.0/sao_paulo/sao_paulo_synpop/cache_1pct_sp_52/matsim.calibration/sim_9",        
        "--config:controler.lastIteration", str(30),
        "--config:controler.writeEventsInterval", str(10),
        "--config:controler.writePlansInterval", str(10),
        "--mode-parameter:walk.alpha_u", str(1.5),
        "--mode-parameter:pt.alpha_u", str(-0.1),
        "--mode-parameter:pt.betaInVehicleTime_u_min", str(-0.0142),
        "--mode-parameter:spPT.alpha_age", str(0.0),
        "--mode-parameter:spTaxi.alpha_u", str(-1.6),
        "--mode-parameter:spTaxi.beta_TravelTime_u_min", str(-0.0),
        "--cost-parameter:taxiPickUpFee_BRL", str(2.16),
        "--cost-parameter:taxiCostPerMin_BRL", str(0.24),
        "--cost-parameter:taxiCostPerkm_BRL", str(1.2),
        "--cost-parameter:ptCostPerTrip_0Transfers_BRL", str(3.6),
        "--config:eqasim.crossingPenalty", str(4.0),
        "--config:transitRouter.searchRadius", str(1300.0),
        "--config:transitRouter.directWalkFactor", str(100.0),
        "--config:transitRouter.maxBeelineWalkConnectionDistance", str(400.0),
        "--cost-parameter:carCost_BRL_km", str(0.35),        
        "--config:strategy.strategysettings[strategyName=DiscreteModeChoice].weight", str(0.1),
        "--config:strategy.strategysettings[strategyName=KeepLastSelected].weight", str(0.9)
    ], cwd = context.cache_path)