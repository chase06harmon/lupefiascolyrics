GENIUS_API_TOKEN='Syj2Kk9BJSkayL2Rs9CnAZJpG2Sjr_oq3_WEwHKUnVZyJ87zZuvYf2DTC1Cvt-us'

# Make HTTP requests
import requests
# Scrape data from an HTML document
from bs4 import BeautifulSoup
# I/O
import os
# Search and manipulate strings
import re
import json

# Get artist object from Genius API
def request_artist_info(artist_name, page):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + GENIUS_API_TOKEN}
    search_url = base_url + '/search?per_page=10&page=' + str(page)
    data = {'q': artist_name}
    response = requests.get(search_url, data=data, headers=headers)
    with open("response.json", 'w') as f: 
        json.dump(response.json(), f, indent=4)
    return response

# Get Genius.com song url's from artist object
def request_song_url(artist_name, song_cap):
    page = 1
    songs = []
    
    while True:
        response = request_artist_info(artist_name, page)
        json = response.json()
        # Collect up to song_cap song objects from artist
        song_info = []
        for hit in json['response']['hits']:
            if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
                song_info.append(hit)
    
        # Collect song URL's from song objects
        for song in song_info:
            if (len(songs) < song_cap):
                url = song['result']['url']
                songs.append(url)
            
        if (len(songs) == song_cap):
            break
        else:
            page += 1
        
    print('Found {} songs by {}'.format(len(songs), artist_name))
    return songs
    
def scrape_song_lyrics(url):
    page = requests.get(url)
    html = BeautifulSoup(page.text, 'html.parser')
    lyrics = html.find('div', class_='Lyrics__Container-sc-1ynbvzw-1 kUgSbL').get_text(separator="\n")
    #remove empty lines
    print(lyrics)
    lyrics = os.linesep.join([s for s in lyrics.splitlines() if s])         
    return lyrics

print(request_song_url("Lupe Fiasco", 23))

