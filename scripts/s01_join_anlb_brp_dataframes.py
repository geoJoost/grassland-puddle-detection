# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:47:22 2023

@author: Marnic Baars & Ageeth de Haan
"""
import geopandas as gpd
import pandas as pd
import os

def filterANLB(filepath, code_list):
    """
    Function that filters the ANLB data based on the subsidy code

    Parameters
    ----------
    filepath : path to the ANLB_2021.shp
    code_list : subsidy code (can be found in the Readme.txt)

    Returns
    -------
    ANLB : filtered ANLB data

    """
    ANLB = gpd.read_file(filepath)
    # select plasdras areas
    ANLB = ANLB[ANLB["CODE_BEHEE"].isin(code_list)]
    return ANLB

### join BRP and ANLB data ################################################
def joindataframes(df1, df2):
    """
    Function that spatial joins two geopandas dataframes. It calculates the centroid of
    of df1 and joins df2 if the centroid intersects with the geometry of df2 while
    preserving the geometry of df1 (instead of the centroid geometry). The function adds a column
    and indicates "yes" when there was a join.

    Parameters
    ----------
    df1 : geopandas dataframe
    df2 : geopandas dataframe

    Returns
    -------
    df1_df2 : joined geopandas dataframe

    """
    df1["Centroid"] = df1.centroid
    df_centroid = gpd.GeoDataFrame(df1, geometry= df1["Centroid"])
    df_centroid["polygon"] = df1.geometry
    df_centroid_dropped = df_centroid.drop(['Centroid'], axis=1)
    df_join = gpd.sjoin(df_centroid_dropped, df2, how='left')
    df1_df2 = gpd.GeoDataFrame(df_join, geometry= df_join["polygon"])
    df1_df2 = df1_df2.drop(["polygon"], axis=1)
    df1_df2["Parcel_found"] = "yes"
    df1_df2["Parcel_found"] = df1_df2["fieldid"].apply(lambda x: 'yes' if pd.notnull(x) else 'no')
    return df1_df2

### ANLB data #######################################################
# Due to time reasons, first check if the file already exist
# Define filepaths
# Define individual directories
data_dir = "data/"
output_dir = "output/"

fp_anlb_input = os.path.join(data_dir, "Shapes/ANLB_2021.shp")
fp_anlb_filtered = os.path.join(output_dir, "01_ANLB_filtered.shp")

fp_brp_input = os.path.join(data_dir, "Shapes/gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp")
fp_brp_output = os.path.join(output_dir, "01_subsidised_field.shp")

# Create a filtered version of the ANLB data
if os.path.exists(fp_anlb_filtered):
    print(f"'{fp_anlb_filtered}' already exists")
    df_anlb = gpd.read_file(fp_anlb_filtered)

else:
    print(f"'{fp_anlb_filtered}' does not exist yet")
    # Subsidy codes correspond to 'plas-dras' subsidy
    code_list_anlb = ['3a','3b','3c','3d'] 
    
    # filter ANLB data
    df_anlb = filterANLB(fp_anlb_input, code_list_anlb)
    
    # and save
    df_anlb.to_file(fp_anlb_filtered)
    #ANLB = gpd.read_file("data/01_ANLB_filtered.shp")

# Join BRP and ANLB data and save it as a shapefile
if os.path.exists(fp_brp_output):
    print(f"'{fp_brp_output}' already exists")

else:
    print(f"'{fp_brp_output}' does not exist yet")
    gdf_brp = gpd.read_file(fp_brp_input)
    subsidised_field = joindataframes(df_anlb, gdf_brp)
    subsidised_field.to_file(fp_brp_output)

"""
if os.path.exists("data/01_ANLB_filtered.shp"):
    print("01_ANLB_filtered.shp exists")
    
else: 
    filepath_ANLB = "input/Shapes/ANLB_2021.shp"
    code_list_ANLB = ['3a','3b','3c','3d']
    
    # filter ANLB data and safe it as a shapefile
    ANLB = filterANLB(filepath_ANLB, code_list_ANLB)
    ANLB.to_file("data/01_ANLB_filtered.shp")
    #ANLB = gpd.read_file("data/01_ANLB_filtered.shp")

# join BRP and ANLB data and save it as a shapefile
if os.path.exists("output/01_subsidised_field.shp"):
    print("output/01_subsidised_field.shp exists")
    subsidised = gpd.read_file("output/01_subsidised_field.shp")
    
else:
    BRP = gpd.read_file("input/Shapes/gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp")
    subsidised_field = joindataframes(ANLB,BRP)
    subsidised_field.to_file("output/01_subsidised_field.shp")
    """




