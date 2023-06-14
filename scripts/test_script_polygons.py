# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 15:23:26 2023

@author: Ageeth
"""
from osgeo import gdal, ogr

# Specify the input raster file
input_raster = "input/Shapes/crane_kriging_raster_5.tif"

# Specify the output shapefile
output_shapefile = "output/mixed_parcels.shp"

def vectorize_raster(input_raster,output_shapefile):
    # Open the raster file
    ds = gdal.Open(input_raster)

    # Get the raster layer (there is only 1 layer in the raster files)
    band = ds.GetRasterBand(1)
    
    # Create a new shapefile
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds_out = driver.CreateDataSource(output_shapefile)

    # Create a new layer in the shapefile
    layer = ds_out.CreateLayer("vector_layer", geom_type=ogr.wkbPolygon)
    
    # Add a single field to the layer (optional)
    field_defn = ogr.FieldDefn("raster_value", ogr.OFTInteger)
    layer.CreateField(field_defn)
    
    # Convert the raster to vector polygons
    gdal.Polygonize(band, None, layer, 0, [], callback=None)
    
    # Close the shapefile and raster file
    #ds_out = None
    #ds = None
    
    print("Raster to vector conversion complete.")

vectorize_raster(input_raster,output_shapefile)
