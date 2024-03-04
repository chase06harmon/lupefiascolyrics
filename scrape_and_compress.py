GENIUS_API_TOKEN='TOKEN'
OPEN_AI_TOKEN='TOKEN'

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
def request_song_info(artist_name, song_cap):
    page = 1
    songs = []
    titles = []
    
    while True:
        response = request_artist_info(artist_name, page)
        json = response.json()
        # Collect up to song_cap song objects from artist
        song_info = []
        for hit in json['response']['hits']:
            if artist_name.lower() in hit['result']['artist_names'].lower():
                song_info.append(hit)
    
        # Collect song URL's from song objects
        for song in song_info:
            if (len(songs) < song_cap):
                url = song['result']['url']
                songs.append(url)
                title = song['result']['title']
                titles.append(title)
        if (len(songs) == song_cap):
            break
        else:
            page += 1
        print('Found {} songs by {}'.format(len(songs), artist_name))
        
    print('Found {} songs by {}'.format(len(songs), artist_name))
    return zip(songs,titles)
    
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
    song_infos = request_song_info(artist_name, song_count)
    client = OpenAI(api_key=OPEN_AI_TOKEN)
    with open(filename, 'w') as f:
        for num, song_info in enumerate(song_infos):
            url, title = song_info
            lyrics = scrape_song_lyrics(url)
            chat_completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f"{lyrics} \n What do the above lyrics mean to you? In your response touch on some of the major themes and metaphors"},
                ]
            )
            summary = chat_completion.choices[0].message.content
            json_object = {"title": title, "lyrics": lyrics, "summary": summary}
            f.write(json.dumps(json_object) + '\n')
            numTicks = int(100/song_count * (num+1))
            print(f'Loading [ {"|" * numTicks}{" " * (100 - numTicks)}]', end='\r')
    f.close()
    print("\n")
    print(f"Finished writing {song_count} songs by {artist_name} to {filename}")

def compress_data(commpressed_file, file_to_compress):
    with tarfile.open(commpressed_file, 'w:gz') as tar: 
        tar.add(file_to_compress)

def clean_data(data_file):
    non_empty_lines = []

    with open(data_file, "r") as f:
        for line in f:
            line_dict = json.loads(line.strip())
            if line_dict.get("lyrics"): 
                non_empty_lines.append(line_dict)
    with open(data_file, "w") as f:
        for line in non_empty_lines:
            f.write(json.dumps(line) + '\n')

def get_all_songs():
    page = requests.get("https://lupefiasco.fandom.com/wiki/List_of_songs")
    soup = BeautifulSoup(page.text, 'html.parser')
    titles = set()
    for td in soup.find_all('td'):  # Adjust if your structure differs
        a = td.find('a')  # Find the 'a' element within each 'td'
        if a:
            titles.add(a.text.lower())  # Add the text (which is the title) to the list
    return titles


if __name__ == "__main__":
    jsonl_filename = "dataset.jsonl"
    tar_filename = "dataset.tar.gz"
    artist_name = "Lupe Fiasco"
    num_songs = 535
    # write_lyrics_to_file(artist_name, num_songs, jsonl_filename)
    # clean_data(jsonl_filename)
    compress_data(tar_filename, jsonl_filename)
    # print(get_all_songs())