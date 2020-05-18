import requests
from tqdm import tqdm
import subprocess as sp
import os.path

def configure(context, require):
    require.stage("utils.java")

def execute(context):
    java = context.stage("utils.java")

    sp.check_call([
        "git", "clone", "https://github.com/eqasim-org/eqasim-java.git"
    ], cwd = context.cache_path)

    sp.check_call([
        "git", "checkout", "develop"
    ], cwd = "%s/eqasim-java" % context.cache_path)

    sp.check_call([
        "mvn", "-Pstandalone", "package"
    ], cwd = "%s/eqasim-java" % context.cache_path)

    jar = "%s/eqasim-java/sao_paulo/target/sao_paulo-1.0.5.jar" % context.cache_path

    return jar
