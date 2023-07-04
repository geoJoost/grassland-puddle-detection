import pandas as pd
import geopandas as gpd

#read csv file and transform to parcelId, time, value format 
df = pd.read_csv('../data/visualisation/vh-results/0.5-output.csv')
binary = pd.melt(
    df,
    id_vars='OBJECTID',
    value_vars=df.columns[1:],  # Exclude the first column 'OBJECTID'
    var_name='time',
    value_name='value')
del df

# Add type column and change the values
binary["type"] = "binary"
binary['value'] = binary['value'].replace({1: 'inundated', 0: 'dry'})
binary.to_csv("../data/visualisation/07_binary.csv")

#read csv file and transform to parcelId, time, value format 
df1 = pd.read_csv('../data/visualisation/vh-results/0.5-parcel_inundation.csv')
percent = pd.melt(
    df1,
    id_vars='OBJECTID',
    value_vars=df1.columns[1:],  # Exclude the first column 'OBJECTID'
    var_name='time',
    value_name='value')
del df1

# Add type column
percent["type"] = "percentage"
percent.to_csv("../data/visualisation/07_percent.csv")

del percent, binary

# read in the subsidised fields to preprocess
df2 = gpd.read_file("../data/visualisation/01_subsidised_field.shp")

#Only keeping necessarry columns and rename to English
subsidised = df2[['OBJECTID','CODE_BEHEE', 'year', 'fieldid', 'provincie', 'gemeente', 'woonplaats', 'regio', 'waterschap', 'geometry']].copy()
subsidised.rename(columns={'provincie': 'province', 'gemeente': 'muni', 'woonplaats': 'residence',
                    'regio': 'region', 'waterschap': 'waterboard'}, inplace=True)
del df2

# write to file
subsidised.to_file('../data/visualisation/07_fields_subsidised.shp')


