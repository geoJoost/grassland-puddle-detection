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
def run_script(script_name):
    # First join the script filepath together
    script_fp = os.path.join("scripts/", script_name)
    
    # Then we run the entire script
    # NOTE: this assumes the script is self-running
    print(f"Running script: '{script_name}'\n")
    
    # Run the script and capture the output in real-time
    process = subprocess.Popen(["python", script_fp], stdout=subprocess.PIPE, text=True)
    
    # Read and display the output while the script is running
    for line in process.stdout:
        print(line, end='')  # Print the output without adding an extra newline
    
    # Wait for the script to finish
    process.wait()
    
    print("\n")
    
    # Get the script's return code
    #return_code = process.returncode
    

"""
Script #1: Filtering and joining of BRP & ANLB data
TODO: ADD INFORMATION
"""
# Run the script and capture the output
run_script("s01_join_anlb_brp_dataframes.py")

"""
Script #2: Filtering and clipping of Sentinel-1 images
TODO: ADD INFORMATION
TODO: Add functions to run the script twice: for VV and VH
"""

run_script("s02_clip_sar_images_to_parcel.py")




















