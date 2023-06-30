import pandas as pd
import geopandas as gpd

#read csv file and transform to parcelId, time, value format 
df = pd.read_csv('input/output.csv')
binary = pd.melt(
    df,
    id_vars='parcelId',
    value_vars=df.columns[1:],  # Exclude the first column 'parcelId'
    var_name='time',
    value_name='value')
del df

# Add type column
binary["type"] = "binary"
binary['value'] = binary['value'].replace({1: 'inundated', 0: 'dry'})

#read csv file and transform to parcelId, time, value format 
df1 = pd.read_csv('input/parcel_inundation.csv')
percent = pd.melt(
    df1,
    id_vars='parcelId',
    value_vars=df1.columns[1:],  # Exclude the first column 'parcelId'
    var_name='time',
    value_name='value')
del df1

# Add type column
percent["type"] = "percentage"

# append the two dataframes
percent_binary = pd.concat([percent, binary], ignore_index=True)
del percent, binary

df2 = gpd.read_file("output/01_subsidised_field.shp")
#Add column to match with parcelId
df2['parcelId'] = df2['fieldid'].fillna(df2['OBJECTID'])

#Only keeping necessarry columns
subsidised = df2[['parcelId','CODE_BEHEE', 'year', 'fieldid', 'provincie', 'gemeente', 'woonplaats', 'regio', 'waterschap', 'geometry']]
del df2

subsidised.to_file('data/07_fields_subsidised.shp')
percent_binary.to_csv("data/07_percent_binary.csv")

