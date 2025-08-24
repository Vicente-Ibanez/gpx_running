"""
This script processes running data from CSV files, cleans it, and prepares it for mapping.
"""

import folium
import geopandas as gpd
import os
import pandas as pd
from shapely.geometry import LineString, Point


def retrive_cols(df:pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the dataframe columns
    
    Arguments:
    `df`: pd.DataFrame - Raw dataframe from CSV
    """

    if df.empty:
        return df
    
    df = df[df.columns[0:25]].copy()

    # Create the proper column headers
    df = df.set_axis([
        "type", "drop", "drop",
        "drop", "timestamp", "drop",
        "type2", "latitude", "drop",
        "drop", "longitude", "drop",
        "drop", "distance", "drop",
        "drop", "speed", "drop",
        "drop", "cadence", "drop", 
        "drop", "drop", "drop", 
        "drop"
    ], axis=1)
    
    # Drop unused columns
    df.drop(columns=["drop"], inplace=True)
    
    return df


def enforce_datatypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce correct datatypes for dataframe columns
    """
    numeric_cols = ['latitude', 'longitude', 'distance', 'speed', 'cadence']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    return df


def data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove unneeded rows from dataframe.
    """
    # Remove unneeded rows
    df = df[(df['type'] == 'Data') & (df['type2'] == 'position_lat')].copy()
    df = df.dropna(axis=0)

    # Convert speed from m/s to mph
    df['speed_mph'] = df['speed'] * 2.236936
    return df

def point_converter(meters_coords):
    # Create function to convert EPSG 3857 (meters) to EPSG 4326 (coordinates)
    boundary = meters_coords / ((2**32 )/ 360)
    return boundary


def prepare_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the latitude and longitude coordinates from the dataframe.
    The coordinates are in a specific format that needs to be converted.
    """

    # Convert the longitude and latitude to EPSG 4326
    point_cols = ['latitude', 'longitude']
    df[point_cols] = df[point_cols].apply(point_converter)

    # Filter out invalid coordinates (very large, very small, or near zero values)
    df = df[
        (df['latitude'] > -90) & (df['latitude'] < 90) &
        (df['longitude'] > -180) & (df['longitude'] < 180)
    ]
    return df

def create_geometry(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Create a GeoDataFrame with geometry points from the dataframe.
    """
    # Create geometry points
    df['geometry'] = df.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    return gdf

def preprocess_df(df):
    """
    Preprocess the dataframe to create geometry and prepare for mapping
    
    Input: pd.DataFrame
    Output: geopandas.GeoDataFrame
    """
    if df.empty:
        print("No data to preprocess")
        return gpd.GeoDataFrame()
    
    print("Preprocessing dataframe...")
    df = retrive_cols(df)
    df = enforce_datatypes(df)
    df = data_cleaning(df)
    df = prepare_coordinates(df)
    
    gdf = create_geometry(df)
    print(f"Preprocessed {len(gdf)} data points")
    return gdf


def create_interactive_map(gdf, map, color):
    """Create an interactive map of the data"""

    if len(gdf) < 2:
        print("❌ Not enough points to create a line.")
        return

    # Sort by timestamp if available for correct order
    if 'timestamp' in gdf.columns:
        gdf = gdf.sort_values('timestamp')

    line = LineString(gdf['geometry'].tolist())

    # Create map centered on the mean of the points
    if map is None:
        mean_lat = gdf['geometry'].y.mean()
        mean_lon = gdf['geometry'].x.mean()
        map = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)

    # Add the line to the map
    folium.GeoJson(
        line, 
        name='Run Path', 
        style_function=lambda x: {
            'color': color,
            'weight': 4,
            'opacity': 0.8
        }
    ).add_to(map)

    # folium.LayerControl().add_to(map)

    return map

 
def main():
    """Main function to run the complete pipeline"""
    print("Starting data processing pipeline")
    
    root_path = os.path.dirname(os.path.dirname(__file__))
    data_path = root_path + "/data/input"
    print(f"Loading data from: {data_path}")
    if not os.path.exists(data_path):
        print("❌ Data path does not exist.")
        return

    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ No CSV files found in data/input/")
        return

    # Create map object (centered on first file's mean location, fallback to default if needed)
    map = None
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'black']
    color_idx = 0

    # Process each CSV file separately and plot each as a separate line
    # This prevents loading more data then the computer can handle
    for file in files:
        file_path = os.path.join(data_path, file)
        print(f"Processing: {file}")
        raw_csv = pd.read_csv(file_path)
        gdf = preprocess_df(raw_csv)

        if gdf.empty or len(gdf) < 2:
            print(f"No valid GPS data in {file}")
            continue
        
        map = create_interactive_map(gdf, map, colors[color_idx])

        color_idx += 1
        color_idx = color_idx % len(colors)

    folium.LayerControl().add_to(map)
    # Save interactive map
    html_path = os.path.join(root_path, "data", "index_cadence.html")
    map.save(html_path)
    print("✅ Pipeline complete!")

if __name__ == "__main__":
    main()