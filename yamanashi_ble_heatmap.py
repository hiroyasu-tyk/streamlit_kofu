# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime as dt, timedelta, time
import pydeck as pdk
# import sys

# sys.path.append("./")
from functions4kofu import *
from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'

def map(data, lat=35.668, lon=138.569, zoom=12):
    st.write(pdk.Deck(
        # map_style="mapbox://styles/mapbox/light-v9",
        map_provider="mapbox",
        map_style=pdk.map_styles.SATELLITE,
        initial_view_state={
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "pitch": 50,
        },
        layers = [
            pdk.Layer(
            # 'HexagonLayer',  # `type` positional argument is here
            "HeatmapLayer",
            #UK_ACCIDENTS_DATA,
            data=data,
            get_position=['log', 'lat'],
            get_elevation='count',
            auto_highlight=True,
            elevation_scale=10,
            pickable=True,
            elevation_range=[0, 100],
            radius = 50,
            extruded=True,
            coverage=1.0)
        ]
        # layers=[
        #     pdk.Layer(
        #         "HexagonLayer",
        #         data=data,
        #         get_position=["lon", "lat"],
        #         radius=100,
        #         elevation_scale=4,
        #         elevation_range=[0, 1000],
        #         pickable=True,
        #         extruded=True,
        #     ),
        # ]
    ))
@st.cache
def load_data():
    url = "https://8tops.yamanashi.ac.jp/kofu/bt/getPopulation_csv.php"
    sday = "20211226"
    res = requests.get(url
                       + "?sday=" + sday).content
    kofu_df = pd.read_csv(io.StringIO(res.decode('utf-8')))
    kofu_df['date'] = kofu_df['Unnamed: 0'].astype('str')
    kofu_df['date'] = pd.to_datetime(kofu_df['date'], format="%Y-%m-%d %H:%M:%S")
    kofu_df['day'] = kofu_df['date'].dt.strftime("%Y-%m-%d")
    kofu_df['hourmin'] = kofu_df['date'].dt.strftime("%H:%M")
    return kofu_df

@st.cache
def load_sensor_info():
    sensors = getSensorInfo()
    sensor_df =pd.DataFrame(sensors)
    sensor_df = sensor_df.T.reset_index().rename(
        columns={"index": "point"})
    return sensor_df


kofu_df = load_data()
sensor_df = load_sensor_info()

init_day = dt(2022,1,23, 0,0)

date4show = st.slider("表示",
         min_value=dt(2022,1,1,0,0),
         max_value= dt(2022,1,31,0,0), # dt.now() doesn't work (return the initial state)
         value=init_day,
         step = timedelta(minutes=10),
         format="YYYY-MM-DD hh:mm")
st.write(date4show)
day = date4show.strftime("%Y-%m-%d")

hourmin = date4show.strftime("%H:%M")

st.session_state.day = date4show
tmp_df = kofu_df[(kofu_df['day']==day) & (kofu_df['hourmin']==hourmin)].T.reset_index()
tmp_df = tmp_df.set_axis(["point", "count"], axis=1)
data4pydeck = pd.merge(tmp_df, sensor_df, on="point", how="inner")
data4pydeck.dropna(inplace=True)
data4pydeck['count'] = data4pydeck['count'].astype(int)
st.dataframe(data4pydeck)
map(data4pydeck)
