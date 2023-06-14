#!/bin/bash
# Geoscripting 2023
# Oxbow Gang:
              # Joost van Dalen
              # 
              # 
              # 
              # 
# Identification of shallow puddles in Friesland, the Netherlands

# Create a data and an output folder
mkdir -p data || exit 1 
mkdir -p input || exit 1
mkdir -p output || exit 1

# MANUALLY create a Python environment
# Use conda env create --file createEnv.yaml
source activate geo_env

echo "Running the scripts"
# Run script 1 to join ANLB and BRP dataframes
python scripts/01_join_anlb_brp_dataframes.py

