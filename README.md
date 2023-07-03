# Precision mapping of inundation

Python script to extract shallow inundation in meadow bird subsidy parcels using Sentinel-1 images from 2021.

The script was commissioned by Wageningen Environmental Research (WENR) - Team Earth Informatics. The script was developed by members of the RGIC23-10 group:

Marnic Baars, Petra Bardocz, Joost van Dalen, Ageeth de Haan, Daan Lichtenberg and Moses Okolo

## Workflow/Order of Execution

```mermaid
graph TB
A[s01] -- Join ANLB and BRP data --> B((s02))
A --> C(s03)
C -- Get Statistics --> B
B -- Clip SAR data --> D{s04}
D --> E[s04a] -- Get Image Average --> F[s04c] -- Get Threshold Value --> G[s04b];
F -- Binary Classification ----> H[s04d]
H -- Validation --> I[s05]
I -- Visualization --> J[s06]
```

## Documentation

The following section outlines what each script does and what modifications users might want to make.

**N.B:** Calling the `main.py` script runs the entire workflow explained below

### s01_preprocess_vector_data.py

This script

- Filters the ANLb shapefile to 3a-d subsidy parcels and joins them with corresponding BRP parcels.

- Creates a dataset of 1000 randomly sampled BRP parcels which are dry grass only.

**Output Folder(s)**

- _../output_

### s02_preprocess_raster_data.py

This script

- Filters out the central pass S1 backscatter images until August 20 for VV and VH polarisations

- Clips SAR images to the shapefile created in s01, which included the merged ANLb parcels and the 1000 BRP grassland parcels. By default, the scipt clips to mixed pixels, i.e. pixels that lie on the border of parcels are also included.

- Selects the SAR images closest in date to validated water polygon data derived from S2 images.

Optional parts:

- Pure pixel clipping: In case SAR images have to be clipped to only pixels which lie completely within the perimeter of the parcels.

**Output Folder(s)**

- _../output_

### s03_get_anlb_statistics_from_sar.py

This script

- Plots the backscatter timeseries of dry grass parcels, inundated parcels, and 5 representative inundated pixels

(OPTIONAL) TO DO:

The script either runs on the VV or the VH images. Change polarisation in script based on what is needed.

**Output Folder(s)**

- _../output_

### s04a_threshold_image_average.py

This script contains the logic for calculating the average of all the images in an input folder. It employs a moving average of two so for example if your input folder contains four images. An output of two images should be expected where output 1 is the average of images 1 and 2 and output 2 is the average of images 3 and 4.

**Output Folder(s)**

- _../data/thresholding_data/output/averages_

### s04b_get_threshold_value.py

This script contains the logic for calculating the optimal threshold value used in the thresholding algorithm. It uses a simple logistic regression model.

**Output Folder(s)**

- _None_

### s04c_thresholding.py

The script takes as input a series of satellite images and applies a threshold to convert them into binary images, where pixels are categorized as either "water" or "non-water" based on their backscatter values.

**Output Folder(s)**

- _../output_
- _../output/running_average_
- _../output/binary_

### s04d_validation.py

This script validates the accuracy of the thresholding algorithm built in `s04c_thresholding.py`.

**Output Folder(s)**

1.  _../output_
