# -*- coding: utf-8 -*-
"""
Created:        20-06-2023
Last update on: 20-06-2023

Authors:
    Joost van Dalen
    Marnic Baars
    Petra Bardocz
    Ageeth de Haan
    Moses Okolo
    Daan Lichtenberg

Purpose:
    The following function executes the entire project created during the course 
    Geo-Information and Remote Sensing Integration at Wageningen University & Research.
    
    TODO: Finish text
    The main aim is to check if landowners
    
    
"""

import subprocess
import os
import geopandas as gpd

# Import individual scripts

# Define individual directories
data_dir = "data/"
output_dir = "output/"


# Define script paths
def run_script(script_name, script_args=None):
    # First join the script filepath together
    # script_fp = os.path.join("scripts/", script_name)
    
    # Prepare the command to run the script
    command = ["python", script_name]

    # If there are any arguments, add them to the command
    if script_args:
        command.extend(script_args)
    
    print(f"Running script: '{script_name}'\n")

    # Run the script and capture the output in real-time
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="scripts/")
    
    # Print the script's output
    print(process.stdout)

    # If there is any error, print it
    if process.stderr:
        print("Error:")
        print(process.stderr)
    print("\n")

    

# """
# Script #1: Filtering and joining of BRP & ANLB data
# TODO: ADD INFORMATION
# """
# # Run the script and capture the output
# run_script("s01_join_anlb_brp_dataframes.py")

# """
# Script #2: Filtering and clipping of Sentinel-1 images
# TODO: ADD INFORMATION
# """

# run_script("s02_clip_sar_images_to_parcel.py")

# """ Script #3
# This script does the following:
#     1. Extract SAR backscatter on ANLB + BRP parcels throughout the whole year from central overpass
#     2. Get statistics of both vector datasets as: min, mean, median, max and saves it as .csv
#     3. Repeat for five representative pixels which are inundated in 2021
#     4. Create and save this as time-series figure

# Comments:
#     - Ideally this script is ONLY used when more information on the problem is required as it takes >2 hours to run
#     - Output is not used in the rest of the model pipeline

# """

# run_script("s03_get_anlb_statistics_from_sar.py")

run_script("s04a_threshold_image_average.py")


run_script("s04c_thresholding.py", ["--threshold_value=0.7"])

run_script("s04d_validation.py", ["--threshold_value=0.7"])



