# -*- coding: utf-8 -*-
"""
Created on Mon Jun 19 10:03:42 2023

@author: Ageeth
"""

from osgeo import gdal,osr
import numpy as np
from scipy.interpolate import RectBivariateSpline
from numpy.lib.stride_tricks import as_strided as ast
import dask.array as da
from joblib import Parallel, delayed, cpu_count
import geopandas as gpd
from skimage.feature import graycomatrix, graycoprops
#normalize
from sklearn.preprocessing import MinMaxScaler
import rasterio

def im_resize(im,Nx,Ny):
    '''
    resize array by bivariate spline interpolation
    '''
    ny, nx = np.shape(im)
    xx = np.linspace(0,nx,Nx)
    yy = np.linspace(0,ny,Ny)

    try:
        im = da.from_array(im, chunks=1000)   #dask implementation
    except:
        pass

    newKernel = RectBivariateSpline(np.r_[:ny],np.r_[:nx],im)
    return newKernel(yy,xx)

def p_me(Z): #win is deleted in the parameter
    '''
    loop to calculate greycoprops
    '''
    try:
        glcm = graycomatrix(Z, [1], [0], 256, symmetric=True, normed=True)
                                #[0, np.pi/4, np.pi/2, 3*np.pi/4]
        cont = graycoprops(glcm, 'contrast')
        diss = graycoprops(glcm, 'dissimilarity')
        homo = graycoprops(glcm, 'homogeneity')
        eng = graycoprops(glcm, 'energy')
        corr = graycoprops(glcm, 'correlation')
        ASM = graycoprops(glcm, 'ASM')
        return (cont, diss, homo, eng, corr, ASM)
    except:
        return (0,0,0,0,0,0)


def read_raster(in_raster):
    in_raster=in_raster
    ds = gdal.Open(in_raster)
    data = ds.GetRasterBand(1).ReadAsArray()
    data[data==999] = np.nan    
    # normalize raster
    scaler = MinMaxScaler(feature_range=(1, 255))
    normalized_raster = scaler.fit_transform(data.astype('float64'))
    normalized_raster = normalized_raster.astype('uint8')
    #normalized_raster[normalized_raster==np.nan] = 0
    print("normalize_raster") 
    

    gt = ds.GetGeoTransform()
    xres = gt[1]
    yres = gt[5]

    # get the edge coordinates and add half the resolution 
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
    ymin = gt[3] + (yres * ds.RasterYSize) + yres * 0.5
    ymax = gt[3] - yres * 0.5
    del ds
    # create a grid of xy coordinates in the original projection
    xx, yy = np.mgrid[xmin:xmax+xres:xres, ymax+yres:ymin:yres]
    print("read raster")
    return normalized_raster, xx, yy, gt #data, xx, yy, gt

def norm_shape(shap):
   '''
   Normalize numpy array shapes so they're always expressed as a tuple,
   even for one-dimensional shapes.
   '''
   try:
      i = int(shap)
      return (i,)
   except TypeError:
      # shape was not a number
      pass

   try:
      t = tuple(shap)
      return t
   except TypeError:
      # shape was not iterable
      pass

   raise TypeError('shape must be an int, or a tuple of ints')

def sliding_window(a, ws, ss = None, flatten = True):
    '''
    Source: http://www.johnvinyard.com/blog/?p=268#more-268
    Parameters:
        a  - an n-dimensional numpy array
        ws - an int (a is 1D) or tuple (a is 2D or greater) representing the size 
             of each dimension of the window
        ss - an int (a is 1D) or tuple (a is 2D or greater) representing the 
             amount to slide the window in each dimension. If not specified, it
             defaults to ws.
        flatten - if True, all slices are flattened, otherwise, there is an 
                  extra dimension for each dimension of the input.

    Returns
        an array containing each n-dimensional window from a
    '''      
    if None is ss:
        # ss was not provided. the windows will not overlap in any direction.
        ss = ws
    ws = norm_shape(ws)
    ss = norm_shape(ss)
    # convert ws, ss, and a.shape to numpy arrays
    ws = np.array(ws)
    ss = np.array(ss)
    shap = np.array(a.shape)
    # ensure that ws, ss, and a.shape all have the same number of dimensions
    ls = [len(shap),len(ws),len(ss)]
    if 1 != len(set(ls)):
        raise ValueError(\
        'a.shape, ws and ss must all have the same length. They were %s' % str(ls))

    # ensure that ws is smaller than a in every dimension
    if np.any(ws > shap):
        raise ValueError(\
        'ws cannot be larger than a in any dimension.\
     a.shape was %s and ws was %s' % (str(a.shape),str(ws)))

    # how many slices will there be in each dimension?
    newshape = norm_shape(((shap - ws) // ss) + 1)


    # the shape of the strided array will be the number of slices in each dimension
    # plus the shape of the window (tuple addition)
    newshape += norm_shape(ws)


    # the strides tuple will be the array's strides multiplied by step size, plus
    # the array's strides (tuple addition)
    newstrides = norm_shape(np.array(a.strides) * ss) + a.strides
    a = ast(a,shape = newshape,strides = newstrides)
    if not flatten:
        return a
    # Collapse strided so that it has one more dimension than the window.  I.e.,
    # the new array is a flat list of slices.
    meat = len(ws) if ws.shape else 0
    firstdim = (np.product(newshape[:-meat]),) if ws.shape else ()
    dim = firstdim + (newshape[-meat:])
    # remove any dimensions with size 1
    dim = tuple(filter(lambda i : i != 1,dim)) ##### here a tuple is made to try to solve the error

    return a.reshape(dim), newshape

def CreateRaster(xx,yy,std,gt,proj,driverName,outFile):  
    '''
    Exports data to GTiff Raster
    '''
    std = np.squeeze(std)
    std[np.isinf(std)] = -99
    driver = gdal.GetDriverByName(driverName)
    rows,cols = np.shape(std)
    ds = driver.Create( outFile, cols, rows, 1, gdal.GDT_Float32)      
    if proj is not None:  
        ds.SetProjection(proj.ExportToWkt()) 
    ds.SetGeoTransform(gt)
    ss_band = ds.GetRasterBand(1)
    ss_band.WriteArray(std)
    ss_band.SetNoDataValue(-99)
    ss_band.FlushCache()
    ss_band.ComputeStatistics(False)
    print("create raster")
    del ds


#Stuff to change
# =============================================================================
# 
# parcels = gpd.read_file("input/Shapes/gewaspercelen_2021_S2Tiles_GWT_BF12_AHN2.shp")
# 
# # Apply the filters to the DataFrame
# parcels = parcels.loc[(parcels['provincie'] == 'Friesland') & (parcels['cat_gewasc'] == 'Grasland') | 
#                       (parcels['provincie'] == 'Groningen') & (parcels['cat_gewasc'] == 'Grasland')]
# parcels = parcels.to_crs(epsg=32631)
# 
# with rasterio.open("data/averages/average_1.tif") as src:
#     out_image, out_transform = rasterio.mask.mask(src, parcels.geometry, crop=True, nodata=999, all_touched = True)
#     out_meta = src.meta
# 
# out_meta.update({"driver": "GTiff",
#                   "height": out_image.shape[1],
#                   "width": out_image.shape[2],
#                   "transform": out_transform})
# 
# 
# with rasterio.open("data/averages/cropped_average_1.tif", "w", **out_meta) as dest:
#     dest.write(out_image)
# =============================================================================


win_sizes = [7]
for win_size in win_sizes[:]:   
    in_raster = "data/averages/average_1.tif"#Path to input raster
    win = win_size
    meter = str(win/4)

    #Define output file names
    contFile = "output/average_1_contFile.tif"
    dissFile = "output/average_1_dissFile.tif"
    homoFile = "output/average_1_homoFile.tif"
    energyFile = "output/average_1_energyFile.tif"
    corrFile = "output/average_1_corrFile.tif"
    ASMFile = "output/average_1_ASMFile.tif"



    merge, xx, yy, gt = read_raster(in_raster)

    #merge[np.isnan(merge)] = 0
###
    Z,ind = sliding_window(merge,(win,win),(win,win))

    Ny, Nx = np.shape(merge)

    w = Parallel(n_jobs = cpu_count(), verbose=0)(delayed(p_me)(Z[k]) for k in list(range(len(Z))))#xrange(len(Z)))

    cont = [a[0] for a in w]
    diss = [a[1] for a in w]
    homo = [a[2] for a in w]
    eng  = [a[3] for a in w]
    corr = [a[4] for a in w]
    ASM_  = [a[5] for a in w]
    
    #cont = [np.mean(array) for array in cont]
    #diss = [np.mean(array) for array in diss]
    #homo = [np.mean(array) for array in homo]
    #eng = [np.mean(array) for array in eng]
    #corr = [np.mean(array) for array in corr]
    #ASM_ = [np.mean(array) for array in ASM_]
    
    #Reshape to match number of windows
    plt_cont = np.reshape(cont , ( ind[0], ind[1] ) )
    plt_diss = np.reshape(diss , ( ind[0], ind[1] ) )
    plt_homo = np.reshape(homo , ( ind[0], ind[1] ) )
    plt_eng = np.reshape(eng , ( ind[0], ind[1] ) )
    plt_corr = np.reshape(corr , ( ind[0], ind[1] ) )
    plt_ASM =  np.reshape(ASM_ , ( ind[0], ind[1] ) )
    del cont, diss, homo, eng, corr, ASM_

    #Resize Images to receive texture and define filenames
    contrast = im_resize(plt_cont,Nx,Ny)
    contrast[merge==0]=np.nan
    dissimilarity = im_resize(plt_diss,Nx,Ny)
    dissimilarity[merge==0]=np.nan    
    homogeneity = im_resize(plt_homo,Nx,Ny)
    homogeneity[merge==0]=np.nan
    energy = im_resize(plt_eng,Nx,Ny)
    energy[merge==0]=np.nan
    correlation = im_resize(plt_corr,Nx,Ny)
    correlation[merge==0]=np.nan
    ASM = im_resize(plt_ASM,Nx,Ny)
    ASM[merge==0]=np.nan
    del plt_cont, plt_diss, plt_homo, plt_eng, plt_corr, plt_ASM


    del w,Z,ind,Ny,Nx

    driverName= 'GTiff'    
    epsg_code=32631
    proj = osr.SpatialReference()
    proj.ImportFromEPSG(epsg_code)

    CreateRaster(xx, yy, contrast, gt, proj,driverName,contFile) 
    CreateRaster(xx, yy, dissimilarity, gt, proj,driverName,dissFile)
    CreateRaster(xx, yy, homogeneity, gt, proj,driverName,homoFile)
    CreateRaster(xx, yy, energy, gt, proj,driverName,energyFile)
    CreateRaster(xx, yy, correlation, gt, proj,driverName,corrFile)
    CreateRaster(xx, yy, ASM, gt, proj,driverName,ASMFile)

    del contrast, merge, xx, yy, gt, meter, dissimilarity, homogeneity, energy, correlation, ASM