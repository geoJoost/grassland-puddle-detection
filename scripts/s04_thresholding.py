import rasterio
import numpy as np
import geopandas as gpd
import os
from rasterio.mask import mask
import glob
import pandas as pd
from datetime import datetime
import math

# from inundation import calculate_inundation




# Define the file paths
# data_path = 'data'
output_path = '../output'

# s1_images_path = os.path.join(data_path, 'Sentinel-1')
# input_path = os.path.join(s1_images_path, 'S1_20150327-VV.tif')
# output_path = os.path.join(output_path, '04_threshold_inundation_outputs')
# shapefile_path = os.path.join(output_path, 'shapey.shp')



def calculate_inundation(thresholded_image):

    print("Total number of pixels for thresholded image")

    print(np.count_nonzero(thresholded_image))

    # Count the number of inundated pixels
    inundated_pixels = np.count_nonzero(thresholded_image == 1)


    print("Total number of water pixels for thresholded imaage")

    print(inundated_pixels)
    
    # Calculate the total number of pixels in the image
    total_pixels = thresholded_image.size
    
    # Calculate the percentage of inundation
    inundation_percentage = (inundated_pixels / total_pixels) * 100

    return inundation_percentage





def calculate_inundation_all_images(image_folder, shapefile_filepath, output_folder, threshold):
    # Create a list of image file paths in the directory
    image_filepaths = sorted(glob.glob(f"{image_folder}/*.tif"))

    # Load the shapefile with geopandas
    gdf = gpd.read_file(shapefile_filepath)

    # print(gdf)

    # Initialize an empty dataframe for storing the results
    df = pd.DataFrame()

    # Initialize a dictionary to hold images by month
    monthly_images = {}

    for image_filepath in image_filepaths:
        # Get the month from the file name
        date_str = os.path.basename(image_filepath).split('_')[3]  # For filename like 'Sigma0_dB_VV_20210104_compressed.tif'
        month_str = date_str[:6]  # YYYYMM

        # Open the tif image and read it into a numpy array
        with rasterio.open(image_filepath) as src:
            image = src.read(1)

            # Update the CRS of the shapefile to match the raster
            gdf = gdf.to_crs(src.crs)

            # Add the image to the corresponding month
            if month_str not in monthly_images:
                monthly_images[month_str] = []
            monthly_images[month_str].append(image)

    for month_str, image_list in monthly_images.items():
        # Calculate the average of the images for the month
        average_image = sum(image_list) / len(image_list)

        # Get the metadata/profile of one of the source images
        profile = rasterio.open(image_filepaths[0]).profile

        # Write the averaged image to a new .tif file
        avg_output_filepath = os.path.join(output_folder, f'04_avg_{month_str}.tif')
        with rasterio.open(avg_output_filepath, 'w', **profile) as dst:
            dst.write(average_image, 1)

        # For each parcel, mask the raster with the parcel shape
        for idx, row in gdf.iterrows():
            with rasterio.io.MemoryFile() as memfile:
                with memfile.open(**profile) as dataset:  # opening the dataset
                    dataset.write(average_image, 1)  # writing the image data to the dataset
                    parcel_image, _ = mask(dataset, [row['geometry']], crop=True)
                    
                    # Ignore if the parcel has no overlap with the image
                    if parcel_image.size == 0:
                        continue

                    # Copy the average image data
                    parcel_image_copy = parcel_image.copy()

                    print("Checking min, max and median")
                    print(f"median: {np.median(parcel_image_copy)}")
                    print(f"min: {np.min(parcel_image_copy)}")
                    print(f"max: {np.max(parcel_image_copy)}")
                    print(f"mean: {np.mean(parcel_image_copy)}")

                    # Apply the thresholding
                    parcel_image_copy[parcel_image_copy > threshold] = 0
                    parcel_image_copy[parcel_image_copy <= threshold] = 1

                    


                    # Calculate the percentage of inundation
                    inundation_percentage = calculate_inundation(parcel_image_copy)

                    # Save the result to the dataframe
                    df.loc[idx, 'parcelId'] = row['OBJECTID'] if math.isnan(row['fieldid']) else row['fieldid']
                    df.loc[idx, f'avg_{month_str}'] = 1 if inundation_percentage > 60 else 0

                    

                    # Calculate the bounds of the parcel
                    minx, miny, maxx, maxy = row['geometry'].bounds

                    # Update the profile to reflect the new data
                    new_profile = profile.copy()
                    new_profile.update({
                        "dtype": rasterio.float32,
                        "height": parcel_image_copy.shape[0],
                        "width": parcel_image_copy.shape[1],
                        "transform": rasterio.Affine.translation(minx, miny) * profile["transform"]
                    })

                    # Write the thresholded parcel image back to a new .tif file
                    output_filepath = os.path.join(output_folder, f'04_thresholded_parcel_{idx}_{month_str}.tif')
                    with rasterio.open(output_filepath, 'w', **new_profile) as dst:
                        dst.write(parcel_image_copy)

                print(df)

    df.to_csv('../output/output.csv', index=False)
    df.to_excel('../output/output.xlsx')

    return df








calculate_inundation_all_images("../data/S1_VV_comp_filtered", "../data/01_SUBSIDISED_FIELDS/01_subsidised_field.shp", output_path, -3)



