# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 11:35:09 2023

@author: joost
"""

import os
import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
from rasterstats import zonal_stats
import matplotlib.pyplot as plt
import seaborn as sns

# %% Read in files
# First load in the ANLB-subsidy and BRP data
gdf_anlb = gpd.read_file("output/01_ANLB_filtered.shp").to_crs('EPSG:32631')

filename_brp_sample ='output/03_brp_sample.shp'

# Repeat for the BRP data
if os.path.exists(filename_brp_sample):
    print("BRP sampled dataset already exists")
    gdf_brp_clip = gpd.read_file(filename_brp_sample)
else:
    print("BRP sampled dataset does not exist yet")
    # Read in BRP data
    gdf_brp = gpd.read_file("data\Shapes\gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp").to_crs('EPSG:32631')
    
    # Following values are found: 'Grasland', 'Bouwland', 'Overige', 'Natuurterrein', 'Braakland'
    # and we only want to keep the grasslands for most realistic comparison
    gdf_brp_filtered = gdf_brp[gdf_brp['cat_gewasc'] == 'Grasland']
    
    # Randomly select 70,000 (about 10% of original sample, N=511,031) polygons from the BRP data
    gdf_brp_sample = gdf_brp.sample(n=50000, random_state=1)

    # Conduct a reverse clip to make sure both vector files do not overlap
    gdf_brp_clip = gpd.overlay(gdf_brp_sample, gdf_anlb, how='difference')
    
    # Export the BRP sampled dataset to file
    gdf_brp_clip.to_file(filename_brp_sample)
    
    print("BRP sampled dataset created \n")


# %% Define equations
def create_vector(extent):
    # Extract the individual coordinates from the extent list
    xmin, ymin, xmax, ymax = extent
    
    # Create the polygon
    polygon = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
    
    # Convert the polygon to a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs='EPSG:4326')
    
    return gdf

""" 
This function does the following things:
    1. Load .tif files as Numpy arrays
    2. And returns transform required to georeference the array with the vector data
"""
# Load raster files and add the transform
def load_raster(filepath):
    with rasterio.open(filepath, driver='GTiff')  as src:
        return src.read(1), src.transform

"""
This function does the following things:
    1. Create a empty DataFrame
    2. Enumerates over all sub-folders to retrieve SAR VV-backscatter images
    3. Retrieve statistics using zonal_stats from rasterstats
"""
# Extract backscatter values from both Sentinel images
def retrieve_stats(raster, polygon, affine, stats_lst = ['count', 'min', 'mean', 'max', 'median']):
    
    # Define dataframe for saving values later
    df_stats = pd.DataFrame(index = np.arange(1), columns = stats_lst)
    
    # Retrieve all the zonal statistics first
    stats =  zonal_stats(polygon, raster, affine = affine, stats = stats_lst)
    
    # Define empty dictionary for appending values
    stat_map = {}

    # Retrieve single value for each individual statistics
    # and save into the dataframe
    for i, stat in enumerate(stats_lst):
        # Index to specific statistic (e.g., 'count', 'min')
        stat_curr = stats_lst[i]
        
        # First get the desired statistic from the dictionary within the list
        # Then append the list of values into a map
        # And then retake the same statistic (e.g., minimum of minimum values, mean of the mean values)
        # Return into DataFrame
        specific_stat_lst = [d[stat_curr] for d in stats]
        # Preprocess the list by replacing None values with NaN
        processed_list = [value if value is not None else np.nan for value in specific_stat_lst]

        # Convert the processed list to a NumPy array
        my_array = np.array(processed_list)
        
        stat_map[stat_curr] = my_array

        # Take statistic of statistic values (e.g., max of max)
        if i == 0:   # Count column
            pass
        elif i == 1: # Minmum column
            df_stats[stat_curr] = round(np.nanmin(stat_map[stat_curr]), 2)
        elif i == 2: # Mean column
            df_stats[stat_curr] = round(np.nanmean(stat_map[stat_curr]), 2)
        elif i == 3: # Maximum column
            df_stats[stat_curr] = round(np.nanmax(stat_map[stat_curr]), 2)
        elif i == 4: # Median column
            df_stats[stat_curr] = round(np.nanmedian(stat_map[stat_curr]), 2)

    return df_stats

"""
This function does the following things:
    1. Through a for-loop load each individual SAR image from Sentinel-1
    2. Using a defined statistics list retrieve minimum, mean, maximum, and median backscatter values (dB)
    3. With tune fcntion "retrieve_stats" extract statistics based on vector set (either ANLB or BRP)
    4. Append statistics into a list and repeat the loop until all SAR statsitics are extracted
"""  
def retrieve_zonal_statistics(vector, vector_name: str):
    # Define empty list to merge dataframes later on
    df_lst, df_combined = [], []

    # Define data folder
    # NOTE: we take the original SAR images to cover backscatter values in the BRP parcels as well
    rootdir = "data\S1"  # Specify the directory path here 

    # Loop over the entire dir
    for i, item in enumerate(sorted(os.listdir(rootdir))):
        # Make sure we only take folders and not individual files (e.g., shapefiles)
        item_path = os.path.join(rootdir, item) 
        
        # We skip every other folder to guarantee we only take central overpasses
        if os.path.isdir(item_path) and i % 2 == 0:
            
            # Since we now identified the correct sub-folder
            # we can index for the desired .tif files
            for filename in os.listdir(item_path):
                # Index for files named "Sigma0_dB_VV_20210104.tif", and ignore "Sigma0_dB_VV_20210104_quicklook.tif"
                if filename.endswith(".tif") and "VV" in filename and not ("Coherence" in filename or "quicklook" in filename):
                    print(f"Working on image: {filename} with {vector_name}")
                    
                    file_path = os.path.join(item_path, filename)
                    
                    # Reset the statistics dataframe for each image
                    df_stats = []
                    
                    # Load in the rasters as Numpy array
                    # Get transformation to georeference the array with the ANLB data
                    sar_img, transform_img = load_raster(file_path)
                    
                    # Define statistics we want to retrieve
                    stats_lst = ['count', 'min', 'mean', 'max', 'median']
                    
                    # Perform zonal statistics
                    df_stats = retrieve_stats(sar_img, vector, transform_img, stats_lst)
                    
                    # Split the entire name ("Sigma0_dB_VV_20210128.tif") to only keep "20210128"
                    date = filename.split('_')[-1].split('.')[0].strip()
                    
                    # Add date into new column
                    df_stats['date'] = date
                    
                    # Convert 'date' column to datetime
                    df_stats['date'] = pd.to_datetime(df_stats['date'])
                    
                    # Append the DataFrame to the list
                    df_lst.append(df_stats)
            
            
    # Merge dataframes together
    # Concatenate the dataframes and assign new index names
    df_combined = pd.concat(df_lst)
    
    # Find the minimum date in the column
    min_date = pd.to_datetime(pd.Series('2021-01-01'))
    
    # Calculate the number of days passed since the 1st of January
    df_combined['days_since_jan1'] = (df_combined['date'] - min_date).dt.days + 1
    
    return df_combined

# %% Retrieve zonal statistics for the ANLB and BNRP data
# Assign filenames for checking if the .csv exists, and for creating a new one if needed
filename_anlb = "output/03_anlb_statistics.csv"
filename_brp = "output/03_brp_statistics.csv"

# Check if the ANLB statistics file already exists
if os.path.exists(filename_anlb):
    df_anlb = pd.read_csv(filename_anlb)
    print("The file already exists.")
else:
    df_anlb = retrieve_zonal_statistics(gdf_anlb, "ANLB")
    df_anlb.to_csv(filename_anlb, index=False)

# Repeat for the BRP data
if os.path.exists(filename_brp):
    df_brp = pd.read_csv(filename_brp)
    print("The file already exists.")
else:
    df_brp = retrieve_zonal_statistics(gdf_brp_clip, "BRP")
    df_brp.to_csv(filename_brp, index=False)


# %% Plot time-series graph

fig, ax = plt.subplots(figsize = (12, 8))

""" ANLB DATA """
# Plot the mean value retrieved from the ANLB polygons
anlb_col = '#219ebc'

sns.lineplot(x='days_since_jan1', y='mean', data=df_anlb, 
             color = anlb_col, label=r'$\mu$ of ANLB ($\mathit{N}$ = 481)', linestyle = '--')

# Shade the area in-between using the minimum and maximum backscatter values
anlb_min = df_anlb['min']
anlb_max = df_anlb['max']

""" BRP DATA """
brp_col = '#fb8500'

# Create simple line plot
sns.lineplot(x='days_since_jan1', y='mean', data=df_brp, 
             color = brp_col, label='$\mu$ of BRP ($\mathit{n}$ = 50,000)', linestyle = '--')

# Shade the area in-between using the minimum and maximum backscatter values
brp_min = df_brp['min']
brp_max = df_brp['max']


""" SELECTED PIXELS """
pix_col = '#780000'

# But also for newly created pixels to get accurate pixel-level statistics
# Define the extent coordinates as a single list
extent_lst = [
    [5.4898417317950887, 53.1597811149882418, 5.4903768596555151, 53.1599419888393143], #1 - Friesland
    [5.5106949090941608, 53.1475020995522840, 5.5108963654507210, 53.1476136227111553], #2 - Friesland
    [5.0220660063737572, 52.4272351063809054, 5.0222749930232906, 52.4273773226332978], #3 - Noord-Holland
    [4.9326604056431744, 51.9831009252632583, 4.9328957684955537, 51.9832394405185951], #4 - Utrecht
    [5.7714493650383663, 51.9296325083013386, 5.7716859400861100, 51.9297904830481514]  #5 - Gelderland
    ]

# Loop through the extent list
# Convert to GeoDataFrame
# Extract statistics
# And plot as line graph
for i, extent in enumerate(extent_lst):
    gdf_pix = create_vector(extent).to_crs('EPSG:32631')
    
    df_pix = retrieve_zonal_statistics(gdf_pix, f"Representative pixel #{i}")
    
    line = sns.lineplot(x='days_since_jan1', y='mean', data=df_pix, 
                        color = pix_col, linestyle = ':', alpha=0.5,
                        label='Representative pixels in ANLB-parcel ($\mathit{n}$ = 5)' if i < 2 else None)


""" MIN-MAX FILLS"""
plt.fill_between(df_anlb['days_since_jan1'], anlb_min, anlb_max, 
                color = anlb_col, alpha=0.2, label= "Min-Max of ANLB")
ax.fill_between(df_brp['days_since_jan1'], brp_min, brp_max, 
                color = brp_col, alpha=0.2, label='Min-Max of BRP')

# remove margin spaces
plt.margins(0, 0)

# add label to the axis and label to the plot
ax.set(xlabel ="Day of the year", 
       ylabel = "VV-backscatter [dB]")#,

ax.set_title("Temporal variations of backscatter in different parcels", fontsize=16)

# Despine the plot
sns.despine(top=True, right=True, left=True, bottom=True)

# Add grid lines
ax.grid(color='gray', linestyle='--', linewidth=0.5)
ax.grid(True)

# Move the legend below the plot
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)

# Create two vertical lines indicating the 15th of February up to the 15th of June 
# Corresponding to subsidy code 3C
x_ticks = [43, 165]
for x in x_ticks:
    ax.axvline(x=x, color='red', linestyle='--')
    
# Calculate the midpoint between the two X-tick positions
midpoint = sum(x_ticks) / len(x_ticks)

# Add text at the midpoint
ax.text(midpoint, ax.get_ylim()[1] * 0.5, "Inundation Period (3c)", ha='center', fontsize=14)


plt.tight_layout()
#plt.show()

# Save the figure
plt.savefig("output/03_timeseries_backscatter.png")
