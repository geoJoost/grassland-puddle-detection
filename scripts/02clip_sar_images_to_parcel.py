# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:08:02 2023

@author: petra
"""

import os
import pandas as pd
import shutil

import geopandas as gpd
import fiona
import rasterio
import rasterio.mask

from PIL import Image
from rasterio.shutil import copy
import glob


base = "D:\\RGIC23GR10\\"
data_folder = base + "data\\"
output_folder = base + "output\\"

#%% Functions

def filterANLB(filepath, code_list): # Can be imported from script 01
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

if os.path.exists(data_folder + "\\01_ANLB_filtered.shp"):
    print("01_ANLB_filtered.shp exists")
else: 
    filepath_ANLB = data_folder + "Shapes\\ANLB_2021.shp"
    code_list_ANLB = ['3a','3b','3c','3d']
    # filter ANLB data and safe it as a shapefile
    ANLB=filterANLB(filepath_ANLB,code_list_ANLB)
    ANLB.to_file(data_folder + "\\01_ANLB_filtered.shp")
    ANLB = gpd.read_file(data_folder + "\\01_ANLB_filtered.shp").to_crs(32631)

        
def clip_raster_mixedpixel(raster_fp, vector_fp, output_fp):
    """
    Function clips input raster based on parcel shapefile. 
    The output raster countains backscatter values of mixed pixels, i.e., pixels that touch the parcel polygons.
    
    raster_fp : Input .tif raster image filepath. The input raster should be (compressed) original SAR backscatter image.
    vector_fp : Input shapefile filepath. The shapefile should be the ANLB parcel polygons.
    output_fp : Output clipped raster filepath.
    
    """
    src_raster_path = raster_fp

    shp_file_path = vector_fp

    output_raster_path = output_fp

    with fiona.open(shp_file_path, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]

    with rasterio.open(src_raster_path) as src:

        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True, nodata=999, all_touched = True)
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                      "height": out_image.shape[1],
                      "width": out_image.shape[2],
                      "transform": out_transform})


    with rasterio.open(output_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)
        
        return f"{output_raster_path} was written to file."

def clip_raster_purepixel(raster_fp, vector_fp, output_fp):
    """
    Function clips input raster based on parcel perimeter shapefile. 
    The output raster countains only backscatter values for pixels that lie purely inside ANLB parcel.
    
    raster_fp : Input .tif raster image filepath. The input raster should be the mixed pixel clipping.
    vector_fp : Input shapefile filepath. The shapefile should be the line perimeter of the parcel polygons.
    output_fp : Output clipped raster filepath.
    
    """
    src_raster_path = raster_fp

    shp_file_path = vector_fp

    output_raster_path = output_fp

    with fiona.open(shp_file_path, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]

    with rasterio.open(src_raster_path) as src:

        out_image, out_transform = rasterio.mask.mask(src, shapes, nodata=999, all_touched = True, invert = True)
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                      "height": out_image.shape[1],
                      "width": out_image.shape[2],
                      "transform": out_transform})


    with rasterio.open(output_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)
        
        return f"{output_raster_path} was written to file." 
#%% Compress all .tif images provided in separate date subdirectories and store all outputs in same file
# define source and output directories

src_S1 = data_folder + "S1A\\" # This directory should have the same structure as the orignial S1 folder (i.e., contain subfolders with dates). Subdirectories should only contain the VV backscatter tif file.
compressed_img_location = data_folder + "S1A_compressed\\"


# define source and output directories
src_dir = src_S1
out_dir = compressed_img_location

# create the output directory if it does not exist
os.makedirs(out_dir, exist_ok=True)

# Increase the max pixel limit.
Image.MAX_IMAGE_PIXELS = None



for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.tif'):
            # Construct full file path
            full_file_path = os.path.join(root, file)
            # Construct output file path (without subdirectories) with "_compressed.tif" suffix
            out_file_path = os.path.join(out_dir, os.path.splitext(file)[0] + "_compressed.tif")

            # Open image file
            with rasterio.open(full_file_path) as src:
                # Copy the source image into the output file with LZW compression
                copy(src, out_file_path, driver='GTiff', compress='lzw')

print("Image compression is done.")

#%% Filter images by central pass dates and time

#Get list with the central pass dates and filter for january-august
s1_pass_info_fp = data_folder + "S1A\Sentinel_1A_2021_overview.csv"
s1_pass_info_df = pd.read_csv(s1_pass_info_fp)
s1_central_pass_dates = s1_pass_info_df.loc[s1_pass_info_df['Overpass'] == 'central', 'Date'].tolist() # filter for central pass
s1_cp_jan_aug = [date for date in s1_central_pass_dates if date <= 20210820] # filter for january-august

filtered_image_location = data_folder + "S1_VV_comp_filtered\\"
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
# NOTE: NO NEED TO RUN THIS PART IF YOU HAVE THE BRP PARCELS ALREADY
# parcel_shapefiles = data_folder + "Shapes\gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp"

# # Load in all datasets
# parcel_gdf = gpd.read_file(parcel_shapefiles).to_crs(32631)

# # Filter parcels to exclude Zeeland and filter for grasslands
# aeo_parcel_gdf = parcel_gdf.loc[parcel_gdf['provincie'] != 'Zeeland']
# aeo_grasslands = aeo_parcel_gdf.loc[aeo_parcel_gdf['cat_gewasc'] == 'Grasland']


# # Write  grassland parcels to file 
# grassland_fn = "02_aoi_grassland_parcels.shp"
# grassland_file = os.path.join(output_folder + grassland_fn)
# aeo_grasslands.to_file(grassland_file)



ANLB.to_file(output_folder + "02_anlb_filtered_epsg32631.shp")

anlb_perimeter = ANLB.boundary
anlb_perimeter.to_file(output_folder + "02_anlb_perimeter.shp")



#%% Testing mixed pixel function
src_raster_path = data_folder + "S1_VV_comp_filtered\Sigma0_dB_VV_20210116_compressed.tif"

shp_file_path = output_folder + "02_anlb_filtered_epsg32631.shp"

output_raster_path = output_folder + "Sigma0_dB_VV_20210116_clipped_ANLB2.tif"

clip_raster_mixedpixel(src_raster_path, shp_file_path, output_raster_path)


#%% Testing pure pixel
src_raster_path = output_folder + "Sigma0_dB_VV_20210116_clipped_ANLB2.tif"

shp_file_path = output_folder + "02_anlb_perimeter.shp"

output_raster_path = output_folder + "02_Sigma0_dB_VV_20210116_clipped_ANLB_pure.tif"

clip_raster_purepixel(src_raster_path, shp_file_path, output_raster_path)


#%% For loop to clip both mixed pixels and pure pixels 


# if not os.path.exists(mixed_pixel_fp):
#     os.makedirs(mixed_pixel_fp)

def process_rasters(source_folder, destination_folder, clipfunction, shapefile):
    # Create the destination folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    # Get a list of .tif files in the source folder
    file_list = glob.glob(os.path.join(source_folder, '*.tif'))

    # Iterate through each file
    for file_path in file_list:
        # Get the filename and extension
        filename = os.path.splitext(os.path.basename(file_path))[0]

        # Create the new filename
        if clipfunction == clip_raster_mixedpixel:
            new_filename = f"02_{filename}_mp_clip.tif"
        elif clipfunction == clip_raster_purepixel:
            new_filename = f"{filename.replace('_mp', '_pp')}.tif"
        else:
            print ('This clip function does not exist.')

        # Construct the output file path
        output_path = os.path.join(destination_folder, new_filename)

        # Apply the clip function to the raster
        clipfunction(file_path, shapefile, output_path)

# Mixed pixel clipping

src_raster_og = data_folder + "S1_VV_comp_filtered\\"
anlb_parcel_fp = output_folder + "02_anlb_filtered_epsg32631.shp"
mixed_pixel_fp = output_folder + "S1_VV_mixedpixel_clipped\\"

process_rasters(src_raster_og,mixed_pixel_fp, clip_raster_mixedpixel, anlb_parcel_fp)

# Pure pixel clipping
src_raster_mp = mixed_pixel_fp
anlb_perimeter_fp = output_folder + "02_anlb_perimeter.shp"
pure_pixel_fp = output_folder + "S1_VV_purepixel_clipped\\"

process_rasters(src_raster_mp, pure_pixel_fp, clip_raster_purepixel, anlb_perimeter_fp)

# Clipping SAR data to grassland parcels and ANLB parcels for Marnic
src_raster = "D:\RGIC23GR10\data\S1_VV_comp_filtered\Sigma0_dB_VV_20210317_compressed.tif"
grassland_anlb = output_folder + "02_aoi_grassland_parcels_merged.shp"
output_raster_fp = output_folder + "02_Sigma0_dB_VV_20210317_compressed_glanlb_clip.tif"
clip_raster_mixedpixel(src_raster, grassland_anlb, output_raster_fp)


