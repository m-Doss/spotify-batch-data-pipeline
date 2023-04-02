import os
import json
import base64
from datetime import date
from requests import post, get
from pymongo_get_database import get_database

# Environement variables for Spotify API
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

countries = ["Argentina", "Australia", "Austria", "Belarus", "Belgium",
            "Bolivia", "Brazil", "Bulgaria", "Canada", "Chile", "Colombia", "Costa Rica",
            "Czech Republic", "Denmark", "Dominican Republic", "Ecuador", "Egypt",
            "El Salvador", "Estonia", "Finland", "France", "Germany", "Greece", "Guatemala",
            "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Ireland",
            "Israel", "Italy", "Japan", "Kazakhstan", "Latvia", "Lithuania", "Luxembourg",
            "Malaysia", "Mexico", "Morocco", "Netherlands", "New Zealand", "Nicaragua",
            "Nigeria", "Norway", "Pakistan", "Panama", "Paraguay", "Peru", "Philippines",
            "Poland", "Portugal", "Romania", "Saudi Arabia", "Singapore", "Slovakia",
            "South Africa", "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan",
            "Thailand", "Turkey", "UAE", "USA", "Ukraine", "United Kingdom", "Uruguay",
            "Venezuela", "Vietnam"
]


# Returns the authorization token
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]

    return token

# Returns the authorization header
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# Search for a "Top - <country>" playlist
def search_for_playlist(token, playlist_name):
    base_url = "https://api.spotify.com/v1"
    header = get_auth_header(token)
    query = f'/search?q={playlist_name}&type=playlist'

    query_url = base_url + query
    result = get(query_url, headers=header)
    json_result = json.loads(result.content)["playlists"]["items"][0]

    return (json_result["id"], json_result["name"])

# Get tracks' meta data
def get_track_audio_features(token, track_id):
    base_url = "https://api.spotify.com/v1"
    header = get_auth_header(token)
    url_ext = f'/audio-features/{track_id}'

    query_url = base_url + url_ext
    result = get(query_url, headers=header)
    json_result = json.loads(result.content)

    return json_result

# Get the tracks id in each playlist
def get_playlist_items(token, playlist_id) -> list[dict]:
    base_url = "https://api.spotify.com/v1"
    header = get_auth_header(token)
    url_ext = f'/playlists/{playlist_id}/tracks'
    query = '?fields=items(track(id,name,popularity))'

    query_url = base_url + url_ext + query
    result = get(query_url, headers=header)
    json_result = json.loads(result.content)["items"]
    tracks = [  
            {"id": json_result[i]["track"]["id"], 
            "name": json_result[i]["track"]["name"], 
            "position": i+1, 
            "popularity": json_result[i]["track"]["popularity"]} 
            for i in range(len(json_result))
            ]
    return tracks



def main():
    token = get_token()
    for _, v in enumerate(countries):
        main_dict = { "_id": int(date.today().strftime("%Y%m%d")), "date": date.today().strftime("%Y-%m-%d"), "country": v }
        playlist = search_for_playlist(token, f'Top 50 - {v}')
        main_dict['playlist_id'] = playlist[0]
        main_dict['playlist_name'] = playlist[1]
        country_top_tracks = get_playlist_items(token, playlist[0])
        
        for i in range(len(country_top_tracks)):
            country_top_tracks[i]["audio_features"] = get_track_audio_features(token, country_top_tracks[i]["id"])
        
        main_dict["tracks"] = country_top_tracks
    
        file_name = "spotifyJson" + v

        # Writing to MongoDB collections
        dbname = get_database()
        collection = dbname[file_name]
        collection.insert_one(main_dict)
        

if __name__ == "__main__":
    main()