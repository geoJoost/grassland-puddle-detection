# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:47:22 2023

@author: Marnic Baars & Ageeth de Haan
"""
import geopandas as gpd

### BRP data ##############################################################
# just for easy filling in the function
filepath_BRP = "data/Shapes/gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp"
province_BRP = "Friesland"

def filterBRP(filepath, province, buffer_centroid= "buffer"):
    import geopandas as gpd
    BRP = gpd.read_file(filepath_BRP)
    # select Friesland
    BRP_province_selection=BRP["provincie"]==province
    BRP=BRP[BRP_province_selection]
    # select buffered zones
    BRP_buffercentroid_selection=BRP["orig_20m"]==buffer_centroid
    BRP=BRP[BRP_buffercentroid_selection]  
    return BRP

# filter BRP data and safe it as a shapefile
BRP = filterBRP(filepath_BRP,province_BRP)
BRP.to_file("output/01_BRP_filtered.shp")


### ANLB data #############################################################
# just for easy filling in the function
filepath_ANLB = "data/Shapes/ANLB_2021.shp"
code_list_ANLB = ['3a','3b','3c','3d']
Friesland = gpd.read_file("data/Shapes/Friesland_area.shp")

def filterANLB(filepath, code_list, province):
    import geopandas as gpd
    ANLB = gpd.read_file(filepath)
    ANLB = ANLB.clip(province)
    # select plasdras areas
    ANLB = ANLB[ANLB["CODE_BEHEE"].isin(code_list)]
    return ANLB

# filter ANLB data and safe it as a shapefile
ANLB=filterANLB(filepath_ANLB,code_list_ANLB, Friesland)
ANLB.to_file("output/01_ANLB_filtered.shp")

BRP = gpd.read_file("output/01_BRP_filtered.shp")
ANLB = gpd.read_file("output/01_ANLB_filtered.shp")

### join BRP and ANLB data ################################################
def joindataframes(df1, df2):
# right gives point data, left gives all available parcels, inner gives some areas which are inundated
# tested using       subsidised_field = joindataframes(BRP,ANLB)
    import geopandas as gpd
    df2["Centroid"] = df1.centroid
    df2 = gpd.GeoDataFrame(df2, geometry= df2["Centroid"])
    df2_dropped = df2.drop(['Centroid'], axis=1)
#     code not completely working due to some holes in the BRP data
#     code below takes all fields within the max distance of the centroid of
#     subsidised areas
#     ANLB_BRP = gpd.sjoin_nearest(df1, df2_dropped,max_distance=10)
    ANLB_BRP = gpd.sjoin(df1, df2_dropped, how='right')
    return ANLB_BRP

### join BRP and ANLB data ################################################
# only working when using right (left and inner does not give any visualisation results)
# does not give the parcels, but the areas which are inundated
# tested using       subsidised_field = joindataframes(BRP,ANLB)
#def joindataframes(df1, df2):
#    import geopandas as gpd
#    df1["Centroid"] = df1.centroid
#    df1 = gpd.GeoDataFrame(df1, geometry= df1["Centroid"])
#    df1_dropped = df1.drop(['Centroid'], axis=1)
#     code not completely working due to some holes in the BRP data
#     code below takes all fields within the max distance of the centroid of
#     subsidised areas
#     ANLB_BRP = gpd.sjoin_nearest(df1, df2_dropped,max_distance=10)
#    ANLB_BRP = gpd.sjoin(df1_dropped, df2, how='right')
#    return ANLB_BRP


# join BRP and ANLB data and safe it as a shapefile
subsidised_field = joindataframes(ANLB,BRP)
subsidised_field.to_file("output/01_subsidised_field.shp")


