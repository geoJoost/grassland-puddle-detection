# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:47:22 2023

@author: Marnic Baars & Ageeth de Haan
"""
import geopandas as gpd
import pandas as pd
import os

#%% Functions
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
    import geopandas as gpd
    ANLB = gpd.read_file(filepath).to_crs(32631)
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
    import geopandas as gpd
    import pandas as pd
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

#%% Define filepaths

#Input filepaths
brp_parcels_fp = "D:/RGIC23GR10/data/Shapes/gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp" # BRP parcels
anlb_parcel_filepaths = "D:/RGIC23GR10/data/Shapes/ANLB_2021.shp" # ANLB parcels

#Intermediate filepaths
filtered_anlb_fp = "D:/RGIC23GR10/data/01_ANLB_filtered.shp" # ANLB parcels filtered for subsidy packages 3a-b-c-d
grassland_brp_fp = "D:/RGIC23GR10/data/01_brp_grasslands.shp" # BRP parcels filtered for grasslands

#Output filepaths
joined_parcel_fp = "D:/RGIC23GR10/output/01_subsidised_field.shp" #not sure if used
brp_grass_sample_fp ="D:/RGIC23GR10/output/01_brp_grassland_sample_200.shp" # 200 BRP grassland parcels which exclude the ANLB parcels
validation_parcel_fp = "D:/RGIC23GR10/output/01_anlb_drygrass_merged.shp" # ANLB parcels merged with BRP grass only parcels for validation raster clip

#%% Filter brp to graslands and write to file
brp_parcels_gdf = gpd.read_file(brp_parcels_fp).to_crs(32631)
grasland_brp_parcels = brp_parcels_gdf[brp_parcels_gdf['cat_gewasc'] == 'Grasland']
if not os.path.exists(grassland_brp_fp):
    grasland_brp_parcels.to_file(grassland_brp_fp)
    print(f"{grassland_brp_fp} written to file.")
else:
    print (f"{grassland_brp_fp} already exists.")


# Filter ANLB parcels to plasdras subsidy packages
if os.path.exists(filtered_anlb_fp):
    print(f"{filtered_anlb_fp} exists")
else: 
    filepath_ANLB = anlb_parcel_filepaths
    code_list_ANLB = ['3a','3b','3c','3d']
    # filter ANLB data and safe it as a shapefile
    ANLB=filterANLB(filepath_ANLB,code_list_ANLB)
    ANLB.to_file(filtered_anlb_fp)
    ANLB = gpd.read_file(filtered_anlb_fp)

# # join BRP and ANLB data and save it as a shapefile
# if os.path.exists(joined_parcel_fp):
#     print(f"{joined_parcel_fp} exists")
#     subsidised = gpd.read_file(joined_parcel_fp).to_crs(32631)
# else:
#     BRP = gpd.read_file(grassland_brp_fp)
#     subsidised_field = joindataframes(ANLB,BRP)
#     subsidised_field.to_file(joined_parcel_fp)

#%% Create dataset containing only dry grass polygons
# Load in the ANLB-subsidy parcels and BRP grassland parcels
anlb_gdf = gpd.read_file(filtered_anlb_fp).to_crs(32631)
brp_gdf = gpd.read_file(grassland_brp_fp).to_crs(32631)

brp_large_parcels = brp_gdf[brp_gdf['area'] >= 30000] # Filter for parcels that are larger or equal to 30000 square meters

# Clipping
if os.path.exists(brp_grass_sample_fp):
    print("BRP sampled dataset already exists")
    gdf_brp_clip = gpd.read_file(brp_grass_sample_fp)
else:
    print("BRP sampled dataset does not exist yet")

    # Randomly select 70,000 (about 10% of original sample, N=511,031) polygons from the BRP data
    gdf_brp_sample = brp_large_parcels.sample(n=200, random_state=1)

    # Conduct a reverse clip to make sure both vector files do not overlap
    gdf_brp_clip = gpd.overlay(gdf_brp_sample, anlb_gdf, how='difference')
    
    # Export the BRP sampled dataset to file
    gdf_brp_clip.to_file(brp_grass_sample_fp)
    
    print("BRP sampled dataset created \n")
    

# Merge ANLB and grass sample shapefiles
# Get gdfs 

dataframesList = [gdf_brp_clip, anlb_gdf]

### Create validation shapefiles per date
# Merge/Combine multiple shapefiles into one
rdf = gpd.GeoDataFrame(pd.concat(dataframesList, ignore_index=True), crs=dataframesList[0].crs)
 
#Export merged geodataframe into shapefile
rdf.to_file(validation_parcel_fp)
