import requests
import re
from dotenv import load_dotenv
import os

load_dotenv()
youtube_token = os.getenv('YOUTUBE_TOKEN')
spotify_secret = os.getenv('SPOTIFY_SECRET')


def get_song_links(input_data):
    links = {}
    debug_info = {}

    # Determine if input is a link, title, artist, or title - artist
    if 'youtube.com' in input_data or 'youtu.be' in input_data:
        video_id = extract_youtube_id(input_data)
        title, artist = get_youtube_info(video_id)
        if title and artist:
            links['youtube'] = f'https://www.youtube.com/watch?v={video_id}'
        debug_info['youtube_initial'] = f"Title: {title}, Artist: {artist}"
    elif 'spotify.com' in input_data:
        track_id = input_data.split('/')[-1]
        title, artist = get_spotify_info(track_id)
        if title and artist:
            links['spotify'] = f'https://open.spotify.com/track/{track_id}'
        debug_info['spotify_initial'] = f"Title: {title}, Artist: {artist}"
    else:
        # Check if input contains ' - ' to separate title and artist
        if ' - ' in input_data:
            title, artist = input_data.split(' - ')
        else:
            # Assume input is either title or artist
            title = artist = input_data
        debug_info['input_parsed'] = f"Title: {title}, Artist: {artist}"

    # Get missing links
    if 'youtube' not in links:
        youtube_link = get_youtube_link(title, artist)
        if youtube_link:
            links['youtube'] = youtube_link
        debug_info['youtube_search'] = f"Link found: {bool(youtube_link)}"

    if 'spotify' not in links:
        spotify_link, spotify_title, spotify_artist = get_spotify_link(title, artist)
        if spotify_link:
            links['spotify'] = spotify_link
            # Update title and artist if they were initially empty
            if title == artist == input_data:
                title, artist = spotify_title, spotify_artist
        debug_info[
            'spotify_search'] = f"Link found: {bool(spotify_link)}, Title: {spotify_title}, Artist: {spotify_artist}"

    # If we got info from Spotify but not YouTube, try YouTube search again
    if 'spotify' in links and 'youtube' not in links:
        youtube_link = get_youtube_link(title, artist)
        if youtube_link:
            links['youtube'] = youtube_link
        debug_info['youtube_retry'] = f"Link found: {bool(youtube_link)}"

    # If we still don't have both links, try searching again with the other service's info
    if 'youtube' in links and 'spotify' not in links:
        spotify_link, _, _ = get_spotify_link(title, artist)
        if spotify_link:
            links['spotify'] = spotify_link
        debug_info['spotify_retry'] = f"Link found: {bool(spotify_link)}"

    debug_info['final_links'] = links
    return links, debug_info


def extract_youtube_id(url):
    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    return video_id_match.group(1) if video_id_match else None


def get_youtube_info(video_id):
    youtube_api_key = youtube_token
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={youtube_api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and data['items']:
            snippet = data['items'][0]['snippet']
            return snippet['title'], snippet['channelTitle']
    print(f"YouTube API Error: {response.status_code}, {response.text}")
    return None, None


def get_spotify_info(track_id):
    spotify_token = spotify_secret
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = {'Authorization': f'Bearer {spotify_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'name' in data and 'artists' in data:
            return data['name'], data['artists'][0]['name']
    print(f"Spotify API Error: {response.status_code}, {response.text}")
    return None, None


def get_youtube_link(title, artist):
    youtube_api_key = youtube_token
    query = f'{title} {artist}'.strip()
    youtube_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={youtube_api_key}'
    response = requests.get(youtube_url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and data['items']:
            video_id = data['items'][0]['id']['videoId']
            return f'https://www.youtube.com/watch?v={video_id}'
    print(f"YouTube Search API Error: {response.status_code}, {response.text}")
    return None


def get_spotify_link(title, artist):
    spotify_token = spotify_secret
    query = f'{title} {artist}'.strip()
    spotify_url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=1'
    headers = {'Authorization': f'Bearer {spotify_token}'}
    response = requests.get(spotify_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'tracks' in data and data['tracks']['items']:
            track = data['tracks']['items'][0]
            return (f'https://open.spotify.com/track/{track["id"]}',
                    track['name'],
                    track['artists'][0]['name'])
    print(f"Spotify Search API Error: {response.status_code}, {response.text}")
    return None, None, None


# Example usage
for query in ["https://www.youtube.com/watch?v=dQw4w9WgXcQ",
              "Bohemian Rhapsody - Queen",
              "Beyoncé",
              "Shape of You"]:
    links, debug = get_song_links(query)
    print(f"Query: {query}")
    print(f"Links: {links}")
    print(f"Debug Info: {debug}")
    print("---")
