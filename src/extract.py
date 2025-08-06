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
    # Filter out invalid coordinates (very large, very small, or near zero values)
    df = df[
        (df['latitude'] > -90) & (df['latitude'] < 90) &
        (df['longitude'] > -180) & (df['longitude'] < 180) &
        (df['latitude'].abs() > 1) & (df['longitude'].abs() > 1)
    ]

    # Remove statistical outliers using IQR for latitude and longitude
    for col in ['latitude', 'longitude']:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df = df[(df[col] >= lower) & (df[col] <= upper)]
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
    
    # Process each CSV file separately and plot each as a separate line
    data_path = root_path + DATA_PATH
    print(f"📂 Loading data from: {data_path}")
    if not os.path.exists(data_path):
        print("❌ Data path does not exist.")
        return

    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ No CSV files found in data/input/")
        return

    # Create map object (centered on first file's mean location, fallback to default if needed)
    map1 = None
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'black']
    color_idx = 0
    any_valid = False
    for file in files:
        file_path = os.path.join(data_path, file)
        print(f"� Processing: {file}")
        raw_csv = pd.read_csv(file_path)
        preprocessed_df = preprocess_cols(raw_csv)
        gdf = preprocess_df(preprocessed_df)
        if gdf.empty or len(gdf) < 2:
            print(f"❌ No valid GPS data in {file}")
            continue
        # Sort by timestamp if available
        if 'timestamp' in gdf.columns:
            gdf = gdf.sort_values('timestamp')
        from shapely.geometry import LineString
        line = LineString(gdf['geometry'].tolist())
        # Create map if not yet created
        if map1 is None:
            mean_lat = gdf['geometry'].y.mean()
            mean_lon = gdf['geometry'].x.mean()
            map1 = folium.Map(location=[mean_lat, mean_lon], zoom_start=13)
        # Add the line to the map
        folium.GeoJson(line, name=file, style_function=lambda x, c=colors[color_idx % len(colors)]: {
            'color': c,
            'weight': 4,
            'opacity': 0.8
        }).add_to(map1)
        color_idx += 1
        any_valid = True

    if not any_valid:
        print("❌ No valid GPS data found in any file.")
        return

    folium.LayerControl().add_to(map1)
    # Save interactive map
    html_path = os.path.join(root_path, "data", "index_cadence.html")
    map1.save(html_path)
    print("✅ Pipeline complete!")

if __name__ == "__main__":
    main()