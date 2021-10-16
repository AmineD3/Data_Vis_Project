from pandas.core.frame import DataFrame
from pandas.io.formats.format import DataFrameFormatter
import streamlit as st
import altair as alt
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
import time
from streamlit.errors import StreamlitAPIWarning
import pydeck as pdk

def get_hour(dt):
    return dt.hour

def count_rows(rows):
    return len(rows)

def color_df(val):
    if val==1:
        color='#FEF983'
    else:
        color='#B8EA65'
    return f'background-color: {color}'

def data_loading_timer(func):
    @st.cache(allow_output_mutation=True)   
    def wrapper():
        before=time.time()
        df=func()
        time.sleep(1)
        fh.write('Data loading took: '+str(round(time.time()-before,3))+" seconds\n")
        return df
    return wrapper

@data_loading_timer
def load_data():
    df=pd.read_csv('data_ny_trips.csv')
    return df

def data_cleaning_timer(func):
    @st.cache()
    def wrapper(df):
        before=time.time()
        df=func(df)
        time.sleep(1)
        fh.write('Data cleaning took: '+str(round(time.time()-before,3))+" seconds\n")
        return df
    return wrapper
    
@data_cleaning_timer
def data_clean(df):
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['pickup_hour']=df["tpep_pickup_datetime"].map(get_hour)
    df['tpep_dropoff_datetime']= pd.to_datetime(df['tpep_dropoff_datetime'])
    df['dropoff_hour'] = df["tpep_dropoff_datetime"].map(get_hour)
    df = df.drop(['tpep_pickup_datetime','tpep_dropoff_datetime'], axis=1)
    return df


def map_drawing_timer(func):
    @st.cache()
    def wrapper(df):
        before=time.time()
        time.sleep(5)
        df=func(df)
        fh.write('Map drawing took: '+str(round(time.time()-before,3))+" seconds\n")
        return df
    return wrapper

@map_drawing_timer
def draw_map(df):
    df=df.head(9500)
    maps=pdk.Deck(map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
    latitude=40.74,
    longitude=-73.93,
    zoom=10.7,
    pitch=60),
    layers=[
    pdk.Layer(
    'HexagonLayer',
    data=df,
    get_position='[longitude,latitude]',
    radius=200,
    elevation_scale=4,
    elevation_range=[0, 1000],
    pickable=True,
    extruded=True),
    ],
    )
    return maps 


#part 1: importing data
st.subheader("Ikrame Kamoun - DS5 - Streamlit lab 2")
st.subheader("1- Import the data:")
st.write("Choose the data that you wish to import:")
left_column, right_column = st.columns(2)
cb0=left_column.checkbox(label='New York trips')
cb1=right_column.checkbox(label='Uber')
global fh
if cb0:
    fh=open('log_execution_time.txt','a')
    fh.write("**** Dataset: New York trips *****\n")
    df=load_data()
    st.write(df)
    st.write("Dataframe description:")
    st.write(df.describe())   
    st.write("Dataframe tail:")
    st.write(df.tail())
#part 2: data cleaning
    st.subheader("2- Cleaning the data:")
    st.write("We need to clean the dataframe in order to improve the quality of the visualizations.")
    st.write("we will replace the columns 'tpep_pickup_datetime' and 'tpep_dropoff_datetime' with the columns pickup_hour and dropoff_hour because all the data in the dataframe is recorded on the 15th of January 2015 (Thursday).")    
    df=data_clean(df) 
    st.write("Here's the dataframe after the update:")
    st.write(df.head())
#part 3: data visualization
    st.subheader("3- Visualizing the data:")
    st.write("Select the visualizations you would like to see:")
    left_col, right_col = st.columns(2)
    cb3=left_col.checkbox(label='Frequency by pick-up hour')
    cb4=right_col.checkbox(label='Frequency by hour for each vendor ID')
    cb5=left_col.checkbox(label='Correlation heatmap')
    cb7=left_col.checkbox(label='Frequency by trip distance')
    cb8=right_col.checkbox(label='Frequency by trip distance for each vendor ID')
    cb9=left_col.checkbox(label='Pick-ups location')
    cb10=right_col.checkbox(label='Drop-offs location')

    if cb3:
        by_hour = df.groupby('pickup_hour').apply(count_rows)
        st.subheader('Frequency by pick-up hour')
        st.write("The line chart below shows the number of pick-ups over 24 hours.")
        st.bar_chart(by_hour)
        st.write("We can notice that the number of trips reaches its peak at 22pm.")
    if cb4:
        st.subheader('Frequency by pick-up hour for each type of vendor')
        by_cross=df.groupby(['pickup_hour','VendorID']).apply(count_rows).unstack()
        by_cross=by_cross.rename(columns={1: 'Vendor ID: 1', 2: 'Vendor ID: 2'})
        by_cross[['Vendor ID: 1','Vendor ID: 2']] = by_cross[['Vendor ID: 1','Vendor ID: 2']].fillna(0)
        #displaying the plots
        left_column, right_column = st.columns(2)
        left_column.line_chart(by_cross['Vendor ID: 1'])
        right_column.line_chart(by_cross['Vendor ID: 2'])
        st.write("The average number of pick-ups of the vendors with the id=1 is:",by_cross['Vendor ID: 1'].mean())
        st.write("The average number of pick-ups of the vendors with the id=2 is:",by_cross['Vendor ID: 2'].mean())
        st.write("We can see from the plots and the values of means that overall, the vendors with the id=2")
        st.write("have more pick-ups than the vendors with the the id=1.")
    if cb5:
        st.subheader("Heatmap")
        fig, ax = plt.subplots(figsize=(10,7))
        sns.heatmap(df.corr(), ax=ax,cmap="YlGnBu",annot=True)
        st.write(fig)
    if cb7:
        st.subheader('Frequency by trip distance')
        df['trip_distance']=df['trip_distance'].round()
        by_dist = df.groupby('trip_distance').apply(count_rows)
        st.bar_chart(by_dist)
        st.write("We can see that most of the trips in our dataset are of small distances of less than 2Km.")
        st.write("This means that either the data that we're studying was recorded in a small town or the service that the vendors offer does not support long distance trips.")
    if cb8:
        st.subheader('Frequency by trip distance for each type of vendor')
        by_coss_dist=df.groupby(['trip_distance','VendorID']).apply(count_rows).unstack()
        by_coss_dist=by_coss_dist.rename(columns={1: 'Vendor ID: 1', 2: 'Vendor ID: 2'})
        by_coss_dist[['Vendor ID: 1','Vendor ID: 2']] = by_coss_dist[['Vendor ID: 1','Vendor ID: 2']].fillna(0)
        #displaying the plots
        left_column, right_column = st.columns(2)
        left_column.line_chart(by_coss_dist['Vendor ID: 1'])
        right_column.line_chart(by_coss_dist['Vendor ID: 2'])
        st.write("By looking at the two line charts above, we can see that both vendors have quiet the same type of trips as both plots peak in the range of 1-2km.")
    if cb9:
        st.subheader("Frequency by pick-up location")
        df_pickups= df.rename({'pickup_longitude': 'longitude', 'pickup_latitude': 'latitude'}, axis=1)
        df_pickups['longitude']=round(df_pickups['longitude'],2)
        df_pickups['latitude']=round(df_pickups['latitude'],2)
        st.pydeck_chart(draw_map(df_pickups))
    if cb10:
        st.subheader("Frequency by drop-off location")
        df_dropoff= df.rename({'dropoff_longitude': 'longitude', 'dropoff_latitude': 'latitude'}, axis=1)
        df_dropoff['longitude']=round(df_dropoff['longitude'],2)
        df_dropoff['latitude']=round(df_dropoff['latitude'],2)
        st.pydeck_chart(draw_map(df_dropoff))
    fh.close()    