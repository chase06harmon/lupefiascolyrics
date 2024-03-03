GENIUS_API_TOKEN='Syj2Kk9BJSkayL2Rs9CnAZJpG2Sjr_oq3_WEwHKUnVZyJ87zZuvYf2DTC1Cvt-us'
OPEN_AI_TOKEN='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'

# Make HTTP requests
import requests
# Scrape data from an HTML document
from bs4 import BeautifulSoup
# I/O
import os
# Search and manipulate strings
import re
import json
from openai import OpenAI
import tarfile

# Get artist object from Genius API
def request_artist_info(artist_name, page):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + GENIUS_API_TOKEN}
    search_url = base_url + '/search?per_page=10&page=' + str(page)
    data = {'q': artist_name}
    response = requests.get(search_url, data=data, headers=headers)
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
    soup = BeautifulSoup(page.text, 'html.parser')
    lyrics = ''
    for elem in soup.find_all('div', class_=lambda value: value and value.startswith("Lyrics__Container")):
        # print(elem.decode_contents())
        if elem.text:
            snippet = elem.decode_contents().replace('<br/>', '\n').replace('<br>', '\n')
            snippet = snippet.replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '')
            # print(snippet)
            clean_snippet = BeautifulSoup(snippet, 'html.parser').get_text(separator='\n')
            lyrics += clean_snippet.strip() + '\n\n'    
    return lyrics




def write_lyrics_to_file(artist_name, song_count, filename):
    urls = request_song_url(artist_name, song_count)
    client = OpenAI(api_key=OPEN_AI_TOKEN)
    with open(filename, 'w') as f:
        for num, url in enumerate(urls):
            lyrics = scrape_song_lyrics(url)
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f"{lyrics} \n What do the above lyrics mean to you? In your response touch on some of the major themes and metaphors"},
                ]
            )
            summary = chat_completion.choices[0].message.content
            json_object = {"lyrics": lyrics, "summary": summary}
            f.write(json.dumps(json_object) + '\n')
            numTicks = int(100/song_count * (num+1))
            print(f'Loading [ {"|" * numTicks}{" " * (100 - numTicks)}]', end='\r')
    f.close()
    print("\n")
    print(f"Finished writing {song_count} songs by {artist_name} to {filename}")

def compress_data(commpressed_file, file_to_compress):
    with tarfile.open(commpressed_file, 'w:gz') as tar: 
        tar.add(file_to_compress)

if __name__ == "__main__":
    jsonl_filename = "dataset.jsonl"
    tar_filename = "dataset.tar.gz"
    artist_name = "Lupe Fiasco"
    num_songs = 2
    write_lyrics_to_file(artist_name, 1, jsonl_filename)
    compress_data(tar_filename, jsonl_filename)