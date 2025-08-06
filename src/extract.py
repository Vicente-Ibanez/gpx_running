import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import folium
import branca
from shapely.geometry import Point
from geojson import Feature, FeatureCollection, dump

root_path = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = "/data/input"

# Create columns correct names
CORRECT_COLS = [
    "type","drop","drop","drop",
    "timestamp","drop","drop","latitude",
    "drop","drop","longitude",
    "drop","drop","distance","drop",
    "drop","speed","drop","drop",
    "cadence", "drop", "drop", "drop", "drop", "drop"
]

def load_data(path: str):
    """Load all CSV files from the given path"""
    df = pd.DataFrame()
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.endswith('.csv'):
                file_path = os.path.join(path, file)
                print(f"📊 Loading: {file}")
                df = pd.concat([df, pd.read_csv(file_path)], ignore_index=True)
            break
    return df

def preprocess_cols(df):
    """Preprocess the dataframe columns"""
    if df.empty:
        return df
    
    df = df[df.columns[0:25]].copy()
    # Create the proper column headers
    df = df.set_axis(CORRECT_COLS, axis=1)
    # Drop unused columns
    df = df.drop(columns="drop")
    df = df.dropna(axis=0)
    df = df[df['type'] == 'Data'].copy()
    return df

def point_converter(meters_coords):
    # Create function to convert EPSG 3857 (meters) to EPSG 4326 (coordinates)
    boundary = meters_coords / ((2**32 )/ 360)
    return boundary

def preprocess_df(df):
    """
    Preprocess the dataframe to create geometry and prepare for mapping
    
    Input: pd.DataFrame
    Output: geopandas.GeoDataFrame
    """
    if df.empty:
        print("❌ No data to preprocess")
        return gpd.GeoDataFrame()
    
    print("🔄 Preprocessing dataframe...")
    
    # Convert coordinates to float
    # df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    # df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['speed'] = pd.to_numeric(df['speed'], errors='coerce')
    df['cadence'] = pd.to_numeric(df['cadence'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
    
    # Drop rows with invalid coordinates
    df = df.dropna(subset=['latitude', 'longitude'])
    print(f"!!!!{len(df)}")

    # # Convert speed from m/s to mph
    df['speed_mph'] = df['speed'] * 2.236936
    
    # Convert the longitude and latitude to EPSG 4326
    df["latitude"] = df["latitude"].apply(point_converter)
    df["longitude"] = df["longitude"].apply(point_converter)
    # Filter out invalid coordinates (very large or very small values)
    df = df[
        (df['latitude'] > -90) & (df['latitude'] < 90) &
        (df['longitude'] > -180) & (df['longitude'] < 180)
    ]
    print(f"!!!!{len(df)}")
    # Create geometry points
    df['geometry'] = df.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    print(f"✅ Preprocessed {len(gdf)} data points")
    return gdf


def create_interactive_map(gdf, html_path):
    """Create an interactive map of the data"""

    # Create a LineString from the points
    from shapely.geometry import LineString
    if len(gdf) < 2:
        print("❌ Not enough points to create a line.")
        return
    # Sort by timestamp if available for correct order
    if 'timestamp' in gdf.columns:
        gdf = gdf.sort_values('timestamp')
    line = LineString(gdf['geometry'].tolist())

    # Create map centered on the mean of the points
    mean_lat = gdf['geometry'].y.mean()
    mean_lon = gdf['geometry'].x.mean()
    map1 = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)

    # Add the line to the map
    folium.GeoJson(line, name='Run Path', style_function=lambda x: {
        'color': 'blue',
        'weight': 4,
        'opacity': 0.8
    }).add_to(map1)

    folium.LayerControl().add_to(map1)

    # Save to the provided html_path
    map1.save(html_path)

 

def main():
    """Main function to run the complete pipeline"""
    print("🚀 Starting data processing pipeline...")
    
    # Load data
    data_path = root_path + DATA_PATH
    print(f"📂 Loading data from: {data_path}")
    raw_csv = load_data(data_path)
    
    if raw_csv.empty:
        print("❌ No CSV files found in data/input/")
        return
    
    print(f"📊 Loaded {len(raw_csv)} rows of data")
    
    # Preprocess columns
    preprocessed_df = preprocess_cols(raw_csv)
    print(f"🔄 Preprocessed columns: {len(preprocessed_df)} rows")
    
    # Create geopandas dataframe
    gdf = preprocess_df(preprocessed_df)
    
    if gdf.empty:
        print("❌ No valid GPS data found")
        return
    
    # Create static map
    output_dir = os.path.join(root_path, "data", "plots")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create interactive map
    html_path = os.path.join(root_path, "data", "index_cadence.html")
    create_interactive_map(gdf, html_path)
    
    print("✅ Pipeline complete!")

if __name__ == "__main__":
    main()