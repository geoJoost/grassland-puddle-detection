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

def filter_og_SAR(infile, outfile, polarisation, datelist):
    """
    Function to filter out backscatter images of interest from original data provided by WENR. The function iterates through the
    Sentinel-1 image folder and copies files which match the following format: Sigma0_dB_{polarisation}_{date}.tif to a new folder.
    Parameters
    ----------
    infile : TYPE string
        DESCRIPTION. Path to source S1 folder containing the raw data given by WENR.
    outfile : TYPE string
        DESCRIPTION. Destination folder to store filtered images
    polarisation : TYPE string
        DESCRIPTION. Polarisation of the SAR image you want to filter for. VV or VH.
    datelist : TYPE list of strings
        DESCRIPTION. List of the dates (as strings) you want to obtain the images for. Date format should match subdirectory folder names,
        i.e., the following format: YYYYMMDD. 

    Returns
    -------
    None.

    """
    # Create the output folder if it doesn't exist
    os.makedirs(outfile, exist_ok=True)

    # Iterate through the input folder and its subfolders
    for root, _, files in os.walk(infile):
        # Iterate through the files in the current subfolder
        for filename in files:
            # Check if the file matches the desired filename pattern
            if filename.startswith("Sigma0_dB_") and filename.endswith(".tif"):
                # Extract the polarization and date from the filename
                _, _, file_polarisation, filedate_tif = filename.split("_")
                file_date = filedate_tif.replace('.tif', '')
                #print(filename, file_polarisation, file_date)
                
                # Check if the polarization and date match the desired values
                if file_polarisation == polarisation and file_date in datelist:
                    # Construct the input and output file paths
                    input_path = os.path.join(root, filename)
                    output_path = os.path.join(outfile, filename)
                    #print(input_path, output_path)
                    # Copy the file to the output folder
                    shutil.copyfile(input_path, output_path)
                    print (f"{filename} was copied to {outfile}.")
    
    print(f"Copying of {polarisation} images finished")
    
def compress_images(src_dir, out_dir):
    """
    Function to compress S1 images using LZW compression. Compressed images are stored in separate folder
    and get a "_compressed.tif" suffix.

    Parameters
    ----------
    src_dir : TYPE string
        DESCRIPTION. Path to folder containing all the .tif images to be compressed.
    out_dir : TYPE string
        DESCRIPTION. Path to output directory where you want to store the compressed images.

    Returns
    -------
    None.

    """
    os.makedirs(out_dir, exist_ok=True)
    Image.MAX_IMAGE_PIXELS = None

    for file in os.listdir(src_dir):
        if file.endswith('.tif'):
            full_file_path = os.path.join(src_dir, file)
            out_file_path = os.path.join(out_dir, os.path.splitext(file)[0] + "_compressed.tif")

            with rasterio.open(full_file_path) as src:
                copy(src, out_file_path, driver='GTiff', compress='lzw')

    print("Image compression is done.")

        
def clip_raster_mixedpixel(raster_fp, vector_fp, output_fp):
    """
    Function clips input raster based on parcel shapefile. 
    The output raster countains backscatter values of mixed pixels, i.e., pixels that touch the parcel polygons.
    The value for exlcluded pixels is set to 999

    Parameters
    ----------
    raster_fp : TYPE string
        DESCRIPTION. Input .tif raster image filepath. The input raster should be (compressed) original SAR backscatter image.
    vector_fp : TYPE string
        DESCRIPTION. vector_fp : Input shapefile filepath. The shapefile should be the ANLB parcel polygons.
    output_fp : TYPE string
        DESCRIPTION. Output clipped raster filepath.

    Returns
    -------
    str
        DESCRIPTION.

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
    The output raster countains only backscatter values for pixels that lie purely inside parcel.

    Parameters
    ----------
    raster_fp : TYPE string
        DESCRIPTION. Input .tif raster image filepath. The input raster should be the mixed pixel clipping.
    vector_fp : TYPE string
        DESCRIPTION. Input shapefile filepath. The shapefile should be the line perimeter of the parcel polygons.
    output_fp : TYPE string
        DESCRIPTION. Output clipped raster filepath.

    Returns
    -------
    str
        DESCRIPTION.

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
    
def process_rasters(source_folder, destination_folder, clipfunction, shapefile):
    """
    Function to batch clip the SAR raster images to either pure or mixed pixels

    Parameters
    ----------
    source_folder : string
        DESCRIPTION. The filepath of the folder containing the raster images you want to clip. For mixed pixel
        this should be the original SAR images. For pure pixel it should be the folder containing the mixed pixel
        clippings.
    destination_folder : TYPE string
        DESCRIPTION. The destination folder you want to store the clipped rasters.
    clipfunction : TYPE function
        DESCRIPTION. Either clip_raster_mixedpixel or clip_raster_purepixel. 
    shapefile : TYPE shapefile
        DESCRIPTION. The shapefile you want to use to clip your raster to. In case of mixed pixel clipping, use
        parcel shapes. For pure pixel use the line perimeter of parcels.

    Returns
    -------
    None. 

    """
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
    
        
#%% Filter from original S1 data folder, only the backscatter .tif files obtained via central pass during study period. 

# Create list of the dates for which images should be filtered for
s1_pass_info_fp = data_folder + "S1A\Sentinel_1A_2021_overview.csv" #Read pass overview csv file
s1_pass_info_df = pd.read_csv(s1_pass_info_fp)
s1_central_pass_dates = s1_pass_info_df.loc[s1_pass_info_df['Overpass'] == 'central', 'Date'].tolist() # filter for central pass
s1_cp_jan_aug = [date for date in s1_central_pass_dates if date <= 20210820] # filter for january-august


# Filter images using filter_og_SAR function
infile = data_folder + "S1A\\"
outfile = data_folder + "S1A_VV_filtered_rf2"
polarisation = 'VV'
datelist = [str(date) for date in s1_cp_jan_aug]

filter_og_SAR(infile, outfile, polarisation, datelist)

#%% Compress all .tif images provided in separate date subdirectories and store all outputs in same file
# define source and output directories

src_dir = data_folder + "S1A_VV_filtered_rf" 
out_dir = data_folder + "S1A_VV_filtered_compressed"
compress_images(src_dir, out_dir) 


        
#%% Filter BRP parcel data to exclude Zeeland 
# NOTE: NO NEED TO RUN THIS PART IF YOU HAVE THE BRP PARCELS ALREADY, since it takes a long time
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

if os.path.exists(data_folder + "\\01_ANLB_filtered.shp"):
    print("01_ANLB_filtered.shp exists")
else: 
    filepath_ANLB = data_folder + "Shapes\\ANLB_2021.shp"
    code_list_ANLB = ['3a','3b','3c','3d']
    # filter ANLB data and safe it as a shapefile
    ANLB=filterANLB(filepath_ANLB,code_list_ANLB)
    ANLB.to_file(data_folder + "\\01_ANLB_filtered.shp")
    ANLB = gpd.read_file(data_folder + "\\01_ANLB_filtered.shp").to_crs(32631)

ANLB.to_file(output_folder + "02_anlb_filtered_epsg32631.shp")

anlb_perimeter = ANLB.boundary
anlb_perimeter.to_file(output_folder + "02_anlb_perimeter.shp")




#%% Clip both mixed pixels and pure pixels 

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


