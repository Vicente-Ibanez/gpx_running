import streamlit as st
from streamlit_folium import st_folium
import streamlit.components.v1 as components

from map_startup import map_create


try:
    # Opening the html file
    HTMLFile = open("data/streamlit_data/index.html", "r")
    
    # Reading the file
    index = HTMLFile.read()

    # Display the file to streamlit
    components.html(html = index, height=800, width=800)
except:
    map_create()
    # Opening the html file
    HTMLFile = open("data/streamlit_data/index.html", "r")
    
    # Reading the file
    index = HTMLFile.read()

    # Display the file to streamlit
    components.html(html = index, height=800, width=800) 