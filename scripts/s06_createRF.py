# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 11:27:57 2023

@author: joost
"""

import os
import datetime
import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

filename_brp_sample ='output/03_brp_sample.shp'
fp_waterpoly = r'D:\grassland-puddle-detection\input\training_data\Water20210331.shp'


gdf_waterpoly = gpd.read_file(fp_waterpoly).set_crs('EPSG:28992').to_crs('EPSG:32631')



filename_sar_vv = r"D:/S1/20210329/Sigma0_dB_VV_20210329.tif"
filename_sar_vh = r"D:/S1/20210329/Sigma0_dB_VH_20210329.tif"

gdf_brp = gpd.read_file(filename_brp_sample)


sar_vv = rasterio.open(filename_sar_vv)  
sar_vh = rasterio.open(filename_sar_vh)

# %% Create VV-VH ratio 
def load_raster(filepath):
    with rasterio.open(filepath, driver='GTiff')  as src:
        return src.read(), src.meta

# Load both raster files as Np arrays
sar_vv, sar_meta = load_raster(filename_sar_vv)
sar_vh, sar_meta = load_raster(filename_sar_vh)

# Create masks to exclude np.nan values
mask1 = np.isnan(sar_vv)
mask2 = np.isnan(sar_vh)

# Apply the masks to the raster arrays
masked_raster1 = np.ma.masked_array(sar_vv, mask=mask1)
masked_raster2 = np.ma.masked_array(sar_vh, mask=mask2)

# Perform element-wise division between the masked arrays
ratio = masked_raster1 / masked_raster2


sar_ratio = sar_vv / sar_vh

fp_ratio = "D:/exports/VVVH_ratio_20210329.tif"

with rasterio.open(fp_ratio, "w", **sar_meta) as dest:
    dest.write(sar_ratio)

sar_vvvh_ratio = rasterio.open(fp_ratio)



def extract_raster_value(vector, sar):
    masked_image, masked_transform = mask(dataset=sar, shapes=vector['geometry'], crop=True, nodata = np.nan)
    
    
    raster_values = masked_image[0]
    
    raster_values_flat = raster_values.flatten()
    
    # Exclude values that are equal to 999
    raster_values_flat = raster_values_flat[raster_values_flat != np.nan]
    
    return raster_values_flat


arr_water_vv = extract_raster_value(gdf_waterpoly, sar_vv)
arr_water_vh = extract_raster_value(gdf_waterpoly, sar_vh)


arr_brp_vv = extract_raster_value(gdf_brp.sample(n=71, random_state=1), sar_vv)
arr_brp_vh = extract_raster_value(gdf_brp.sample(n=71, random_state=1), sar_vh)

arr_water_ratio = extract_raster_value(gdf_waterpoly, sar_vvvh_ratio)
arr_brp_ratio = extract_raster_value(gdf_brp.sample(n=71, random_state=1), sar_vvvh_ratio)




# Plot the graphs
bins = np.linspace(-30, 0, 100)
#bins = np.linspace(0, 1, 100)

plt.hist(np.log(arr_water_vh), bins, alpha=0.5, label='Water (n = 71)')
plt.hist(np.log(arr_brp_vh), bins, alpha=0.5, label='BRP (n = 71)')

plt.legend(loc='upper right')
plt.xlabel('Pixel Value [dB; VH]')
plt.ylabel('Frequency')
plt.title('Histogram of backscatter [dB] in March 2021')

plt.show()

    



























gdf_trainpoly = gpd.read_file("input/training_data/Water20210331.shp")

# Conduct a train-test split
gdf_train, gdf_test = train_test_split(gdf_trainpoly, test_size=0.2, random_state=1, shuffle=True)
            



