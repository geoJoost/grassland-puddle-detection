# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 15:00:16 2023

@author: Marnic
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import geopandas as gpd

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.io as io

df = gpd.read_file("output/01_subsidised_field.shp")
subsidised = df.to_crs(crs=4326)
del df

    
fig = px.choropleth(subsidised, geojson= subsidised.geometry, color=subsidised["Parcel_fou"],
                    locations=subsidised.index) #hover_data=subsidised["CODE_BEHEE"])

#fig.update_geos(fitbounds=subsidised.geometry, visible=False)
#fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H4("Political candidate voting pool analysis"),
        html.P("Select a candidate:"),
        dcc.RadioItems(
            id="candidate",
            options=["Joly", "Coderre", "Bergeron"],
            value="Coderre",
            inline=True,
        ),
        dcc.Graph(id="graph"),
    ]
)


@app.callback(
    Output("graph", "figure"),
    Input("candidate", "value"),
)
def display_choropleth(candidate):
    geojson = px.data.election_geojson()
    fig = px.choropleth(
        df,
        geojson=geojson,
        color=candidate,
        locations="district",
        featureidkey="properties.district",
        projection="mercator",
        range_color=[0, 6500],
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
