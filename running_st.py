from lib2to3.pytree import generate_matches
import streamlit as st
from streamlit_folium import st_folium
import streamlit.components.v1 as components

from map_startup import map_create

st.title("Florence 2022")
st.write("By Vicente Ibanez")

map_type = st.sidebar.selectbox(
    "Select Category:",
    ("speed", "cadence")
)

st.write(map_type)


def generate_map(map_type):
    try:
        # Select the file to open
        path = "data/streamlit_data/index_" + map_type + ".html"
        
        HTMLFile = open(path, "r")

        # Reading the file
        index = HTMLFile.read()

        # Display the file to streamlit
        components.html(html = index, height=800, width=800)
    except:

        map_create(map_type)
        
        # Select the file to open
        path = "data/streamlit_data/index_" + map_type + ".html"
        
        # Opening the html file
        HTMLFile = open(path, "r")
        
        # Reading the file
        index = HTMLFile.read()

        # Display the file to streamlit
        components.html(html = index, height=800, width=800) 

if map_type == "speed":
    generate_map(map_type)
else:
    generate_map(map_type)


