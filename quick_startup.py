import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import os 
from shapely.geometry import LineString, MultiLineString
import shapely.geometry
import pytz
import datetime
import pyproj #import Proj, transform
print(pyproj.__version__)  # 2.4.1
print(pyproj.proj_version_str)  # 6.2.1
import plotly.express as px
from extract import extract

def quick_startup():
    """This function can be called to quickly read and prepare data to be used to make a plot
    
    Keyword arguments:
    argument -- No Arguments
    Return: geopandas Dataframe ready for plotting/exploring
    """
    
    folder = "data/florence_run_csv/"
    track = pd.DataFrame()
    x = 0
    for file in os.listdir(folder):
        if file.endswith(('.csv')):
            try:
                data = pd.read_csv(folder + file)
                track = track.append(extract(data, file))
                x +=1
            except:
                print("Error", file)
    print(x)
    # track_plot = track[["geometry", "Pace Mi/Hr"]].copy()
    track_plot = track.copy()
    # # Add the Florence Plot
    gdf = gpd.read_file("data/florence_city_gps/florence_city.gpx", layer='tracks', crs = 4326)

    gdf = gdf[["geometry"]]

    track_plot = gpd.GeoDataFrame(track_plot, geometry="geometry", crs = 4326)

    track_plot = track_plot.append(gdf)

    # track_plot["Pace Mi/Hr"] = track_plot["Pace Mi/Hr"].fillna(0)
    track_plot["speed"] = track_plot["speed"].fillna(0)

    return track_plot