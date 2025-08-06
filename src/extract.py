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
    map_type = "cadence"
    gdf["cadence"] = gdf["cadence"].fillna(0)
    gdf["cadence"] = gdf["cadence"].astype(float)

    # Convert the geometry column into a GeoJson to be usable for folium
    s = gdf["geometry"].to_json()
    s = json.loads(s)

    # Change the location of id feature in geojson so it can be accessed
    for id_spot in s["features"]:
        id_spot["properties"]["id"] = str(id_spot["id"])
        id_spot["properties"]["name"] = str(id_spot["id"])

    # open a new geojson file and write the current one into it
    with open('data/myfile.geojson', 'w') as f:
        dump(s, f)

    # Convert index to an id column to be used to merge dfs
    gdf["id"] = gdf.index
    gdf["id"] = gdf["id"].astype(str)

    # read in the geojson file
    s2 = gpd.read_file('data/myfile.geojson', driver='GeoJSON')

    
    # use only certain column from the data file
    gdf2 = gdf[[map_type, "id", "geometry"]].copy()

    # Merge the two dfs (df and geojson)
    gdf2 = gpd.sjoin(s2, gdf2, how='inner', predicate='within')

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
        colormap.caption="Steps/Min"

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
        map1.save('data/index_speed.html')
    else:
        # save map to html file
        map1.save('data/index_cadence.html')

 

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