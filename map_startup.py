import folium
from folium.plugins import Search

import pandas as pd
import geopandas as gpd
import geopandas as gpd, folium, branca

from geojson import Point, Feature, FeatureCollection, dump
import json

import numpy as np
import matplotlib.pyplot as plt
import os 

from shapely.geometry import LineString, MultiLineString
import shapely.geometry
import shapely.wkt

import pytz
import datetime
import pyproj

from quick_startup import quick_startup


def map_create(map_type):
    # Get the data from the data file and transform it into the correct format
    data = quick_startup()
    # data 
    # print(data["cadence"])

    data["cadence"] = data["cadence"].fillna(0)
    data["cadence"] = data["cadence"].astype(float)

    # Copy the data and use the copied version
    gdf = data.copy()

    # Convert the geometry column into a GeoJson to be usable for folium
    s = gdf["geometry"].to_json()
    s = json.loads(s)

    # Change the location of id feature in geojson so it can be accessed
    for id_spot in s["features"]:
        id_spot["properties"]["id"] = str(id_spot["id"])
        id_spot["properties"]["name"] = str(id_spot["id"])

    # open a new geojson file and write the current one into it
    with open('data/streamlit_data/myfile.geojson', 'w') as f:
        dump(s, f)

    # Convert index to an id column to be used to merge dfs
    gdf["id"] = gdf.index
    gdf["id"] = gdf["id"].astype(str)

    # read in the geojson file
    s2 = gpd.read_file('data/streamlit_data/myfile.geojson', driver='GeoJSON')

    
    # use only certain column from the data file
    gdf2 = gdf[[map_type, "id", "geometry"]].copy()

    # Merge the two dfs (df and geojson)
    gdf2 = gpd.sjoin(s2, gdf2, how='inner', op='within')

    # get min and max of geojsons, cutting off obsurities/annolimies
    min, max = gdf2[map_type].quantile([0.1,0.9]).apply(lambda x: round(x, 2))
    print(min, "     ", max)
    # Set color map based on distribution of speed
    colormap = branca.colormap.LinearColormap(
        colors=['black', '#ecca00','#ec9b00','#ec5300','#ec2400', '#ec0000'],
        index=gdf2[map_type].quantile([.01,0.2,0.4,0.6,0.8]),
        vmin=min,
        vmax=max
    )

    # Assign caption type
    if map_type == "speed":
        colormap.caption="Speed Mi/Hr"
    else:
        colormap.caption="Steps/Second"

    # Create map with initial location
    map1 = folium.Map(location=[43.7696, 11.2558], zoom_start=12)

    # Use the geojson to plot the runs w/ speed as the color and add to map
    speed_geo = folium.GeoJson(gdf2,
                            name='Track',
                            style_function=lambda x: {                    
                                'color': colormap(x['properties']
                                [map_type]),                             
                                'weight':3, 'fillOpacity':0.5
                                }
                            ).add_to(map1)
   
    # Add a LayerControl
    folium.LayerControl().add_to(map1)
   
    # And the Color Map legend
    colormap.add_to(map1)
   
    # Save with descriptive name
    if map_type == "speed":
        # save map to html file
        map1.save('data/streamlit_data/index_speed.html')
    else:
        # save map to html file
        map1.save('data/streamlit_data/index_cadence.html')
        # pass