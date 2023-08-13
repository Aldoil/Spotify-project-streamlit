import streamlit as st 
import pandas as pd 
import numpy as np 
import plotly.express as px 



#Read data
df = pd.read_csv('Clean_data.csv')


def visualize(df):

    df['date'] = pd.to_datetime(df['date']).dt.date
    ### Title part ###
    image_url = 'https://iaudioguide.com/wp-content/uploads/2014/12/spotify-logo-primary-horizontal-dark-background-rgbizi.jpg'

    st.image(image_url)
    st.title("Data exploatory")
    st.markdown(""" 
                This is your spotify stats dashboard.\n 
                * Data from {} to {} 
                """.format(df['date'].min(), df['date'].max()))
    

    ### Filters ###
    st.sidebar.header('Your menu')
    first_date = st.sidebar.date_input('Start date', df['date'].min())
    last_date = st.sidebar.date_input('End date', df['date'].max())
    system = st.sidebar.multiselect('System', ['All'] + df['System'].unique().tolist())
    device = st.sidebar.multiselect('Device', ['All'] + df['Device'].unique().tolist())
    audio_type = st.sidebar.multiselect('Audio type', df['Type'].unique().tolist())
    artist = st.sidebar.multiselect('Artist', ['All'] + df['master_metadata_album_artist_name'].unique().tolist())
    song = st.sidebar.multiselect('Song', ['All'] + df['master_metadata_track_name'].unique().tolist())

    df = df[(df['date'] >= first_date) & (df['date'] <= last_date)]

    if system and system != ['All']:
        df = df[df['System'].isin(system)]
    if device and device != ['All']:
        df = df[df['Device'].isin(device)]
    if audio_type:
        df = df[df['Type'].isin(audio_type)]
    if artist and artist != ['All']:
        df = df[df['master_metadata_album_artist_name'].isin(artist)]
    if song and song != ['All']:
        df = df[df['master_metadata_track_name'].isin(song)]


    ### Information part ###
    st.info(f"Time played: {round(df['ms_played'].sum()/60000, 2)} minutes \
                which is {round(df['ms_played'].sum()/3600000, 2)} hours \
                which is {round(df['ms_played'].sum()/3600000/24, 2)} days.")
    st.info(f"Number of unique artists listened: {df['master_metadata_album_artist_name'].nunique()}")
    st.info(f"Number of unique songs/podcasts listened: {df['master_metadata_track_name'].nunique()}")

    
    ### Date plots ###
    df_min_played = df.groupby(['date'])['ms_played'].sum().reset_index()
    df_min_played['Minutes played'] = round(df_min_played['ms_played']/60000, 2)
    df_min_played['Hours played'] = round(df_min_played['ms_played']/3600000, 2)
    df_min_played['Days played'] = round(df_min_played['Hours played'] / 24, 2)
    
    date_range = pd.date_range(start=df_min_played['date'].min(), end=df_min_played['date'].max(), freq='D')   # Create a full date range
    df_min_played.set_index('date', inplace=True)
    df_min_played = df_min_played.reindex(date_range).fillna(0).reset_index()  # Set 'date' as the index and reindex with the full date range
    df_min_played.rename(columns={'index': 'date'}, inplace=True) # Rename the new index to 'date'

    df_min_played['year'] = df_min_played['date'].dt.year  # Extract the year from the date

    # Sum the minutes played by year
    df_yearly_played = df_min_played.groupby('year')[['Minutes played', 'Hours played', 'Days played']].sum().reset_index()
    
    hist_year_plot = px.bar(data_frame=df_yearly_played, x='year', y='Hours played', title='Hours listened per year', hover_data=['Hours played', 'Days played'])
    hist_year_plot.update_xaxes(type='category', tickmode='array', tickvals=df_yearly_played['year'])
    st.plotly_chart(hist_year_plot)

    line_date_plot = px.line(df_min_played, x='date', y='Minutes played', title='Minutes listened per month', hover_data=['Hours played', 'Days played'])
    line_date_plot.update_xaxes(range=[df_min_played['date'].min(), df_min_played['date'].max()] )

    st.plotly_chart(line_date_plot)
    df_min_played

    ### Artists plot ###

    df_artist_gruped = df.groupby('master_metadata_album_artist_name')['ms_played'].sum().reset_index()
    df_artist_gruped['Minutes played'] = round(df_artist_gruped['ms_played']/60000, 2)
    df_artist_gruped['Hours played'] = round(df_artist_gruped['ms_played']/3600000, 2)
    df_artist_gruped['Days played'] = round(df_artist_gruped['Hours played'] / 24, 2)
    df_artist_gruped.rename(columns={'master_metadata_album_artist_name': 'Artist'}, inplace=True)
    df_artist_gruped = df_artist_gruped.sort_values('Minutes played', ascending=False).head(20)

    artist_plot = px.pie(df_artist_gruped, values='Hours played', names='Artist', title='Most listened artists')
    st.plotly_chart(artist_plot)


    ### Artists plot ###
    df_songs_gruped = df.groupby('master_metadata_track_name')['ms_played'].sum().reset_index()
    df_songs_gruped['Minutes played'] = round(df_songs_gruped['ms_played']/60000, 2)
    df_songs_gruped['Hours played'] = round(df_songs_gruped['ms_played']/3600000, 2)
    df_songs_gruped['Days played'] = round(df_songs_gruped['Hours played'] / 24, 2)
    df_songs_gruped.rename(columns={'master_metadata_track_name': 'Song'}, inplace=True)
    df_songs_gruped = df_songs_gruped.sort_values('Minutes played', ascending=True).head(20)

    songs_plot = px.pie(df_songs_gruped, values='Minutes played', names='Song', title='Most played songs')
    st.plotly_chart(songs_plot)




visualize(df)

