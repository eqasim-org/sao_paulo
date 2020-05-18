import requests
from tqdm import tqdm
import subprocess as sp
import os.path

def configure(context, require):
    require.stage("utils.java")

def execute(context):
    java = context.stage("utils.java")

    os.mkdir("%s/__java_tmp" % context.cache_path)

    sp.check_call([
        "git", "clone", "https://github.com/matsim-org/pt2matsim.git"
    ], cwd = context.cache_path)

    sp.check_call([
        "git", "checkout", "master"
    ], cwd = "%s/pt2matsim" % context.cache_path)

    sp.check_call([
        "mvn", "-Djava.io.tmpdir=%s/__java_tmp" % context.cache_path, "package"
    ], cwd = "%s/pt2matsim" % context.cache_path)

    jar = "%s/pt2matsim/target/pt2matsim-19.11-shaded.jar" % context.cache_path
    java(jar, "org.matsim.pt2matsim.run.CreateDefaultOsmConfig", ["test_config.xml"], cwd = context.cache_path)

    assert(os.path.exists("%s/test_config.xml" % context.cache_path))

    return jar
