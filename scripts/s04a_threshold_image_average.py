import rasterio
import glob
import os

def calc_image_average():
    # To run the script for VV-polarization, change the line below to
    # image_filepaths = sorted(glob.glob(f"../data/thresh_stuff/training/vvsar/*.tif"))

    image_filepaths = sorted(glob.glob(f"../data/thresh_stuff/training/vhsar/*.tif"))

    for i in range(0, len(image_filepaths) - 1, 2):
        with rasterio.open(image_filepaths[i]) as src1, rasterio.open(image_filepaths[min(i + 1, len(image_filepaths) - 1)]) as src2:
            image1 = src1.read(1)
            image2 = src2.read(1)
            average_image = (image1 + image2) / 2
                
            profile = src1.profile
            avg_output_filepath = os.path.join(f"../data/thresh_stuff/output/averages", f'average_{i//2 + 1}.tif')
            os.makedirs(os.path.dirname(avg_output_filepath), exist_ok=True)
                
            with rasterio.open(avg_output_filepath, 'w', **profile) as dst:
                dst.write(average_image, 1)

    # Special case for the last image, paired with the previous one
    if len(image_filepaths) % 2 != 0:
        with rasterio.open(image_filepaths[-2]) as src1, rasterio.open(image_filepaths[-1]) as src2:
            image1 = src1.read(1)
            image2 = src2.read(1)
            average_image = (image1 + image2) / 2
                
            profile = src1.profile
            avg_output_filepath = os.path.join(f"../data/thresh_stuff/output/averages", f'average_{len(image_filepaths)//2 + 1}.tif')
            os.makedirs(os.path.dirname(avg_output_filepath), exist_ok=True)
                
            with rasterio.open(avg_output_filepath, 'w', **profile) as dst:
                dst.write(average_image, 1)


calc_image_average()