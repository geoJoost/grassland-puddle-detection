import rasterio
import numpy as np
import geopandas as gpd
import os
from rasterio.mask import mask
import glob
import pandas as pd
from datetime import datetime
import math
from s04b_get_threshold_value import average_threshold



output_path = '../output'
image_folder = '../data/S1_VV_comp_filtered'
shapefile_path = '../data/01_SUBSIDISED_FIELDS/01_subsidised_field.shp'



def calculate_inundation(thresholded_image):
    inundated_pixels = np.count_nonzero(thresholded_image == 1)
    total_pixels = np.size(thresholded_image)
    inundation_percentage = (inundated_pixels / total_pixels) * 100
    print(f"Inundation percentage: {inundation_percentage}")
    return inundation_percentage




def calculate_inundation_all_images(image_folder, shapefile_filepath, output_folder, threshold):
    image_filepaths = sorted(glob.glob(f"{image_folder}/*.tif"))
    gdf = gpd.read_file(shapefile_filepath)
    
    category_images = {"3a": [], "3b": [], "3c": [], "3d": []}
    category_dfs = {"3a": pd.DataFrame(), "3b": pd.DataFrame(), "3c": pd.DataFrame(), "3d": pd.DataFrame()}
    
    for image_filepath in image_filepaths:
        date_str = os.path.basename(image_filepath).split('_')[3]  
        date = datetime.strptime(date_str, "%Y%m%d")  

        if datetime(date.year, 2, 15) <= date <= datetime(date.year, 4, 15):
            category_images["3a"].append(image_filepath)
        if datetime(date.year, 2, 15) <= date <= datetime(date.year, 5, 15):
            category_images["3b"].append(image_filepath)
        if datetime(date.year, 2, 15) <= date <= datetime(date.year, 6, 15):
            category_images["3c"].append(image_filepath)
        if datetime(date.year, 2, 15) <= date <= datetime(date.year, 8, 15):
            category_images["3d"].append(image_filepath)

    print("Category Dict")

    print(category_images)

    for category, image_filepaths in category_images.items():
        category_gdf = gdf[gdf["CODE_BEHEE"] == category]
        
        for i in range(len(image_filepaths) - 1):
            with rasterio.open(image_filepaths[i]) as src1, rasterio.open(image_filepaths[i + 1]) as src2:
                image1 = src1.read(1)
                image2 = src2.read(1)
                average_image = (image1 + image2) / 2
                
                profile = src1.profile
                avg_output_filepath = os.path.join(f"{output_folder}/{category}_average_{i + 1}", f'{category}_average_{i + 1}.tif')
                os.makedirs(os.path.dirname(avg_output_filepath), exist_ok=True)
                
                with rasterio.open(avg_output_filepath, 'w', **profile) as dst:
                    dst.write(average_image, 1)

                category_gdf = category_gdf.to_crs(src1.crs)
                print(f"Calculating inundation for {category}_average_{i + 1}.tif")
                for idx, row in category_gdf.iterrows():
                    with rasterio.io.MemoryFile() as memfile:
                        with memfile.open(**profile) as dataset:
                            dataset.write(average_image, 1)
                            parcel_image, _ = mask(dataset, [row['geometry']], crop=True)
                            
                            if parcel_image.size == 0:
                                continue

                            parcel_image_copy = parcel_image.copy()
                            parcel_image_copy[parcel_image_copy > threshold] = 0
                            parcel_image_copy[parcel_image_copy <= threshold] = 1

                            inundation_percentage = calculate_inundation(parcel_image_copy)

                            category_dfs[category].loc[idx, 'parcelId'] = row['OBJECTID'] if math.isnan(row['fieldid']) else row['fieldid']
                            category_dfs[category].loc[idx, f'avg_{i + 1}'] = 1 if inundation_percentage > 60 else 0

                            minx, miny, maxx, maxy = row['geometry'].bounds

                            new_profile = profile.copy()
                            new_profile.update({
                                "dtype": rasterio.float32,
                                "height": parcel_image_copy.shape[0],
                                "width": parcel_image_copy.shape[1],
                                "transform": rasterio.Affine.translation(minx, miny) * profile["transform"]
                            })

                            output_filepath = os.path.join(f"{output_folder}/{category}_average_{i + 1}", f'{category}_thresholded_parcel_{idx}.tif')
                            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

                            with rasterio.open(output_filepath, 'w', **new_profile) as dst:
                                dst.write(parcel_image_copy)

    for category, df in category_dfs.items():
        df.to_csv(f'../output/{category}_output.csv', index=False)
        df.to_excel(f'../output/{category}_output.xlsx')


   

    return category_dfs





threshold_value = average_threshold()

calculate_inundation_all_images(image_folder, shapefile_path, output_path, threshold_value)

