# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 11:35:09 2023

@author: joost
"""

import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.model_selection import train_test_split
from rasterstats import zonal_stats
import matplotlib.pyplot as plt

# %% Read in files
# First load in the ANLB-subsidy data
gdf_anlb = gpd.read_file("output/ANLB_filtered.shp").to_crs('EPSG:32631')

# Afterwards load in two Sentinel-1 images
# One before 1feb, and one afterwards
# To compare before-after inundation of grasslands
# Load raster file
def load_raster(filepath):
    with rasterio.open(filepath, driver='GTiff')  as src:
        return src.read(1), src.transform

# Load Sentinel-1 images and extract affine transforms
sar_jan, transform_jan = load_raster('output/Sigma0_dB_VV_20210128.tif')
sar_feb, transform_feb = load_raster('output/Sigma0_dB_VV_20210209.tif')


# Conduct a train-test split
gdf_train, gdf_test = train_test_split(gdf_anlb, test_size=0.2, random_state=1, shuffle=True)

# Export testing dataset as shapefile
# Since we will not use anymore until script #5
gdf_test.to_file("output/03_anlb_testdata.shp")

# %% Extract backscatter values from both Sentinel images
def retrieve_stats(raster, polygon, affine, stats_lst = ['count', 'min', 'mean', 'max', 'median']):
    
    # Define dataframe for saving values later
    df_stats = pd.DataFrame(index = np.arange(1), columns = stats_lst)
    
    # Retrieve all the zonal statistics first
    stats =  zonal_stats(polygon, raster, affine = affine, stats = stats_lst)
    
    # Retrieve single value for each individual statistics
    # and save into the dataframe
    for i, stat in enumerate(stats_lst):
        # Index to specific statistic (e.g., 'count', 'min')
        stat_curr = stats_lst[i]
        
        # Sum up the statistic value for all pixels found
        # and append to the dataframe
        df_stats[stat_curr] = round(stats[i][stat_curr], 2)
        
    return df_stats

# Define statistics we want to retrieve
stats_lst = ['count', 'min', 'mean', 'max', 'median']

# Perform zonal statistics
df_jan = retrieve_stats(sar_jan, gdf_anlb, transform_jan, stats_lst)
df_feb = retrieve_stats(sar_feb, gdf_anlb, transform_feb, stats_lst)

# Concatenate the dataframes and assign new index names
df_combined = pd.concat([df_jan, df_feb], keys=['jan', 'feb'])

# Remove the zeros from the original index
df_combined.index = df_combined.index.droplevel(1)

# Print the combined dataframe
print(df_combined)

# %% Create plot
# Flip the raster image vertically
raster_jan = sar_jan
#np.flipud(sar_jan)

# Get the extent of the vector data
extent = gdf_anlb.total_bounds

# Plot the raster image
plt.figure(figsize=(10, 5))
plt.imshow(raster_jan, cmap='gray', extent=[extent[0], extent[2], extent[1], extent[3]])

# Overlay the vector file
gdf_anlb.plot(ax=plt.gca(), facecolor='none', edgecolor='red')

# Set appropriate aspect ratio
plt.gca().set_aspect('equal')

# Add title and axis labels
plt.title('January SAR Image with Vector Overlay')
plt.xlabel('X')
plt.ylabel('Y')

# Show the plot
plt.tight_layout()
plt.show()



















