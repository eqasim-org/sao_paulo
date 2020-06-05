# How to create a scenario

The following sections describe three steps of using the pipeline. To generate
the synthetic population, first all necessary data must be gathered. Afterwards,
the pipeline can be run to create a synthetic population in *CSV* and *GPKG*
format. Optionally, the pipeline can then prepare a [MATSim](https://matsim.org/)
simulation and run it in a third step:

- [Gathering the data](#section-data)
- [Running the pipeline](#section-data)
- *(Optional)* [Running the simulation](#section-simulation)

## <a name="section-data"></a>Gathering the data

To create the scenario, a couple of data sources must be collected. It is best
to start with an empty folder, e.g. `/data`. All data sets need to be named
in a specific way and put into specific sub-directories. The following paragraphs
describe this process.

### 1) Census data (Censo 2010)

Census data containing the socio-demographic information of people living in
Brasil is available at the website of Centro de Estudos da Metrópole:

- [Census data](http://centrodametropole.fflch.usp.br/pt-br/controle-acesso)
- You need to register with your email, name and institution email before
you can use the service
- Select the data under censo demographico 2010
- Download Bancos de microdados da amostra do Censo Demográfico 2010
- Copy the contents of the *zip* file into the folder `data/Census`

### 2) Sao Paulo household travel survey (OD 2017)

The Sao Paulo household travel survey is available from Transportes Metropolitanos:

- [Sao Paulo household travel survey](http://www.metro.sp.gov.br/pesquisa-od/)
- Download Banco de Dados zip file
- Put the downloaded contents of the *zip* file int othe folder `data/HTS`.

### 3) OpenStreetMap data

The OpenStreetMap data is avaialble from Geofabrik:

- Here you cna find [Sao-Paulo OSM](http://download.geofabrik.de/south-america/brazil/sudeste.html) data
- Download the sudeste-latest.osm.pbf file
- Now you need to cut-out the Sao Paulo Metropolitan region. 
This can be easily done using a tool called [osmosis](https://github.com/openstreetmap/osmosis). Download the latest build and follow
the installation instructions. You would need a polygon 
file describing the boundaries of the region, which you can find also [here](../resources) called sao_paulo.poly. 
- The following command using osmosis can be used to cut-out a Sao Paulo region:
```
osmosis --read-pbf file="sudeste-latest.osm.pbf" --bounding-polygon file="sao_paulo.poly" --write-pbf file="sao_paulo.osm.pbf"
```
- Cut-out Sao Paulo region and place sao_paulo.osm.pbf file in `data/osm`

### 4) Educational facilities

The private and public school of Sao Paulo region are available from Dados Abertos da Educação:
- [Educational facilities in Sao Paulo region](https://dados.educacao.sp.gov.br/dataset/endere%C3%A7os-de-escolas)
- Download Endereços de Escolas (set/2018) - Secretaria da Educação de São Paulo csv data
- Please note that this file has one error in line 25881, there is one comma too many. Please replace in this line 
"5,00E+91" with "500E+91" and save it. 
- Put the downlaod *csv* file in `data/escolas_enderecos.csv`.

### 5) Census zoning system

The Census zoning system is available from Centro de Estudos da Metrópole:

- [Zoning data](http://centrodametropole.fflch.usp.br/pt-br/controle-acesso)
- You need to register with your email, name and institution email before
you can use the service
- Select the data under censo demographico 2010
- Download Shapefile dos Setores Censitários 2010 RM São Paulo SC2010 CEM
- Copy the contents of the *zip* file into the folder `data/spatial`
- Additionally there are two more files based on the shapefile above that were created for now manually (
SC2010_RMSP_CEM_V3_city and SC2010_RMSP_CEM_V3_center). These represent the city of Sao Paulo and downtown 
Sao Paulo.
You can find them under resources folder. Please copy these files to `data/spatial`.

### 9) *(Optional)* Road network (OpenStreetMap)

Only in case you want to run a full simulation of the scenario (rather than
creating the synthetic population in itself), you need to use the sao-paulo osm data again:

- The file you have created in step 3 unpack to .osm (you can do that using osmosis tool):
```
osmosis --read-pbf file="sao_paulo.osm.pbf" --write-xml file="sao_paulo.osm"
```
- In order to save storage space, you should pack it to sao_paulo.osm.gz
- Put the *gz* file into the folder `data/osm`.

### 10) *(Optional)* Public transit schedule (GTFS)

Again, only if you want to run a full simulation, you need to download the
public transit schedule. It is available from two sources:

- [SPTRANS GTFS](http://transitfeeds.com/p/sptrans/1049)
- Downlaod a zip file and rename it to sptrans.zip
- Unfortuantely the second provider does not provide an open GTFS schedule and at the moment, and only
the residents of Brasil can obtain it via this [link](http://www.emtu.sp.gov.br/emtu/dados-abertos/dados-abertos-principal/gtfs.fss)
- Download the zip file, rename it to emtu.zip
- Copy the *zip* files into the folder `data/gtfs`.
Note: When working with multiple gtfs schedules you need to amke sure that they are coming
from the same period of time, or in other words, they need to have an overlapping operations
period. Therfore, if using a provided emtu.zip you would need to update the validity dates
in calendar.txt in order to overlap with sptrans calendar.txt dates
### Overview

Your folder structure should now have at least the following files:

- `data/Census/Censo.2010.brasil.amostra.10porcento.sav`
- `data/HTS/OD_2017.dbf`
- `data/osm/sao_paulo.osm.pbf`
- `data/escolas_enderecos.csv`
- `data/Spatial/SC2010_RMSP_CEM_V3.cpg`
- `data/Spatial/SC2010_RMSP_CEM_V3.shp`
- `data/Spatial/SC2010_RMSP_CEM_V3.dbf`
- `data/Spatial/SC2010_RMSP_CEM_V3.prj`
- `data/Spatial/SC2010_RMSP_CEM_V3.shx`
- `data/Spatial/SC2010_RMSP_CEM_V3_center.cpg`
- `data/Spatial/SC2010_RMSP_CEM_V3_center.shp`
- `data/Spatial/SC2010_RMSP_CEM_V3_center.dbf`
- `data/Spatial/SC2010_RMSP_CEM_V3_center.prj`
- `data/Spatial/SC2010_RMSP_CEM_V3_center.shx`
- `data/Spatial/SC2010_RMSP_CEM_V3_city.cpg`
- `data/Spatial/SC2010_RMSP_CEM_V3_city.shp`
- `data/Spatial/SC2010_RMSP_CEM_V3_city.dbf`
- `data/Spatial/SC2010_RMSP_CEM_V3_city.prj`
- `data/Spatial/SC2010_RMSP_CEM_V3_city.shx`


If you want to run the simulation, there should be also the following files:

- `data/osm/sao_paulo.osm.gz`
- `data/gtfs/emtu.zip`
- `data/gtfs/sptrans.zip`

## <a name="section-population">Running the pipeline

The pipeline code is available in [this repository](https://github.com/eqasim-org/sao_paulo).
To use the code, you have to clone the repository with `git`:

```bash
git clone https://github.com/eqasim-org/sao_paulo
```

which will create the `sao_paulo` folder containing the pipeline code. To
set up all dependencies, especially the [synpp](https://github.com/eqasim-org/synpp) package,
which is the code of the pipeline code, we recommend setting up a Python
environment using [Anaconda](https://www.anaconda.com/):

```bash
cd sao_paulo
conda env create -f environment.yml
```

This will create a new Anaconda environment with the name `sao_paulo`. (In
case you don't want to use Anaconda, we also provide a `requirements.txt` to
install all dependencies in a `virtualenv` using `pip install -r requirements.txt`).

To activate the environment, run:

```bash
conda activate sao_paulo
```

Now have a look at `config.yml` which is the configuration of the pipeline.
Check out [synpp](https://github.com/eqasim-org/synpp) to get a more general
understanding of what it does. For the moment, it is important to adjust
two configuration values inside of `config.yml`:

- `working_directory`: This should be an *existing* (ideally empty) folder where
the pipeline will put temporary and cached files during runtime.
- `data_path`: This should be the path to the folder where you were collecting
and arranging all the raw data sets as described above.
- `output_path`: This should be the path to the folder where the output data
of the pipeline should be stored. It must exist and should ideally be empty
for now.

To set up the working/output directory, create, for instance, a `cache` and a
`output` directory. These are already configured in `config.yml`:

```bash
mkdir cache
mkdir output
```

Everything is set now to run the pipeline. The way `config.yml` is configured
it will create the relevant output files in the `output` folder.

To run the pipeline, call the [synpp](https://github.com/eqasim-org/synpp) runner:

```bash
python3 -m synpp
```

It will automatically detect the `config.yml`, process all the pipeline code
and eventually create the synthetic population. You should see a couple of
stages running one after another. Most notably, first, the pipeline will read all
the raw data sets to filter them and put them into the correct internal formats.

After running, you should be able to see a couple of files in the `output`
folder:

- `meta.json` contains some meta data, e.g. with which random seed or sampling
rate the population was created and when.
- `persons.csv` and `households.csv` contain all persons and households in the
population with their respective sociodemographic attributes.
- `activities.csv` and `trips.csv` contain all activities and trips in the
daily mobility patterns of these people including attributes on the purposes
of activities or transport modes for the trips.
- `activities.gpkg` and `trips.gpkg` represent the same trips and
activities, but in the spatial *GPKG* format. Activities contain point
geometries to indicate where they happen and the trips file contains line
geometries to indicate origin and destination of each trip.

## <a name="section-simulation">Running the simulation

The pipeline can be used to generate a full runnable [MATSim](https://matsim.org/)
scenario and run it for a couple of iterations to test it. For that, you need
to make sure that the following tools are installed on your system (you can just
try to run the pipeline, it will complain if this is not the case):

- **Java** needs to be installed, with a minimum version of Java 8. In case
you are not sure, you can download the open [AdoptJDK](https://adoptopenjdk.net/).
- **Maven** needs to be installed to build the necessary Java packages for setting
up the scenario (such as pt2matsim) and running the simulation. Maven can be
downloaded [here](https://maven.apache.org/) if it does not already exist on
your system.
- **git** is used to clone the repositories containing the simulation code. In
case you clone the pipeline repository previously, you should be all set.

Then, open again `config.yml` and uncomment the `matsim.output` stage in the
`run` section. If you call `python3 -m synpp` again, the pipeline will know
already which stages have been running before, so it will only run additional
stages that are needed to set up and test the simulation.

After running, you should find the MATSim scenario files in the `output`
folder:

- `sao_paulo_population.xml.gz` containing the agents and their daily plans.
- `sao_paulo_facilities.xml.gz` containing all businesses, services, etc.
- `sao_paulo_network.xml.gz` containing the road and transit network
- `sao_paulo_households.xml.gz` containing additional household information
- `sao_paulo_transit_schedule.xml.gz` and `ile_de_france_transit_vehicles.xml.gz` containing public transport data
- `sao_paulo_config.xml` containing the MATSim configuration values
- `sao_paulo-1.0.5.jar` containing a fully packaged version of the simulation code including MATSim and all other dependencies

If you want to run the simulation again (in the pipeline it is only run for
two iterations to test that everything works), you can now call the following:

```bash
java -Xmx14G -cp sao_paulo-1.0.5.jar org.eqasim.sao_paulo.RunSimulation --config-path sao_paulo_config.xml
```

This will create a `simulation_output` folder (as defined in the `sao_paulo_config.xml`)
where all simulation is written.
