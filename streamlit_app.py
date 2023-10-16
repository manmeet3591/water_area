import os
import json
import ee
import streamlit as st

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

@st.cache
def get_water_area(start_date, end_date, coords):
    # Define a rectangle (box) geometry using the coordinates
    box = ee.Geometry.Rectangle(coords)

    # Filter collection
    colFilter = ee.Filter.and(
        ee.Filter.bounds(box),
        ee.Filter.date(ee.Date(start_date), ee.Date(end_date))
    )

    # Get Dynamic World collection
    dwCol = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1').filter(colFilter)
    dwImage = ee.Image(dwCol.first())

    # Extract the "water" class
    water_mask = dwImage.select('water')

    # Calculate area
    pixel_area = water_mask.multiply(ee.Image.pixelArea())
    total_water_area = pixel_area.reduceRegion(reducer=ee.Reducer.sum(), geometry=box, scale=10).get('water').getInfo()

    # Convert from square meters to square kilometers
    total_water_area_km2 = total_water_area / 1e6
    return total_water_area_km2

st.title("Dynamic World - Water Area Calculator over a Box")

# Input widgets
start_date = st.date_input("Start Date", START_DATE)
end_date = st.date_input("End Date", END_DATE)
min_lon = st.number_input("Minimum Longitude", value=20.0)
min_lat = st.number_input("Minimum Latitude", value=52.0)
max_lon = st.number_input("Maximum Longitude", value=21.0)
max_lat = st.number_input("Maximum Latitude", value=53.0)

# Calculate and display results
coords = [min_lon, min_lat, max_lon, max_lat]
water_area = get_water_area(start_date, end_date, coords)
st.write(f"Total water area for the selected date range: {water_area:.2f} km^2")

# To run the app:
# streamlit run streamlit_app.py
