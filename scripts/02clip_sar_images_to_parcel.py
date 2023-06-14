# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:08:02 2023

@author: petra
"""

import os
import pandas as pd
import shutil
from osgeo import gdal

import geopandas as gpd
import fiona
import rasterio
import rasterio.mask


base = "D:\\RGIC23GR10\\"
data_folder = base + "data\\"
output_folder = base + "output\\"
#%% Compress all .tif images provided in separate date subdirectories and store all outputs in same file
# define source and output directories

src_dir = data_folder + "S1A\\" # This directory should have the same structure as the orignial S1 folder (i.e., contain subfolders with dates). Subdirectories should only contain the VV backscatter tif file.
compressed_img_location = data_folder + "S1Acomp3\\"

# create the output directory if it does not exist
os.makedirs(compressed_img_location, exist_ok=True)

infn = "D:\RGIC23GR10\S1A\20210104\Sigma0_dB_VV_20210104.tif"
outfn = output_folder + "Sigma0_dB_VV_20210104_compressed.tif"
ds = gdal.Translate(outfn, infn, creationOptions=["COMPRESS=LZW", "TILED=YES"])
ds = None

#%% Filter images by central pass dates and time

#Get list with the central pass dates and filter for january-august
s1_pass_info_fp = "D:\RGIC23GR10\S1A\Sentinel_1A_2021_overview.csv"
s1_pass_info_df = pd.read_csv(s1_pass_info_fp)
s1_central_pass_dates = s1_pass_info_df.loc[s1_pass_info_df['Overpass'] == 'central', 'Date'].tolist() # filter for central pass
s1_cp_jan_aug = [date for date in s1_central_pass_dates if date <= 20210820] # filter for january-august

filtered_image_location = data_folder + "S1_VV_filtered\\"
source_folder = compressed_img_location
destination_folder = filtered_image_location


dates = s1_cp_jan_aug

# Copy the images corresponding to filtered dates
# Create the destination folder if it does not exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

for date in dates:
    # Construct the filename based on the date
    filename = f"Sigma0_dB_VV_{date}_compressed.tif"
    
    # Check if the file exists in the source folder
    file_path = os.path.join(source_folder, filename)
    if os.path.isfile(file_path):
        # Copy the file to the destination folder
        shutil.copy(file_path, destination_folder)
        
#%% Filter parcel data to exclude Zeeland and clip SAR images
parcel_shapefiles = data_folder + "Shapes\gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp"

# Load in all datasets
parcel_gdf = gpd.read_file(parcel_shapefiles).to_crs(32631)

# Filter parcels to exclude Zeeland and filter for grasslands
aeo_parcel_gdf = parcel_gdf.loc[parcel_gdf['provincie'] != 'Zeeland']
aeo_grasslands = aeo_parcel_gdf.loc[aeo_parcel_gdf['cat_gewasc'] == 'Grasland']


# Write  grassland parcels to file 
grassland_fn = "02_aoi_grassland_parcels.shp"
grassland_file = os.path.join(output_folder + grassland_fn)
aeo_grasslands.to_file(grassland_file)



#%% For each SAR image selected, crop the raster to the Friesland parcel, store in subdirectory created in prev step

src_raster_path = "D:\\RGIC23GR10\\central_backscatter_vv\\Sigma0_dB_VV_20210116.tif"

shp_file_path = "D:\\RGIC23GR10\\output\\shapes\\fl_grassland_parcels.shp"

output_raster_path = "D:\\RGIC23GR10\output\\20210116_fl_grassland.tif"

with fiona.open(shp_file_path, "r") as shapefile:
    shapes = [feature["geometry"] for feature in shapefile]

with rasterio.open(src_raster_path) as src:

    out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
    out_meta = src.meta

# out_meta.update({"driver": "GTiff",
#                  "height": out_image.shape[1],
#                  "width": out_image.shape[2],
#                  "transform": out_transform})


with rasterio.open(output_raster_path, "w", **out_meta) as dest:
    dest.write(out_image)









