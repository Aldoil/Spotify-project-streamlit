import streamlit as st 
import pandas as pd 
import numpy as np 
import plotly.express as px 
import plotly.graph_objects as go



def get_data():
    json_data_list = []
    # Allow multiple file uploads
    uploaded_files = st.file_uploader("Choose JSON files", accept_multiple_files=True)
    for file in uploaded_files:
        # Read the uploaded JSON file
        data = pd.read_json(file)
        json_data_list.append(data)

    try:    
        df = pd.concat(json_data_list, ignore_index =True)
        return df
    except:
        st.title('There is no data')
        
def data_processing(df):
    df = df.drop(columns=['username', 'user_agent_decrypted', 'spotify_track_uri', 'spotify_episode_uri', 
                      'reason_start', 'reason_end', 'offline_timestamp', 'incognito_mode', 'ip_addr_decrypted'])
    pattern_1 = r'([^ ]+)'
    pattern_2 = r'\((.*?)\)'

    # Use str.extract to split the 'platform' column
    df['System'] = df['platform'].str.extract(pattern_1)[0].str.upper()
    df['Device'] = df['platform'].str.extract(pattern_2)[0].str.upper()
    df['System'] = df['System'].replace('OSX', 'OS')

    #Deal with dates 
    df['ts'] = pd.to_datetime(df['ts'])
    df['date'] = df['ts'].dt.strftime('%Y-%m-%d')
    df['time'] = df['ts'].dt.strftime('%H:%M')
    df = df.drop(['ts', 'platform'], axis=1)
    # Create type column
    df['Type'] = np.where(df['episode_name'].notna() , 'Podcast', 'Song')

    return df

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
    country = st.sidebar.multiselect('Listening country', ['All'] + df['conn_country'].unique().tolist())

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
    if country and country != ['All']:
        df = df[df['conn_country'].isin(country)]


    ### Information part ###
    st.info(f"Time played: {round(df['ms_played'].sum()/60000, 2)} minutes \
                which is {round(df['ms_played'].sum()/3600000, 2)} hours \
                which is {round(df['ms_played'].sum()/3600000/24, 2)} days.")
    st.info(f"Number of unique artists listened: {df['master_metadata_album_artist_name'].nunique()}")
    st.info(f"Number of unique songs listened: {df['master_metadata_track_name'].nunique()}")
    st.info(f"Number of unique podcasts listened: {df['episode_show_name'].nunique()}")
    st.info(f"Number of unique podcasts episodes listened: {df['episode_name'].nunique()}")


    
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


    ### Time plot ###   
    df['time'] = pd.to_datetime(df['time'], format='%H:%M') #Prepare data
    df['time'] = df['time'].dt.hour

    df_time_grouped = df.groupby(df['time'])['ms_played'].sum().reset_index()
    df_time_grouped['Minutes played'] = round(df_time_grouped['ms_played']/60000, 2)
    df_time_grouped['Hours played'] = round(df_time_grouped['ms_played']/3600000, 2)
    df_time_grouped['Days played'] = round(df_time_grouped['Hours played'] / 24, 2)                             
    
    time_fig = px.bar(data_frame=df_time_grouped, x='time', y='Minutes played', title='Minutes played per hour of the day', hover_data=['Hours played', 'Days played'])
    st.plotly_chart(time_fig)


    ### Artists plot ###

    df_artist_gruped = df.groupby('master_metadata_album_artist_name')['ms_played'].sum().reset_index()
    df_artist_gruped['Minutes played'] = round(df_artist_gruped['ms_played']/60000, 2)
    df_artist_gruped['Hours played'] = round(df_artist_gruped['ms_played']/3600000, 2)
    df_artist_gruped['Days played'] = round(df_artist_gruped['Hours played'] / 24, 2)
    df_artist_gruped.rename(columns={'master_metadata_album_artist_name': 'Artist'}, inplace=True)
    df_artist_gruped = df_artist_gruped.sort_values('Minutes played', ascending=False).head(20)

    artist_plot = px.pie(df_artist_gruped, values='Hours played', names='Artist', title='Most listened artists (Top 20)')
    st.plotly_chart(artist_plot)

    ### Artists plot ###
    df_songs_gruped = df.groupby(['master_metadata_album_artist_name', 'master_metadata_track_name'])['ms_played'].sum().reset_index()
    df_songs_gruped['Minutes played'] = round(df_songs_gruped['ms_played']/60000, 2)
    df_songs_gruped['Hours played'] = round(df_songs_gruped['ms_played']/3600000, 2)
    df_songs_gruped['Days played'] = round(df_songs_gruped['Hours played'] / 24, 2)
    df_songs_gruped.rename(columns={'master_metadata_track_name': 'Song', 'master_metadata_album_artist_name': 'Artist'}, inplace=True)
    df_songs_gruped = df_songs_gruped.sort_values('Minutes played', ascending=False).head(20)

    df_songs_gruped['Artist '] = df_songs_gruped['Artist'] + ' | Hours played: ' + df_songs_gruped['Hours played'].astype(str) #Create hover

    # Plot using 'hover_info' as hover data
    songs_plot = px.pie(df_songs_gruped, values='Minutes played', names='Song', title='Most played songs (Top 20)', hover_data=['Artist '])
    st.plotly_chart(songs_plot)



df = get_data()
df = data_processing(df)
visualize(df)

