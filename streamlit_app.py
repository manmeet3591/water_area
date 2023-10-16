import os
import json
import ee
import streamlit as st
import datetime

import folium
from streamlit_folium import folium_static

# Get the environment variable or default to an empty string
service_account_key_str = os.environ.get('GEE_SERVICE_ACCOUNT_KEY', '')


# Retrieve the service account key from Streamlit's secrets
service_account_key = st.secrets["GEE_SERVICE_ACCOUNT_KEY"]
# Use the service account for authentication
credentials = ee.ServiceAccountCredentials(email=service_account_key['client_email'], key_data=service_account_key['private_key'])
ee.Initialize(credentials)

# Constants for our app
START_DATE = '2021-04-02'
END_DATE = '2021-04-03'


def get_water_area(start_date, end_date, coords):
    # Define a rectangle (box) geometry using the coordinates
    box = ee.Geometry.Rectangle(coords)

    # Filter collection
    colFilter = ee.Filter.And(
        ee.Filter.bounds(box),
        ee.Filter.date(ee.Date(str(start_date)), ee.Date(str(end_date)))
    )

    # Get Dynamic World collection
    dwCol = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filter(colFilter)
    dwImage = ee.Image(dwCol.first())

    # Extract the "water" class
    water_mask = dwImage.select('water')

    # Calculate area
    pixel_area = water_mask.multiply(ee.Image.pixelArea())
    total_water_area = pixel_area.reduceRegion(reducer=ee.Reducer.sum(), geometry=box, scale=30).get('water').getInfo()

    # Convert from square meters to square kilometers
    total_water_area_km2 = total_water_area / 1e6
    return total_water_area_km2, water_mask

st.title("Dynamic World - Water Area Calculator over a Box")

# Input widgets

start_date_default = datetime.datetime.strptime(START_DATE, '%Y-%m-%d').date()
#start_date = st.date_input("Start Date", start_date_default)


#start_date = st.date_input("Start Date", START_DATE)
end_date_default = datetime.datetime.strptime(END_DATE, '%Y-%m-%d').date()


#end_date = st.date_input("End Date", end_date_default)

start_date = st.date_input("Start Date", start_date_default).strftime('%Y-%m-%d')
end_date = st.date_input("End Date", end_date_default).strftime('%Y-%m-%d')

min_lon = st.number_input("Minimum Longitude", value=20.0)
min_lat = st.number_input("Minimum Latitude", value=52.0)
max_lon = st.number_input("Maximum Longitude", value=20.5)
max_lat = st.number_input("Maximum Latitude", value=52.5)

# Calculate and display results
coords = [min_lon, min_lat, max_lon, max_lat]
water_area, water_mask = get_water_area(start_date, end_date, coords)
st.write(f"Total water area for the selected date range: {water_area:.2f} km^2")

# To run the app:
# streamlit run streamlit_app.py
def plot_water_mask_on_map(mask, coords):
    """Function to plot water mask on a map using folium."""
    
    center_lat = (coords[1] + coords[3]) / 2
    center_lon = (coords[0] + coords[2]) / 2
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Create a URL for the water mask using Earth Engine's `getThumbURL` method
    mask_url = mask.getThumbURL({
        'bands': 'water',
        'min': 0,
        'max': 1,
        'palette': ['blue'],  # Color for water
        'region': coords
    })
    
    # Add the mask as an image overlay on the folium map
    folium.raster_layers.ImageOverlay(
        image=mask_url,
        bounds=[[coords[1], coords[0]], [coords[3], coords[2]]],
        opacity=0.7
    ).add_to(m)
    
    return m
# Rest of the code ...

# Calculate and display results
coords = [min_lon, min_lat, max_lon, max_lat]
water_area = get_water_area(start_date, end_date, coords)

# Plot the water mask
water_mask_map = plot_water_mask_on_map(water_mask, coords)
folium_static(water_mask_map)

#st.write(f"Total water area for the selected date range: {water_area:.2f} km^2")
