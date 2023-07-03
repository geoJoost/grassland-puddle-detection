import os

import rasterio
import geopandas as gpd
import numpy as np
from rasterio.mask import mask

from scipy.optimize import fsolve

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


np.random.seed(42)



filename_brp_sample ="../output/01_brp_grassland_sample_200.shp" # Training grass parcel set

fp_waterpoly = "../data/training_data"

sar_images_vv = "../data/thresholding_data/output/averages"

# Mapping of average_X.tif files to corresponding WaterYYYYMMDD.shp files
mapping_dict = {
    'average_1.tif': 'Water20210226.shp',
    'average_2.tif': 'Water20210331.shp',
    'average_3.tif': 'Water20210427.shp',
    'average_4.tif': 'Water20210530.shp',
    'average_5.tif': 'Water20210616.shp'
}


def sigmoid(x):
        return 1 / (1 + np.exp(-x))



def extract_raster_value(vector, ds):
    shapes = [feature.__geo_interface__ for feature in vector.geometry]
    masked_image, masked_transform = mask(dataset=ds, shapes=shapes, crop=True, nodata = np.nan)
    raster_values = masked_image[0]
    raster_values_flat = raster_values.flatten()
    # Exclude values that are equal to np.nan
    raster_values_flat = raster_values_flat[~np.isnan(raster_values_flat)]
    return raster_values_flat

def load_raster(ds):
    return ds.read(1)


def get_threshold(water, sar, brp, threshold):
    gdf_waterpoly = gpd.read_file(water).set_crs('EPSG:28992').to_crs('EPSG:32631')
    gdf_brp = gpd.read_file(brp)
    sar_vv_ds = rasterio.open(sar)
    sar_vv = load_raster(sar_vv_ds)
    mask1 = np.isnan(sar_vv)
    arr_water_vv = extract_raster_value(gdf_waterpoly, sar_vv_ds)
    arr_brp_vv = extract_raster_value(gdf_brp, sar_vv_ds)

    # print(f"Total BRP Pixels {len(arr_brp_vv)}")

    # Calculate min and max of the image data
    min_val = np.nanmin(sar_vv)
    max_val = np.nanmax(sar_vv)


    # Take random subset of arr_brp_vv with length equal to arr_water_vv
    if len(arr_brp_vv) > len(arr_water_vv):
        arr_brp_vv = np.random.choice(arr_brp_vv, len(arr_water_vv), replace=False)

    # print(f"Total Water Pixels {len(arr_water_vv)}")
    # print(f"Total BRP Pixels (random sub samples) {len(arr_brp_vv)}")

    sar_vv_ds.close()

    labels_water = np.ones(len(arr_water_vv))
    labels_brp = np.zeros(len(arr_brp_vv))

    features = np.concatenate((arr_water_vv, arr_brp_vv))
    labels = np.concatenate((labels_water, labels_brp))

    # Split the data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(features.reshape(-1, 1), labels, test_size=0.2, random_state=42)

    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train.ravel())

    # Predict the labels of the test set
    y_pred = model.predict(X_test)

    # Calculate the accuracy of the model
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy:", accuracy)

    def decision_function(x, model=model):
        if x < min_val or x > max_val:
            return np.inf
        return sigmoid(x * model.coef_[0] + model.intercept_[0]) - threshold


    initial_guess = -19
    try:
        threshold = fsolve(decision_function, initial_guess)
    except RuntimeError:
        print("Failed to find threshold for current data")
        threshold = [np.nan]

    print("Threshold for classification:", threshold[0])
    # Return both threshold and pixel count
    return threshold[0], len(arr_water_vv)


def average_threshold(threshold=0.7):

    all_thresholds = []
    all_pixel_counts = []

    for sar, water in mapping_dict.items():
        sar_path = os.path.join(sar_images_vv, sar)
        water_path = os.path.join(fp_waterpoly, water)

        if os.path.isfile(sar_path) and os.path.isfile(water_path):
            print(f'Processing: {sar}')
            threshold, pixel_count = get_threshold(water_path, sar_path, filename_brp_sample, threshold)
            all_thresholds.append(threshold)
            all_pixel_counts.append(pixel_count)
        else:
            print(f'Skipping: {sar} (No corresponding files found)')

    # Convert lists to numpy arrays for calculation
    all_thresholds = np.array(all_thresholds)
    all_pixel_counts = np.array(all_pixel_counts)

    # Calculate weighted average threshold
    average_threshold = np.average(all_thresholds, weights=all_pixel_counts)

    print(f"Average Threshold Value: {average_threshold}")
    return average_threshold



