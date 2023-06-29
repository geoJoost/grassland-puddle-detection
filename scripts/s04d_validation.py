import os
import glob
import datetime
import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
from rasterio.mask import mask
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import fsolve

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import json
from shapely.geometry import mapping
from sklearn.metrics import accuracy_score
from s04b_get_threshold_value import average_threshold

filename_brp_sample = '../data/thresh_stuff/training/brp/01_brp_dry_grass_sample.shp'
fp_waterpoly = '../data/thresh_stuff/training/water'
sar_images_vv = "../data/thresh_stuff/output/averages"
binary_images_vv = "../data/thresh_stuff/output/binary"


# Mapping of average_X.tif files to corresponding WaterYYYYMMDD.shp files
mapping_dict = {
    'average_1.tif': 'Water20210226.shp',
    'average_2.tif': 'Water20210331.shp',
    'average_3.tif': 'Water20210427.shp',
    'average_4.tif': 'Water20210530.shp',
    'average_5.tif': 'Water20210616.shp'
}



def load_raster(ds):
    return ds.read(1)

def extract_raster_value(vector, ds):
    shapes = [feature.__geo_interface__ for feature in vector.geometry]
    masked_image, masked_transform = mask(dataset=ds, shapes=shapes, crop=True, nodata=np.nan)
    raster_values = masked_image[0]
    raster_values_flat = raster_values.flatten()
    raster_values_flat = raster_values_flat[~np.isnan(raster_values_flat)]
    return raster_values_flat

def get_pixels(water, sar, brp):
    gdf_waterpoly = gpd.read_file(water).set_crs('EPSG:28992').to_crs('EPSG:32631')
    gdf_brp = gpd.read_file(brp)
    sar_vv_ds = rasterio.open(sar)
    sar_vv = load_raster(sar_vv_ds)
    arr_water_vv = extract_raster_value(gdf_waterpoly, sar_vv_ds)
    arr_brp_vv = extract_raster_value(gdf_brp, sar_vv_ds)

    if len(arr_brp_vv) > len(arr_water_vv):
        arr_brp_vv = np.random.choice(arr_brp_vv, len(arr_water_vv), replace=False)

    print(f"Total Water Pixels {len(arr_water_vv)}")
    print(f"Total BRP Pixels (random sub samples) {len(arr_brp_vv)}")

    sar_vv_ds.close()

    return arr_water_vv, arr_brp_vv

def binary_and_confusion():
    threshold_value = average_threshold()
    actual_labels = []
    predicted_labels = []
    image_counter = 1

    for sar, water in mapping_dict.items():
        sar = os.path.join(sar_images_vv, sar)
        
        water = os.path.join(fp_waterpoly, water)

        ground_truth_values, brp_values = get_pixels(water, sar, filename_brp_sample)
        
        with rasterio.open(sar) as src:
            sar_data = src.read(1)
            profile = src.profile

        binary_image = sar_data.copy()
        binary_image[sar_data > threshold_value] = 0
        binary_image[sar_data <= threshold_value] = 1

        binary_output_filepath = os.path.join("../data/thresh_stuff/output/binary", f'binary_{image_counter}.tif')
        os.makedirs(os.path.dirname(binary_output_filepath), exist_ok=True)
        with rasterio.open(binary_output_filepath, 'w', **profile) as dst:
            dst.write(binary_image, 1)

        binary = os.path.join(binary_images_vv, f"binary_{image_counter}.tif")

        print(f"on binary_{image_counter}.tif")

        classified_water, classified_grass = get_pixels(water, binary, filename_brp_sample)

        actual_labels.extend(['water']*len(ground_truth_values))
        actual_labels.extend(['grass']*len(brp_values))

        # These are the predicted labels for the ground truth and brp_values pixel locations
        predicted_water_labels = ['water' if i == 1 else 'grass' for i in classified_water]
        predicted_grass_labels = ['water' if i == 1 else 'grass' for i in classified_grass]

        predicted_labels.extend(predicted_water_labels)
        predicted_labels.extend(predicted_grass_labels)

        image_counter += 1

    # print(predicted_labels[-10:]) 

    predicted_labels.extend(['water', 'grass'])
    # print(predicted_labels[-10:]) 

    confusion_matrix = pd.crosstab(pd.Series(actual_labels, name='Actual'),
                                   pd.Series(predicted_labels, name='Predicted'))

    # Calculate precision, recall and accuracy
    TP = confusion_matrix.loc['water', 'water']
    FP = confusion_matrix.loc['grass', 'water']
    TN = confusion_matrix.loc['grass', 'grass']
    FN = confusion_matrix.loc['water', 'grass']

    precision = TP / (TP + FP)
    recall = TP / (TP + FN)
    accuracy = (TP + TN) / (TP + FP + FN + TN)

    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"Overall accuracy: {accuracy}")

    # Store the metrics in a dictionary
    metrics = {'Precision': precision, 'Recall': recall, 'Accuracy': accuracy}

    # Save the confusion matrix to a CSV file
    confusion_matrix.to_csv("../output/confusion_matrix.csv")

    # Save the metrics to the same CSV file
    with open("../output/confusion_matrix.csv", 'a') as f:
        f.write("\n\nMetrics:\n")
        for key, val in metrics.items():
            f.write(f"{key},{val}\n")

binary_and_confusion()

