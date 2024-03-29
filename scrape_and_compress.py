GENIUS_API_TOKEN=TOKEN
OPEN_AI_TOKEN=OTHER_TOKEN


def gpt_prompt(lyrics):
    pattern = re.compile(r'(\[.*?\])')
    section_type = re.search(pattern, lyrics)

    return f"""
    # You take a section of lyrics from a rap song and create a prompt that could be used to generate the section. 
    # You are GREAT at extracting the most important information out of these lyrics.  
    # The section type can be found at the top of the lyrics.
    # The prompts must be short and simple. No more than a single sentence. 

    # example outputs:

    Write a verse in the style of Lupe Fiasco exploring the concept of identity.

    Write an intro in the style of Kendrick Lamar that tells the story of how Kendrick Lamar’s father, Ducky, almost lost his life in a fateful encounter.

    Write a hook in the style of Jay Z about a man who has problems, but none of them are caused by women.

    Write a chorus in the style of 2Pac recognizing the strength and resiliency of women. 

    Write an outro in the style of J. Cole, reflecting on the impact of societal expectations on personal growth.

    Write a bridge in the style of Drake, about the paradoxes of fame and solitude.

    # end of examples

    # Here are the lyrics
    
    {lyrics}

    # Remember the section type and artist should be completely determined by {section_type}
    """


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
import csv

# Get artist object from Genius API
def request_artist_info(artist_name, page):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + GENIUS_API_TOKEN}
    search_url = base_url + '/search?per_page=10&page=' + str(page)
    data = {'q': artist_name}
    response = requests.get(search_url, data=data, headers=headers)
    return response

# Get Genius.com song url's from artist object
def request_song_info(artist_name):
    page = 1
    songs = []
    titles = []
    artists = []
    while True:
        response = request_artist_info(artist_name, page)
        json = response.json()
        # Collect up to song_cap song objects from artist
        song_info = []
        for hit in json['response']['hits']:
            if artist_name.lower() in hit['result']['artist_names'].lower():
                song_info.append(hit)
        
        if len(songs) >= 3: # no new songs
            break

        # Collect song URL's from song objects
        for song in song_info:
            url = song['result']['url']
            songs.append(url)
            title = song['result']['title']
            titles.append(title)
            artists.append(artist_name)
        page += 1
        print('Found {} songs by {}'.format(len(songs), artist_name))
        
    print('There are {} songs by {} available on Genuis API'.format(len(songs), artist_name))
    return list(zip(songs,titles,artists))
    
def scrape_song_lyrics(url, artist_name):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    pattern = re.compile(r'(\[.*?\])')
    lyrics = ''
    for elem in soup.find_all('div', class_=lambda value: value and value.startswith("Lyrics__Container")):
        # print(elem.decode_contents())
        if elem.text:
            snippet = elem.decode_contents().replace('<br/>', '\n').replace('<br>', '')
            snippet = snippet.replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '')
            clean_snippet = BeautifulSoup(snippet, 'html.parser').get_text(separator='\n')
            new_snippet = re.sub(r'\n+', '\n', clean_snippet)
            lyrics += new_snippet.strip()
    sections = re.split(pattern, lyrics)
    results = []
    num_sections = len(sections)
    for idx in range(0,num_sections-1):
        current_section = sections[idx]
        next_section = sections[idx+1]
        if re.search(pattern, current_section) and "Produced" not in current_section and next_section: # the current idx is a valid section header and there is lyrics following it
            if ":" not in current_section:
                current_section = current_section + f": {artist_name}"
            results.append(current_section + next_section)
    return results


def write_lyrics_to_file(artist_names, filename):
    song_infos = []
    artist_infos = []
    for artist_name in artist_names: 
        song_infos.extend(request_song_info(artist_name))
    client = OpenAI(api_key=OPEN_AI_TOKEN)
    num_songs = len(song_infos)
    print(f"Synthesizing {num_songs} songs to {filename}")
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['song_title', 'lyrics', 'prompt'])
        for num, song_info in enumerate(song_infos):
            url, title, artist = song_info
            sections = scrape_song_lyrics(url, artist)
            for lyrics in sections: 
                chat_completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": gpt_prompt(lyrics)},
                    ]
                )
                prompt = chat_completion.choices[0].message.content
                writer.writerow([title, lyrics, prompt])
            numTicks = int(100/num_songs * (num+1))
            print(f'Loading {num+1} / {num_songs}   [ {"|" * numTicks}{" " * (100 - numTicks)}]', end='\r')
    f.close()
    print("\n")
    print(f"Finished writing {num_songs} songs to {filename}")

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
    csv_filename = "train.csv"
    tar_filename = "dataset.tar.gz"
    artist_names = ["Lupe Fiasco", "Common"]
    write_lyrics_to_file(artist_names, csv_filename)
    # with open(csv_filename, 'r', encoding='utf-8') as csvfile:
    #     reader = csv.reader(csvfile)
    #     for row in reader:
    #         print(row)
    # for artist in artist_names:
    #     write_lyrics_to_file(artist, csv_filename)
        # clean_data(jsonl_filename)
    
    # compress_data(tar_filename, jsonl_filename)
    # print(get_all_songs())