# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:08:02 2023

@author: petra
"""

import os
import sys
import pandas as pd
import shutil

import geopandas as gpd
import rasterio
import rasterio.mask

from PIL import Image
from rasterio.shutil import copy
import glob


#base = "D:\\RGIC23GR10\\"
data_folder = r"data/"
output_folder = r"output/"

#%% Functions


def filter_og_SAR(infile, polarisation, fp_csv):
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
    outfile = os.path.join(data_folder + f"S1_{polarisation}_filtered")
    
    # Create the output folder if it doesn't exist
    os.makedirs(outfile, exist_ok=True)
    
    # Define complete file-paths
    infile = os.path.join(data_folder + "S1/")
    
    # Create list of the dates for which images should be filtered for
    s1_pass_info_df = pd.read_csv(os.path.join(data_folder, fp_csv)) #Read pass overview csv file

    
    # Select only the overpass images
    s1_central_pass_dates = s1_pass_info_df.loc[s1_pass_info_df['Overpass'] == 'central', 'Date'].tolist() # filter for central pass
    
    # Convert to list for easier filtering later on
    # Note we only take images taken before the 20th of August
    datelist = [str(date) for date in s1_central_pass_dates if date <= 20210820]

    # Iterate through the input folder and its subfolders
    for root, _, files in os.walk(infile):

        # Iterate through the files in the current subfolder
        for filename in files:
            
            # Check if the file matches the desired filename pattern
            if filename.startswith("Sigma0_dB_") and filename.endswith(".tif") and not "quicklook" in filename:
                #print(filename)
                
                # Extract the polarization and date from the filename
                file_polarisation, filedate_tif = filename.split("_")[2], filename.split("_")[3]
                
                file_date = filedate_tif.replace('.tif', '')
                #print(filename, file_polarisation, file_date)
                
                # Check if the polarization and date match the desired values
                if file_polarisation == polarisation and file_date in datelist:
                    # Construct the input and output file paths
                    input_path = os.path.join(root, filename)
                    output_path = os.path.join(outfile, filename)
                    
                    print (f"{filename} was copied to {outfile}.")
                    
                    # Copy the file to the output folder
                    shutil.copyfile(input_path, output_path)

    
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

    # Create filepath
    fp_anlb = os.path.join(output_folder + vector_fp)
    
    print(fp_anlb)

    output_raster_path = output_fp
    
    if os.path.exists(fp_anlb):
        #print("01_ANLB_filtered.shp exists") # Use for error-handling. Removed due to spam
        
        # Read in the shapefile
        gdf = gpd.read_file(fp_anlb).to_crs(32631)
        
        # Flatten the geometry into GeoJSON-like format as required by rasterio.mask()
        shapes = gdf[['geometry']].values.flatten()
        
    else: 
        print("Filtered ANLB file does not exist. Please run script #1")
        sys.exit()     

    with rasterio.open(raster_fp) as src:

        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True, nodata=999, all_touched = True)
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                      "height": out_image.shape[1],
                      "width": out_image.shape[2],
                      "transform": out_transform})


    with rasterio.open(output_raster_path, "w", **out_meta) as dest:
        dest.write(out_image)
        
        print(f"{output_raster_path} was written to file")

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
      
    
    # Read in the shapefile
    gdf = gpd.read_file(vector_fp).to_crs(32631)
    
    # Flatten the geometry into GeoJSON-like format as required by rasterio.mask()
    shapes = gdf[['geometry']].values.flatten()

    with rasterio.open(raster_fp) as src:

        out_image, out_transform = rasterio.mask.mask(src, shapes, nodata=999, all_touched = True, invert = True)
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                      "height": out_image.shape[1],
                      "width": out_image.shape[2],
                      "transform": out_transform})


    with rasterio.open(output_fp, "w", **out_meta) as dest:
        dest.write(out_image)
        
        print(f"{output_fp} was written to file")
    
def process_rasters(polarisation, clipfunction, shapefile, source_folder):
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
    # Create filepath + destination folder if it does not yet exist
    destination_folder = os.path.join(output_folder, f"02_{polarisation}_{clipfunction}_clipped")
    os.makedirs(destination_folder, exist_ok=True)
     

    # Get a list of .tif files in the source folder
    #file_list = glob.glob(os.path.join(source_folder, '*.tif'))
    file_list = glob.glob(source_folder)
    
    # Iterate through each file
    for file_path in file_list:
        # Get the filename and extension
        filename = os.path.splitext(os.path.basename(file_path))[0]

        # Create the new filename
        if clipfunction == "mp":
            clip_func = clip_raster_mixedpixel
            new_filename = f"02_{filename}_mp_clip.tif"
            
        elif clipfunction == "pp": 
            # Note that pure-pixel is based on mixed-pixel clipping, therefore the name is different
            clip_func = clip_raster_purepixel
            new_filename = filename.replace("_mp_clip", "_pp_clip")
            
        else:
            print ('This clip function does not exist.')

        # Construct the output file path
        output_path = os.path.join(destination_folder, new_filename)

        # Apply the clip function to the raster
        #clipfunction(file_path, shapefile, output_path)
        clip_func(file_path, shapefile, output_path)


    
        
#%% Filter from original S1 data folder, only the backscatter .tif files obtained via central pass during study period. 

filter_og_SAR("data/S1/", "VV", "S1/Sentinel_1A_2021_overview.csv") # VV polarisation
filter_og_SAR("data/S1/", "VH", "S1/Sentinel_1A_2021_overview.csv") # VH polarisation

#%% OPTIONAL : Compress all .tif images provided in separate date subdirectories and store all outputs in same file
# define source and output directories
"""
OPTIONAL COMPRESSION
src_dir = data_folder + "S1A_VV_filtered" 
out_dir = data_folder + "S1A_VV_filtered_compressed"
compress_images(src_dir, out_dir) 
"""

#%% Clip both mixed pixels and pure pixels 

# Mixed pixel clipping
process_rasters("VV", "mp", "01_anlb_drygrass_merged.shp", os.path.join(data_folder, "S1_VV_filtered/", "*.tif"))
process_rasters("VH", "mp", "01_anlb_drygrass_merged.shp", os.path.join(data_folder, "S1_VH_filtered/", "*.tif"))


"""
 OPTIONAL: Pure pixel clipping in case SAR images have to clipped to only pixels lying completely within parcel boundaries
 
#src_raster_mp = mixed_pixel_fp
#anlb_perimeter_fp = data_folder + "02_anlb_perimeter.shp"
#pure_pixel_fp = output_folder + "02_VV_purepixel_clipped\\"

# Load in the ANLB data and retrieve ONLY the boundaries of polygons
anlb_perimeter = gpd.read_file(output_folder + "\\01_ANLB_filtered.shp").to_crs(32631).boundary

fp_anlb_perimeter = os.path.join(data_folder, "02_anlb_perimeter.shp")
anlb_perimeter.to_file(fp_anlb_perimeter)

process_rasters("VV", "pp", fp_anlb_perimeter, os.path.join(output_folder, "02_VV_mp_clipped/", "*.tif"))
process_rasters("VH", "pp", fp_anlb_perimeter, os.path.join(output_folder, "02_VH_mp_clipped/", "*.tif"))

"""

