import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Environment variables for API keys and tokens
load_dotenv('tokens.env')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# List of label IDs to track (you can add more)
LABELS_TO_TRACK = [
    "The Third Movement",
    "Heresy",
    "Broken Strain",
    "Spoontech Records",
    "Dark. Descent.",
]

# Initialize Spotify client
spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)

def check_new_releases():
    """Check for new releases from specified labels"""
    new_releases = []
    
    for label_id in LABELS_TO_TRACK:
        # Get all albums from the label
        results = spotify.search(
            f'label:"{label_id}" tag:new',
            type='album',
            limit=3,
        )
        
        for item in results['albums']['items']:
            # Fetch detailed album information
            album_results = spotify.album(item['id'])
            
            # Check if the album's label matches any in LABELS_TO_TRACK
            if album_results['label'] in LABELS_TO_TRACK:
                new_releases.append({
                    'name': album_results['name'],
                    'artists': [artist['name'] for artist in album_results['artists']],
                    'url': album_results['external_urls']['spotify'],
                    'label': album_results['label'],
                })

    print(new_releases)
    return new_releases

check_new_releases()