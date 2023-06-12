# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:47:22 2023

@author: marni
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
BRP.to_file("data/Shapes/BRP_filtered.shp")


### ANLB data #############################################################
# just for easy filling in the function
filepath_ANLB = "data/Shapes/ANLB_2021.shp"
code_list_ANLB = ['3a','3b','3c','3d']
def filterANLB(filepath, code_list):
    import geopandas as gpd
    ANLB = gpd.read_file(filepath)
    # select plasdras areas
    ANLB = ANLB[ANLB["CODE_BEHEE"].isin(code_list)]
    return ANLB

# filter ANLB data and safe it as a shapefile
ANLB=filterANLB(filepath_ANLB,code_list_ANLB)
ANLB.to_file("data/Shapes/ANLB_filtered.shp")

ANLB = gpd.read_file("data/Shapes/ANLB_filtered.shp")

### join BRP and ANLB data ################################################
def joindataframes(df1, df2):
    import geopandas as gpd
    df1["Centroid"] = df1.centroid
    df1 = gpd.GeoDataFrame(df1, geometry= df1["Centroid"])
    #ANLB_BRP = gpd.sjoin(BRP, ANLB)
    return df1
join2 = joindataframes(ANLB, BRP)
    

