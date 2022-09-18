import pandas as pd
import geopandas as gpd
import os 
import pytz
import datetime


def garmin_time_change(timestamp):
    """sumary_line
    Input: timestamp (in seconds)
    Output: timestamp in usable form for pandas
    """
    
    # Convert timestamp
    timestamp_16 = 31132
    mesgTimestamp = timestamp + ((timestamp_16 - timestamp) & 0xffff)
    return datetime.datetime.fromtimestamp(mesgTimestamp + 631065600, pytz.timezone('Europe/Zurich'))


def point_converter(meters_coords):
    # Create function to convert EPSG 3857 (meters) to EPSG 4326 (coordinates)
    boundary = meters_coords / ((2**32 )/ 360)
    return boundary


def number_rounder(value):
    if value > 0 and value < 11:
        return value
    if value >= 11:
        return 11
    elif value < 0:
        return 0