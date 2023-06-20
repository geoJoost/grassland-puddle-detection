# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 11:23:17 2023

@author: Ageeth
"""
#```python
#import numpy as np
#from skimage.feature import graycomatrix, graycoprops
from skimage import io, color, img_as_ubyte

import matplotlib.pyplot as plt
#import gdal, gdalconst
import numpy as np
from skimage.feature import graycomatrix, graycoprops


glcm_array=np.load("output/glcm_array.npy")

sarfile = io.imread("input/Shapes/crane_kriging_raster_5.tif")
                    
                    #"input/Shapes/Coherence_VH_6day_20210104_quicklook.tif")
sarfile=sarfile.astype(int)

#filename = "//mnt//glaciology//RS2_20140101.jpg"
#outfilename = "//home//max//Documents//GLCM_contrast.tif"
#sarfile = gdal.Open(filename, gdalconst.GA_ReadOnly)

#sarraster = sarfile.ReadAsArray()
#sarraster is satellite image, testraster will receive texture
testraster = np.copy(sarfile)
testraster[:] = 0

for i in range(testraster.shape[0] ):
    print(i),
    for j in range(testraster.shape[1] ):

        #windows needs to fit completely in image
        if i <3 or j <3:
            continue
        if i > (testraster.shape[0] - 4) or j > (testraster.shape[0] - 4):
            continue

        #Calculate GLCM on a 7x7 window
        glcm_window = sarfile[i-3: i+4, j-3 : j+4]
        
        # unsigned integer type 
        
        
        glcm = graycomatrix(glcm_window, [1], [0], levels=253, symmetric = True, normed = True )

        #Calculate contrast and replace center pixel
        contrast = graycoprops(glcm, 'contrast')
        testraster[i,j]= contrast


sarplot = plt.imshow(testraster, cmap = 'gray')


#Calculate contrast and replace center pixel
homogeneity = graycoprops(glcm, 'homogeneity')
testraster[i,j]= homogeneity





image = img_as_ubyte(img)

bins = np.array([0, 16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 255]) #16-bit
inds = np.digitize(image, bins)

#max_value = inds.max()+1
matrix_coocurrence = graycomatrix(inds, [1], [0], levels=5, normed=False, symmetric=False)

# GLCM properties
def contrast_feature(matrix_coocurrence):
	contrast = graycoprops(matrix_coocurrence, 'contrast')
	return "Contrast = ", contrast

def dissimilarity_feature(matrix_coocurrence):
	dissimilarity = graycoprops(matrix_coocurrence, 'dissimilarity')	
	return "Dissimilarity = ", dissimilarity

def homogeneity_feature(matrix_coocurrence):
	homogeneity = graycoprops(matrix_coocurrence, 'homogeneity')
	return "Homogeneity = ", homogeneity

def energy_feature(matrix_coocurrence):
	energy = graycoprops(matrix_coocurrence, 'energy')
	return "Energy = ", energy

def correlation_feature(matrix_coocurrence):
	correlation = graycoprops(matrix_coocurrence, 'correlation')
	return "Correlation = ", correlation

def asm_feature(matrix_coocurrence):
	asm = graycoprops(matrix_coocurrence, 'ASM')
	return "ASM = ", asm

print(contrast_feature(matrix_coocurrence))
print(dissimilarity_feature(matrix_coocurrence))
print(homogeneity_feature(matrix_coocurrence))
print(energy_feature(matrix_coocurrence))
print(correlation_feature(matrix_coocurrence))
print(asm_feature(matrix_coocurrence))



import matplotlib.pyplot as plt

# Visualize the GLCM matrix
plt.imshow(glcm_array[:, :, 0, 0], cmap='gray')
plt.title('GLCM Matrix')
plt.colorbar()
plt.show()


