"""
Extract

This file is used to convert a pandas dataframe into plottable data.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import os 
from shapely.geometry import LineString, MultiLineString
import shapely.geometry
import pytz
import datetime
import plotly.express as px

import warnings

from shapely.errors import ShapelyDeprecationWarning


from file_utilities import(
    garmin_time_change,
    point_converter,
    number_rounder
)


# Initialize the csv's column names
old_cols = [
    'Type', 'Local Number', 'Message', 'Field 1', 'Value 1', 'Units 1',
    'Field 2', 'Value 2', 'Units 2', 'Field 3', 'Value 3', 'Units 3',
    'Field 4', 'Value 4', 'Units 4', 'Field 5', 'Value 5', 'Units 5',
    'Field 6', 'Value 6', 'Units 6', 'Field 7', 'Value 7', 'Units 7',       
    'Unnamed: 24', "drop", "drop", "drop"
]

# Create columns correct names
cols = [
    "type","drop","drop","drop",
    "timestamp","drop","drop","latitude",
    "drop","drop","longitude",
    "drop","drop","distance","drop",
    "drop","speed","drop","drop",
    "cadence", "drop", "drop", "drop", "drop", "drop"
    
    ]


def extract(data, file):
    """
    This function changes to panadas dataframe to have the correct columns and units
    
    Input: pd.DataFrame
    This is a dataframe the gps and running metrics data.

    Output: pd.DataFrame
    This is a dataframe that has the correct column names and datatypes, with data integrity ensured

    """
    try:
        # Create the proper column headers
        data = data.set_axis(cols, axis=1, inplace=False)
        # Drop unused columns
        data = data.drop(columns="drop")
        data = data.dropna(axis=0)
    except:
        # If the columns are not convertable, then ignore that one file and return
        # an empty dataframe
        print("This file has no gps data: ", file)
        return pd.DataFrame(cols=cols)


    # Change timestamp into MM/DD/YYYY/HH/MM/SS
    data["datetime"] = data["timestamp"].apply(garmin_time_change)
    
    # Convert the longitude and latitude to EPSG 4326
    data["latitude"] = data["latitude"].apply(point_converter)
    data["longitude"] = data["longitude"].apply(point_converter)

    # Make a copy of the df so other statitics
    gdf_copy = data.copy()

    # Shift the points up by one in new column
    gdf_copy["longitude_2"] = gdf_copy["longitude"].shift(-1)
    gdf_copy["latitude_2"] = gdf_copy["latitude"].shift(-1)

    # Check that longtitude/latitude are not gps errors
    if len(gdf_copy[gdf_copy["longitude"]<10])>0 or len(gdf_copy[gdf_copy["latitude"]<10])>0:
        print("Problem with: ", file)

    # fill the last column with its same coordinate, as the shift left one value empty
    gdf_copy = gdf_copy.fillna({"longitude_2":gdf_copy.iloc[-1]["longitude"], "latitude_2":gdf_copy.iloc[-1]["latitude"]})
    
    # Convert the coordinates into x, y coords
    gdf_copy["start"] = [xy for xy in zip(gdf_copy.longitude, gdf_copy.latitude)]
    gdf_copy["finish"] = [xy for xy in zip(gdf_copy.longitude_2, gdf_copy.latitude_2)]

    # Ignore the deprecation warning as shapely 2.0 isnt being used
    warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
    # changed the two coordinates into a line
    gdf_copy["geometry"] = gdf_copy.apply(lambda x: LineString([x.start, x.finish]), axis=1)
    warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
    
    # create a unique identifyer (type) using the start date/time as a primary key
    gdf_copy["type"] = str(gdf_copy["datetime"][0])

    # Convert speed from meters/second to miles/hour
    gdf_copy["speed"] = gdf_copy["speed"].apply(lambda x: x*2.236936)
    # Create a column for speed with rounded values to help plotting
    gdf_copy["Pace Mi/Hr"] = gdf_copy.speed.apply(number_rounder)
    # check if any speed or geometry values are missing
    if gdf_copy["speed"].isna().sum() > 0 or gdf_copy["geometry"].isna().sum():
        print(file, " has missing speed values")

    return gdf_copy
