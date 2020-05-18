import osmium as osm
import pandas as pd
import subprocess as sp
import os.path
import shapely.wkb as wkblib
wkbfab = osm.geom.WKBFactory()

def configure(context, require):
    pass
    
    
class OSMHandler(osm.SimpleHandler):
    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.osm_data = []

    def tag_inventory(self, elem, elem_type):
        for tag in elem.tags:
            self.osm_data.append([elem_type, 
                                   elem.id,                                   
                                   tag.k, 
                                   tag.v])

    def way(self, w):
        try:
            wkb = wkbfab.create_linestring(w)
            line = wkblib.loads(wkb, hex=True)
            for tag in w.tags:        	
                self.osm_data.append(['way', 
                                   w.id,                                   
                                   tag.k, 
                                   tag.v, line.centroid.x, line.centroid.y])
        except Exception:
            pass

def execute(context):

    osmhandler = OSMHandler()
    # scan the input file and fills the handler list accordingly
    osmhandler.apply_file("/nas/balacm/Airbus/SF/Sebastian/V1.0/sao_paulo/Data_SP/Data_SP/osm/sao_paulo.osm.pbf", locations=True)

    # transform the list into a pandas DataFrame
    data_colnames = ['type', 'id', 'tagkey', 'tagvalue', 'x', 'y']
    df_osm = pd.DataFrame(osmhandler.osm_data, columns=data_colnames)
    df_osm = df_osm[df_osm['type']=='way']
    df_osm = df_osm[df_osm['tagkey']=='highway']
    df_osm = df_osm[df_osm['tagvalue']=='residential']
    return df_osm
    