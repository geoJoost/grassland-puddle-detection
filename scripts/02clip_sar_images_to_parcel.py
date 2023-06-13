# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:08:02 2023

@author: petra
"""

import os
import pandas as pd
import geopandas as gpd
import shutil

import fiona
import rasterio
import rasterio.mask

indir = "D:\\RGIC23GR10\\"
outdir = "D:\\RGIC23GR10\\output\\"

# Define file paths
parcel_shapes = indir + "\\Shapes\\gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp"
s1_pass_info_fp =  indir + "\\S1\\Sentinel_1A_2021_overview.csv"


# Load in all datasets
parcel_gdf = gpd.read_file(parcel_shapes).to_crs(32631)


# Filter parcels to Friesland only
fl_parcel_gdf = parcel_gdf.loc[parcel_gdf['provincie'] == 'Friesland']
fl_grasslands = fl_parcel_gdf.loc[fl_parcel_gdf['cat_gewasc'] == 'Grasland']

# Write Friesland grassland parcels to file 
subfolder = "shapes"
grasland_fn = "fl_grassland_parcels.shp"
subfolder_path = os.path.join(outdir + subfolder)
if not os.path.exists(subfolder_path ): # Create 'shapes' subfolder in output directory if it's not created yet
    os.makedirs(subfolder_path)

if not os.listdir(subfolder_path):
    output_file = os.path.join(subfolder_path, grasland_fn)  # Specify the output file path within the subfolder
    fl_grasslands.to_file(output_file)
    print("Data written to file.")
else:
    print("Subfolder contains files. No action taken.")


#%% Select SAR images with central overpass based on pass info csv file
#Get list with the centrall pass dates
s1_pass_info_df = pd.read_csv(s1_pass_info_fp)
s1_central_pass_dates = s1_pass_info_df.loc[s1_pass_info_df['Overpass'] == 'central', 'Date'].tolist()

#Create subfolder in input directory to store the central pass, VV backscatter .tif files
central_pass_subfolder = "central_backscatter_vv"
subfolder_path = os.path.join(indir + central_pass_subfolder)
if not os.path.exists(subfolder_path ): # Create 'shapes' subfolder in output directory if it's not created yet
    os.makedirs(subfolder_path)


# Specify the parent directory and the destination folder
parent_directory = indir + "S1" # Replace with the actual parent directory path
destination_folder = indir + central_pass_subfolder  # Replace with the actual destination folder path

# Iterate over each date in the list containing central pass dates
for date in s1_central_pass_dates:
    # Construct the folder path based on the date
    folder_path = os.path.join(parent_directory, str(date))
    
    # Check if the folder exists
    if os.path.exists(folder_path):
        # Find the file with the specified name pattern
        file_pattern = f"Sigma0_dB_VV_{date}.tif"
        files = [file for file in os.listdir(folder_path) if file.endswith(file_pattern)]
        
        if len(files) > 0:
            # Copy the file to the destination folder
            source_file = os.path.join(folder_path, files[0])
            destination_file = os.path.join(destination_folder, files[0])
            shutil.copy(source_file, destination_file)
            print(f"File {files[0]} copied successfully.")
        else:
            print(f"No matching file found in folder {folder_path}.")
    else:
        print(f"Folder {folder_path} does not exist.")

# Make subdirectory in output folder for the cropped SAR images
cropped_sar_subfolder = "cropped_sar_images"
cropped_sar_subfolder_path = os.path.join(outdir + cropped_sar_subfolder)
if not os.path.exists(cropped_sar_subfolder_path ): # Create 'shapes' subfolder in output directory if it's not created yet
    os.makedirs(cropped_sar_subfolder_path)

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









