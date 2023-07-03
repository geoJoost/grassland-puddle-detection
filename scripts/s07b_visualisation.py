# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 15:00:16 2023

@author: Marnic
"""

import geopandas as gpd
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Read file
subsidised = gpd.read_file('data/07_fields_subsidised.shp')

# Change CRS to match with plotly
subsidised = subsidised.to_crs(4326)
percent = pd.read_csv("data/07_percent.csv", index_col=0)
binary = pd.read_csv("data/07_binary.csv", index_col=0)
# Make the map, add hoverdata and assign the color (yellow)
fig = px.choropleth_mapbox(subsidised, geojson=subsidised.geometry,
                           locations=subsidised.index, hover_data=subsidised.iloc[:, :-1],
                           color_discrete_sequence=['#ffb703'])

# Add OSM base map
fig.update_layout(mapbox_style="open-street-map")

# Center the map to the NL
fig.update_layout(mapbox=dict(
    center=dict(lat=52.1326, lon=5.2913),
    zoom=7))

# Increase width of the lines and give color (blue)
fig.update_traces(marker_line={'width': 2})
fig.update_traces(marker_line={'width': 8, 'color': 'rgb(2,48,71)'})

# Initialize the line graphs
fig_line1 = px.line()
fig_line2 = px.line()

# Initialize application
app = Dash(__name__)

# Set layout of the app
app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Puddle Dashboard", style={"text-align": "center"}),
                        html.P(
                            "This interactive tool leverages SAR VH (P0.5) data to visualise the puddle mapping project. The dashboard provides valuable insights into the time and extent of inundation in these areas. Through two dynamic graphs, you can explore the temporal patterns of puddle formation and track the percentage of land affected by inundation. The graphs update instantly when clicked, allowing you to delve deeper into specific time periods or regions of interest. With this comprehensive visualization, you can gain a better understanding of puddle dynamics and make informed decisions related to grassland management and conservation.",
                            style={"text-align": "justify"},
                        ),
                    ]
                )
            ],
            style={"width": "70%", "margin": "20px auto"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Puddle mapping", style={"text-align": "center"}),
                        dcc.Graph(id="map", figure=fig, style={"height": "700px"}),
                    ],
                    style={"text-align": "center", "width": "100%"},
                ),
            ],
            style={"width": "50%", "margin": "0 auto"},
        ),
        html.Div(
            [
                html.Div(
                    [html.H3("Inundation period", style={"margin-bottom": "0.5px"}),
                     dcc.Graph(figure=fig_line1, id="graph1")],
                    style={"text-align": "center", "width": "100%"},
                ),
                html.Div(
                    [html.H3("Inundation area of the plot", style={"margin-bottom": "0.5px"}),
                     dcc.Graph(figure=fig_line2, id="graph2")],
                    style={"text-align": "center", "width": "100%"},
                ),
            ],
            style={"width": "50%", "margin": "0 auto"},
        ),
    ],
    style={"display": "flex", "flex-wrap": "wrap"},
)


# Callback to update the graph based on a polygon click
@app.callback(
    Output('graph1', 'figure'),
    Output('graph2', 'figure'),
    Input('map', 'clickData')
)
def update_graphs(click):
    if click is None:
        # Return initial figures or empty figures if desired
        return {}, {}
    # Extract the clicked polygon's ID (or other identifying information) from clickData
    clicked_id = click['points'][0]['pointIndex']
    # Get the OBJECTID based on the index
    parcel_id = binary.loc[clicked_id, 'OBJECTID']
    # Filter the DataFrame based on the clicked polygon's ID and type ('binary')
    filtered_binary = binary[(binary['OBJECTID'] == parcel_id) & (binary['type'] == 'binary')]
    # Change the value column
    filtered_binary.rename(columns={'value': 'Class'}, inplace=True)
    # Create graph
    fig_binary = create_graph(filtered_binary)

    # Get the OBJECTID based on the index
    parcel_id = percent.loc[clicked_id, 'OBJECTID']
    # Filter the DataFrame based on the clicked polygon's ID and type ('percent')
    filtered_percent = percent[(percent['OBJECTID'] == parcel_id) & (percent['type'] == 'percentage')]
    # Change the value column
    filtered_percent.rename(columns={'value': 'Inundation [%]'}, inplace=True)
    # Create graph
    fig_percent = create_graph(filtered_percent)

    return fig_binary, fig_percent


# Function to create a graph based on a filtered DataFrame
def create_graph(df):
    if "Class" in df.columns:
        df.sort_values(by='Class', ascending=False)
        line = px.line(df, x='time', y='Class')
    else:
        df.sort_values(by='Inundation [%]', ascending=True)
        line = px.line(df, x='time', y='Inundation [%]')
    return line


# Run the app
app.run_server(debug=True)
