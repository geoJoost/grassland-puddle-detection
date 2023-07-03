import rasterio
import numpy as np
import geopandas as gpd
import os

import glob
import pandas as pd
from datetime import datetime

from s04b_get_threshold_value import average_threshold
from rasterio.io import MemoryFile

import argparse

# create the parser
parser = argparse.ArgumentParser(description='Puddles')

# add the argument
parser.add_argument('--threshold_value', type=float, help='Threshold value. Defaults to 0.5 if nothing is provided')

# parse the arguments
args = parser.parse_args()

output_path = '../output'
# To run the script for VV-polarization, change the line below to ***image_folder = '../data/02_VV_mp_clipped'****
image_folder = '../data/02_VH_mp_clipped'
shapefile_path = '../output/01_subsidised_field.shp'



    

def calculate_inundation(thresholded_image, id):
    # Replace nan values with 1
    img = np.nan_to_num(thresholded_image, nan=1)

    inundated_pixels = np.count_nonzero(img == 1)
    total_pixels = np.size(img)
    print(f"parcel id: {id}")
    # print(thresholded_image)
    # print(img)
    print(f"Total pixels in parcel: {total_pixels}")
    print(f"inundated pixels in parcel: {inundated_pixels}")
    if(total_pixels == 0):
        return 200
    else:
        inundation_percentage = (inundated_pixels / total_pixels) * 100
        return inundation_percentage


def calculate_inundation_all_images(image_folder, shapefile_filepath, output_folder, threshold):
    image_filepaths = sorted(glob.glob(f"{image_folder}/*.tif"))
    gdf = gpd.read_file(shapefile_filepath)
    nodata_value = 999  # Define your NoData value

    # Create an empty dataframe for binary values
    df = pd.DataFrame()

    # Create a separate dataframe for parcel-level inundation percentages
    parcel_df = pd.DataFrame()

    category_dates = {
        "3a": (2, 15, 4, 15),
        "3b": (2, 15, 5, 15),
        "3c": (2, 15, 6, 15),
        "3d": (2, 15, 8, 15)
    }

    # Filter image filepaths based on date range
    start_date = datetime.now().replace(
        month=category_dates["3d"][0], day=category_dates["3d"][1]
    ).date()
    end_date = datetime.now().replace(
        month=category_dates["3d"][2], day=category_dates["3d"][3]
    ).date()

    image_filepaths = [
    image for image in image_filepaths if datetime.strptime(
        os.path.basename(image).split('_')[4], "%Y%m%d"
    ).date() >= datetime.now().replace(
        month=category_dates["3d"][0], day=category_dates["3d"][1], year=2021
    ).date() and datetime.strptime(
        os.path.basename(image).split('_')[4], "%Y%m%d"
    ).date() <= datetime.now().replace(
        month=category_dates["3d"][2], day=category_dates["3d"][3], year=2021
    ).date()
    ]

    # print(len(image_filepaths))

    # Iterate over all the images, excluding the last one
    for i in range(len(image_filepaths) - 1):
        with rasterio.open(image_filepaths[i]) as src1, rasterio.open(image_filepaths[i + 1]) as src2:
            image1 = src1.read(1)
            image2 = src2.read(1)
            

            # Convert nodata values to np.nan
            image_one = np.where(image1 == nodata_value, np.nan, image1)
            image_two = np.where(image2 == nodata_value, np.nan, image2)

            # Compute the average while ignoring np.nan values
            average_image = np.nanmean([image_one, image_two], axis=0)


            # Get the date of the second image
            # date_str = os.path.basename(image_filepaths[i + 1]).split('_')[3].split('.')[0]
            date_str = os.path.basename(image_filepaths[i + 1]).split('_')[4]

            date = datetime.strptime(date_str, "%Y%m%d")

            profile = src1.profile

            # Save the average image
            avg_output_filepath = os.path.join(f"{output_folder}/running_average", f'running_average_{i + 1}.tif')
            os.makedirs(os.path.dirname(avg_output_filepath), exist_ok=True)
            with rasterio.open(avg_output_filepath, 'w', **profile) as dst:
                dst.write(average_image, 1)

            # Convert the average image to binary
            binary_image = average_image.copy()
            binary_image[binary_image > threshold] = 0
            binary_image[binary_image <= threshold] = 1

            

            # Save the binary image
            binary_output_filepath = os.path.join(f"{output_folder}/binary", f'binary_{i + 1}.tif')
            os.makedirs(os.path.dirname(binary_output_filepath), exist_ok=True)
            with rasterio.open(binary_output_filepath, 'w', **profile) as dst:
                dst.write(binary_image, 1)

            gdf = gdf.to_crs(src1.crs)

            for idx, row in gdf.iterrows():
                start_month, start_day, end_month, end_day = category_dates[row["CODE_BEHEE"]]
                start_date = datetime(date.year, start_month, start_day)
                end_date = datetime(date.year, end_month, end_day)

                if start_date <= date <= end_date:
                    # Write the binary_image array to a temporary rasterio dataset
                    with MemoryFile() as memfile:
                        with memfile.open(**profile) as dataset:
                            dataset.write(binary_image, 1)
                            # Now you can pass the dataset (which is a DatasetWriter object) to the mask function
                            parcel_binary_image, _ = rasterio.mask.mask(dataset, [row['geometry']], crop=True, nodata=np.nan)

                    if parcel_binary_image.size == 0:
                        continue

                    inundation_percentage = calculate_inundation(parcel_binary_image, int(row['OBJECTID']))


                    # Update column names in parcel_df with second date
                    column_name = f'{date.date()}'

                    df.loc[idx, 'OBJECTID'] = int(row['OBJECTID']) 
                    # if math.isnan(row['fieldid']) else int(row['fieldid'])
                    df.loc[idx, column_name] = 1 if inundation_percentage > 60 else 0

                   
                    parcel_df.loc[idx, 'OBJECTID'] = int((row['OBJECTID'])) 
                    # if math.isnan(row['fieldid']) else int(row['fieldid'])
                    parcel_df.loc[idx, column_name] = int(round(inundation_percentage))



    # Save binary dataframe to CSV and Excel files
    df.to_csv(f'{output_folder}/{args.threshold_value}-output.csv', index=False)
    df.to_excel(f'{output_folder}/{args.threshold_value}-output.xlsx', index=False)

    # Save parcel-level inundation percentages to separate CSV and Excel files
    parcel_df.to_csv(f'{output_folder}/{args.threshold_value}-parcel_inundation.csv', index=False)
    parcel_df.to_excel(f'{output_folder}/{args.threshold_value}-parcel_inundation.xlsx', index=False)





threshold_value = average_threshold(args.threshold_value)
calculate_inundation_all_images(image_folder, shapefile_path, output_path, threshold_value)
