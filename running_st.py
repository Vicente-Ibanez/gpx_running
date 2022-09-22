import streamlit as st
from streamlit_folium import st_folium

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
import pyproj #import Proj, transform
import plotly.express as px

from quick_startup import quick_startup

data = quick_startup()

gdf = data.copy()

### Code no longer needed after GEOJSON file is created
# s = gdf["geometry"].to_json()
# s = json.loads(s)

# for id_spot in s["features"]:
#     id_spot["properties"]["id"] = str(id_spot["id"])
#     id_spot["properties"]["name"] = str(id_spot["id"])

# with open('/data/streamlit_data/myfile.geojson.geojson', 'w') as f:
#    dump(s, f)

gdf["id"] = gdf.index
gdf["id"] = gdf["id"].astype(str)

s2 = gpd.read_file('data/streamlit_data/myfile.geojson', driver='GeoJSON')


gdf2 = gdf[["speed", "id", "geometry"]].copy()

gdf2 = gpd.sjoin(s2, gdf2, how='inner', op='within')

min, max = gdf2['speed'].quantile([0.1,0.9]).apply(lambda x: round(x, 2))

colormap = branca.colormap.LinearColormap(
    colors=['black', '#ecca00','#ec9b00','#ec5300','#ec2400', '#ec0000'],
    index=gdf2['speed'].quantile([.01, 0.2,0.4,0.6,0.8]),
    vmin=min,
    vmax=max
)
colormap.caption="Speed Mi/Hr"


map1 = folium.Map(location=[43.7696, 11.2558], zoom_start=12)

stategeo = folium.GeoJson(gdf2,
                          name='Track',
                          style_function=lambda x: {                    
                            'color': colormap(x['properties']
                            ['speed']),                             
                            'weight':3, 'fillOpacity':0.5
                            }
                         ).add_to(map1)

# Add a LayerControl.
folium.LayerControl().add_to(map1)

# And the Color Map legend.
colormap.add_to(map1)

st_data = st_folium(map1, width=500, height=500)