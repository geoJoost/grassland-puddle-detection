# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 15:00:16 2023

@author: Marnic
"""

import dash
import plotly.graph_objects as go
import geopandas as gpd
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.io as io

subsidised = gpd.read_file('data/07_fields_subsidised.shp')

subsidised = subsidised.to_crs(4326)
data = pd.read_csv("data/07_percent_binary.csv", index_col=0)
subsidised['parcelId'] = subsidised['parcelId'].astype(int)

fig = px.choropleth_mapbox(subsidised, geojson= subsidised.geometry,
                    locations=subsidised.index, hover_data=subsidised.iloc[:, :-1], color_discrete_sequence=['#ffb703'])

#fig.update_layout(showlegend=False)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(mapbox=dict(
    center=dict(lat=52.1326, lon=5.2913),
    zoom=7))

fig.update_traces(marker_line={'width': 2})
fig.update_traces(marker_line={'width': 8, 'color': 'rgb(2,48,71)'})

fig_line1 = px.line()

fig_line2 = px.line()

app = Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Puddle Dashboard", style={"text-align": "center"}),
                        html.P(
                            "This interactive tool leverages SAR data to map puddles in grasslands. The dashboard provides valuable insights into the time and extent of inundation in these areas. Through two dynamic graphs, you can explore the temporal patterns of puddle formation and track the percentage of land affected by inundation. The graphs update instantly when clicked, allowing you to delve deeper into specific time periods or regions of interest. With this comprehensive visualization, you can gain a better understanding of puddle dynamics and make informed decisions related to grassland management and conservation.",
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
                    [html.H3("Inundation period", style={"margin-bottom": "0.5px"}), dcc.Graph(figure=fig_line1, id="graph1")],
                    style={"text-align": "center", "width": "100%"},
                ),
                html.Div(
                    [html.H3("Inundation percentage [%]", style={"margin-bottom": "0.5px"}), dcc.Graph(figure=fig_line2, id="graph2")],
                    style={"text-align": "center", "width": "100%"},
                ),
            ],
            style={"width": "50%", "margin": "0 auto"},
        ),
    ],
    style={"display": "flex", "flex-wrap": "wrap"},
)




# @app.callback(
#     Output(component_id='my-output', component_property='children'),
#     Input(component_id='map', component_property='clickData')
# )
# def update_output_div(input_value):
#     return f'Output: {input_value}'


@app.callback(
    Output('graph1', 'figure'),
    Output('graph2', 'figure'),
    Input('map', 'clickData')
)

def update_graphs(clickData):
    if clickData is None:
        # Return initial figures or empty figures if desired
        return {}, {}
    # Extract the clicked polygon's ID (or other identifying information) from clickData
    clicked_id = clickData['points'][0]['pointIndex']
    parcel_id = data.loc[clicked_id, 'parcelId']
    # Filter the DataFrame based on the clicked polygon's ID and type ('binary')
    filtered_binary = data[(data['parcelId'] == parcel_id) & (data['type'] == 'binary')]
    filtered_binary = filtered_binary.sort_values(by=['time'])
    fig_line1 = create_graph(filtered_binary)

    # Filter the DataFrame based on the clicked polygon's ID and type ('percent')
    filtered_percent = data[(data['parcelId'] == parcel_id) & (data['type'] == 'percentage')]
    filtered_percent = filtered_percent.sort_values(by=['time', 'value'])
    fig_line2 = create_graph(filtered_percent)

    return fig_line1, fig_line2


# Function to create a graph based on a filtered DataFrame
def create_graph(df):
    # Customize the graph creation based on your data and desired graph type
    line = px.line(df, x='time', y='value')
    # Add any desired customization to the figure here

    return line

# Run the app
app.run_server(debug=True)

