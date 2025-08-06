#!/bin/bash
set -e

echo "🚀 Starting GPX Running Application Setup..."

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Java is not installed. Please install Java first."
    exit 1
fi

echo "Java is installed:"
java -version

# Check if FitCSVTool.jar already exists in project root
if [ -f "FitCSVTool.jar" ]; then
    echo "✅ FitCSVTool.jar already exists in project root"
else
    echo "🔍 FitCSVTool.jar not found, setting up Garmin SDK..."
    
    # Create garmin_sdk directory if it doesn't exist
    if [ ! -d "garmin_sdk" ]; then
        echo "📁 Creating garmin_sdk directory..."
        mkdir garmin_sdk
    fi

    # Change to garmin_sdk directory
    cd garmin_sdk

    # Download FitSDK if it doesn't exist
    if [ ! -f "FitSDKRelease_21.171.00.zip" ]; then
        echo "📦 Downloading FitSDK from Garmin..."
        curl -L -o FitSDKRelease_21.171.00.zip https://developer.garmin.com/downloads/fit/sdk/FitSDKRelease_21.171.00.zip
    else
        echo "✅ FitSDK already downloaded"
    fi

    # Extract FitSDK if not already extracted
    if [ ! -d "java" ]; then
        echo "📂 Extracting FitSDK..."
        unzip -q FitSDKRelease_21.171.00.zip
    else
        echo "✅ FitSDK already extracted"
    fi

    # Find and copy FitCSVTool.jar to parent directory
    if [ -f "java/FitCSVTool.jar" ]; then
        echo "📋 Copying FitCSVTool.jar to project root..."
        cp java/FitCSVTool.jar ..
        echo "✅ FitCSVTool.jar ready"
    else
        echo "❌ FitCSVTool.jar not found in extracted SDK"
        exit 1
    fi

    # Go back to project root
    cd ..
fi

# Convert FIT files to CSV if they exist
if [ -d "data/running_data" ]; then
    echo "🔄 Processing FIT files..."
    
    # # Rename all .FIT files to .fit (lowercase extension)
    # echo "📝 Renaming .FIT files to .fit..."
    # for fit_file in data/running_data/*.FIT; do
    #     if [ -f "$fit_file" ]; then
    #         new_name="${fit_file%.FIT}.fit"
    #         mv "$fit_file" "$new_name"
    #         echo "Renamed: $(basename "$fit_file") → $(basename "$new_name")"
    #     fi
    # done
    
    # # Check if there are any .fit files after renaming
    # if [ "$(ls -A data/running_data/*.fit 2>/dev/null)" ]; then
    #     echo "🔄 Converting FIT files to CSV..."
        
    #     # Create output directory if it doesn't exist
    #     mkdir -p data/input
        
    #     # Convert each FIT file
    #     for fit_file in data/running_data/*.fit; do
    #         if [ -f "$fit_file" ]; then
    #             filename=$(basename "$fit_file" .fit)
    #             echo "Converting $filename.fit..."
    #             java -jar FitCSVTool.jar -b "$fit_file" "data/input/${filename}.FIT.records.csv"
    #         fi
    #     done
    #     echo "✅ FIT file conversion complete"
        
        # Setup Python virtual environment and install packages
        echo "🐍 Setting up Python environment..."
        
        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            echo "🔧 Creating virtual environment..."
            python3 -m venv venv
        else
            echo "✅ Virtual environment already exists"
        fi
        
        # Activate virtual environment
        echo "🔌 Activating virtual environment..."
        source venv/bin/activate
        
        # Upgrade pip
        echo "⬆️ Upgrading pip..."
        pip install --upgrade pip
        
        # Install requirements
        echo "📦 Installing required packages..."
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            echo "⚠️ No requirements.txt found, installing basic dependencies..."
            pip install pandas geopandas numpy matplotlib shapely pytz pyproj plotly streamlit
        fi
        
        # Run the extract.py script to create graphs
        if [ -f "src/extract.py" ]; then
            echo "🎨 Running extract.py to create graphs..."
            python3 src/extract.py
            echo "✅ Graph creation complete"
        else
            echo "⚠️ src/extract.py not found, skipping graph creation"
        fi
    else
        echo "ℹ️ No FIT files found in data/running_data/"
    fi
else
    echo "ℹ️ No data/running_data/ directory found"
fi


