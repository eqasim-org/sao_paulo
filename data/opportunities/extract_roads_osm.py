import osmium as osm
import pandas as pd
import subprocess as sp
import os.path
import shapely.wkb as wkblib
wkbfab = osm.geom.WKBFactory()

def configure(context):
    context.config("data_path")    
    context.config("osm_file")
    
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
    def node(self, w):
        try:
            for tag in w.tags:
                if ((tag.k=='public_transport') | (tag.k=='amenity')):
                    self.osm_data.append(['node', 
                                   w.id,                                   
                                   tag.k, 
                                   tag.v, w.location.lon, w.location.lat])
        except Exception:
            pass

def execute(context):

    osmhandler = OSMHandler()
    # scan the input file and fills the handler list accordingly
    osmhandler.apply_file("%s/osm/%s" % (context.config("data_path"), context.config("osm_file")), locations=True)

    # transform the list into a pandas DataFrame
    data_colnames = ['type', 'id', 'tagkey', 'tagvalue', 'x', 'y']
    df_osm = pd.DataFrame(osmhandler.osm_data, columns=data_colnames)
    
    amenity_shop = ['pharmacy', 'convenience_store', 'commercial', 'marketplace', 'winery', 'food_court',
                 'convenience']
    amenity_leisure = ['social_facility',
       'theatre', 'swimming_pool',
       'place_of_worship', 'library', 'science_park', 'social_centre',
       'arts_centre', 'community_centre', 'restaurant', 'events_centre', 'pub', 'cafe',
       'commercial', 'cinema', 'winery', 'bar', 'amphitheatre', 'concert_hall', 'studio', 'nightclub', 'food_court',
       'bbq', 'music_venue', 'senior_center', 'pool', 'casino',
       'events_venue', 'spa', 'boat_rental',
       'senior_centre',
       'music_venue;bar', 'community_center', 'ice_cream','church', 'park', 'stripclub', 'swingerclub',
       'biergarten',
       'music_rehearsal_place', 'cafeteria', 'meditation_centre', 'gym',
       'planetarium', 'clubhouse', 'dive_centre', 'community_hall',
       'event_hall', 'bicycle_rental', 'club', 'gambling']
    amenity_work = ['school',
       'bank', 'hospital', 'social_facility', 'police', 'pharmacy',
       'theatre', 'university', 'college', 'swimming_pool',
       'place_of_worship', 'library', 'clinic', 'science_park',
       'conference_centre', 'trailer_park', 'social_centre',
       'arts_centre', 'courthouse', 'post_office', 'community_centre',
       'car_rental', 'restaurant', 'ranger_station',
       'events_centre', 'convenience_store', 'townhall', 'mortuary',
       'fuel', 'car_wash', 'fast_food', 'pub', 'fire_station', 'cafe',
       'doctors', 'commercial', 'nursing_home', 'marketplace', 'cinema',
       'public_building', 'winery',
       'dentist', 'bar', 'amphitheatre', 'ferry_terminal',
       'concert_hall', 'studio', 'nightclub', 'kindergarten',
       'civic', 'food_court', 'childcare', 'prison',
       'caravan_rental', 'monastery', 'dialysis', 'veterinary',
       'music_venue', 'senior_center', 'pool', 'casino',
       'events_venue', 'preschool',
       'animal_shelter', 'spa', 'boat_rental',
       'senior_centre', 'brokerage', 'vehicle_inspection', 'healthcare',
       'music_venue;bar', 'community_center', 'embassy', 'ice_cream',
       'tailor', 'coworking_space', 'church',
       'storage_rental', 'stripclub', 'swingerclub',
       'office', 'biergarten',
       'music_rehearsal_place', 'cafeteria', 'truck_rental',
       'sperm_bank', 'meditation_centre',
       'funeral_parlor', 'cruise_terminal',
       'crematorium', 'gym',
       'planetarium', 'clubhouse', 
       'language_school', 'convenience', 'music_school', 'dive_centre',
       'community_hall',
       'event_hall', 'research_institute',
       'club',  'gambling',
       'retirement_village']
       
       
    building_work = ['hotel', 'tower', 'police_station',
       'retail', 'shop', 'arena', 'transportation',
       'office', 'commercial', 'hangar', 'industrial',
       'terminal', 'mall', 'warehouse', 'multi_level_parking',
       'university', 'dormitory', 'museum', 'theatre',
       'stadium', 'fire_station', 'control_tower',
       'manufacture', 'sports_centre', 'hospital', 'train_station',
       'civic', 'church', 
       'gymnasium', 'temple', 'mixed_use',
       'central_office', 'amphitheatre',
       'Business', 'barn', 'data_center', 'cinema',
       'service', 'supermarket',  'weapon_armory',
       'cathedral', 'farm_auxiliary', 'factory',
       'station', 'library', 'farm', 'mosque','stable', 'historic_building',
       'carousel', 'synagogue', 'convent',
       'mortuary',
       'prison', 
       'brewery', 'Office',
       'monastery', 'clinic', 'kiosk', 'carpark', 'mixed', 'mixd_use',
       'motel', 'community_center', 'research', 'charity', 'medical', 'offices', 'community_centre',
       'synogogue', 'Athletic_field_house', 'depot', 'Laundry', 'chapel',
       'lighthouse',
       'clubhouse', 'guardhouse', 'bungalow', 'retails', 'tech_cab',
       'commerical', 'gasstation', 'yes;offices', 'castle']   
    shops =["retails", "apartments;commerical", "mixd_use", "mixed", "kiosk", "supermarket", "mixed_use", "mall", "commercial",
        "shop", "retail"]
        
    df_facilities = df_osm[(df_osm["tagkey"]=='building') & (df_osm["tagvalue"].isin(shops))]
    df_facilities["purpose"] = "shop work"
    df_shop = df_osm[(df_osm["tagkey"]=='amenity') & (df_osm["tagvalue"].isin(amenity_shop))]
    df_shop["purpose"] = "shop work"
    df_facilities = pd.concat([df_facilities, df_shop])
    
    df_leisure = df_osm[(df_osm["tagkey"]=='amenity') & (df_osm["tagvalue"].isin(amenity_leisure))]
    df_leisure["purpose"] = "leisure work"    
    df_facilities = pd.concat([df_facilities, df_leisure])
    df_work = df_osm[(df_osm["tagkey"]=='amenity') & (df_osm["tagvalue"].isin(amenity_work))]
    df_work["purpose"] = "work"    
    df_facilities = pd.concat([df_facilities, df_work])
    
    df_work = df_osm[(df_osm["tagkey"]=='building') & (df_osm["tagvalue"].isin(building_work))]
    df_work["purpose"] = "work"    
    df_facilities = pd.concat([df_facilities, df_work])
    
    df_home = df_osm[df_osm['type']=='way']
    df_home = df_home[df_home['tagkey']=='highway']
    df_home = df_home[(df_home['tagvalue']=='residential') | (df_home['tagvalue']=='living_street')]
    df_home["purpose"] = "home"
    df_facilities = pd.concat([df_facilities, df_home])
    
    df_facilities.to_csv("%s/osm/facilities.csv" % context.config("data_path"))
    #df_osm = df_osm[df_osm['type']=='way']
    #df_osm = df_osm[df_osm['tagkey']=='highway']
    #df_osm = df_osm[df_osm['tagvalue']=='residential']
    return df_facilities
    
