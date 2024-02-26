import requests
import re
from bs4 import BeautifulSoup
import json
from ytmusicapi import YTMusic
import urllib
from selenium import webdriver
from langdetect import detect_langs

ACCESS_TOKEN='Am0j_AT5WLWaoi06MnmRSIiA5EPAV5hr1VeipuwZpLGrcvsgZ8mQvCfGJOnTK6H4'

def get_youtube_link(artist_name, song_name):
    ytmusic = YTMusic()

    search_results = ytmusic.search(f'{artist_name} {song_name} audio')
    # Make a lambda function to return a song url
    i = 0
    while search_results[i]['resultType'] not in ['video', 'song'] and i<5:
        i += 1
    #print(search_results[i])
    if i == 5:
        print(search_results[:5])
        return None
    song_id = search_results[i]['videoId']

    return f"https://www.youtube.com/watch?v={song_id}"

def is_english(lyrics): 
    try: 
        langs = detect_langs(lyrics) 
        if len(langs) == 1:
            return langs[0].lang == "en"
        lang_one, lang_two = langs[0], langs[1]
        if langs[0].lang != "en" or langs[1].prob > 0.15:
            return False
        return True
        # for item in langs: 
        #     # The first one returned is usually the one that has the highest probability
        #     return item.lang, item.prob 
    except: return "err", 0.0 

def extract_key_bpm(artist_name, song_title):
    base_url = "https://tunebat.com"
    alt_headers = {
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    artist = artist_name.replace(' ', '%20')
    song_title = song_title.replace('+', '%2B')
    song_title = song_title.replace(' ', '%20')
    search_url = f"{base_url}/Search?q={song_title}%20{artist}"

    # send GET request
    driver = web_driver()
    driver.get(search_url)

    # create a BeautifulSoup object and specify the parser
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # response = requests.get(search_url, headers=alt_headers)
    # soup = BeautifulSoup(response.text, 'html.parser')
    print(soup)

    key_bpm_data = soup.find_all('div', {'class': 'k43JJ'})
    key = key_bpm_data[0].find('p', {'class': 'lAjUd'}).text
    bpm = key_bpm_data[1].find('p', {'class': 'lAjUd'}).text

    return key, bpm

# def search_artist_id(artist_name, access_token):
#     base_url = "https://api.genius.com"
#     #headers = {"Authorization": f"Bearer {access_token}"}
#     headers = {
#       "Authorization": f"Bearer {ACCESS_TOKEN}",
#       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
#     }
#     search_url = f"{base_url}/search?q={artist_name}"
#     response = requests.get(search_url, headers=headers)

#     if response.status_code != 200:
#         raise Exception(f"Request failed with status code {response.status_code} and {response.text}")

#     data = response.json()
#     # print(data)
#     for hit in data["response"]["hits"]:
#         if hit["result"]["primary_artist"]["name"].lower() == artist_name.lower():
#             # print(hit["result"]["primary_artist"]["id"])
#             return hit["result"]["primary_artist"]["id"]

#     return None

def get_song_lyrics(artist_name, song_title, access_token):
    base_url = "https://api.genius.com"
    headers = {
      "Authorization": f"Bearer {ACCESS_TOKEN}",
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    #headers = {"Authorization": f"Bearer {access_token}"}
    # print(headers)
    artist = artist_name.replace(' ', '%20')
    song_title_search = song_title.replace('+', '%2B')
    song_title_search = song_title_search.replace(' ', '%20')
    search_url = f"{base_url}/search?q={artist}%20{song_title_search}"
    response = requests.get(search_url, headers=headers)
    # print(search_url)

    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code} and {response.text}")

    data = response.json()
    lyrics = ""
    # print(data)

    hits = data["response"]["hits"]
    found = False
    hit_num = 0
    while not found and hit_num < len(hits):
        hit = hits[hit_num]
        # print(hit["result"])
        if hit["result"]["primary_artist"]["url"][27:].replace('-', ' ').lower() == artist_name.lower() or hit["result"]["title"] == song_title:
            found = True
            print('found')
            print(hit["result"]["primary_artist"]["id"])
            lyrics, sections = get_lyrics(hit["result"]["api_path"], access_token)
        hit_num += 1

    if not found or lyrics == "":
        return None, None

    return lyrics, sections

# def get_songs(artist_id, access_token):
#     base_url = "https://api.genius.com"
#     headers = {
#       "Authorization": f"Bearer {ACCESS_TOKEN}",
#       "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
#     }
#     url = f"{base_url}/artists/{artist_id}/songs"
#     params = {"sort": "title", "per_page": 50, "page": 1}
#     songs = []

#     while True:
#         response = requests.get(url, headers=headers, params=params)
#         if response.status_code != 200:
#             raise Exception(f"Request failed with status code {response.status_code} and {response.text}")

#         data = response.json()
#         songs.extend(data["response"]["songs"])

#         if not data["response"]["next_page"]:
#             break

#         params["page"] += 1
#     print(songs)
#     song_json = json.dumps(songs)

#     with open('songs.json', 'w') as f:
#         json.dump(song_json, f)
#     return songs


def get_lyrics(api_path, access_token):
    base_url = "https://api.genius.com"
    headers = {
      "Authorization": f"Bearer {ACCESS_TOKEN}",
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    alt_headers = {
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    search_url = base_url+api_path
    #print(search_url)
    response = requests.get(search_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}, {response.text}")

    data = response.json()
    print(data["response"]["song"]["url"])

    response = requests.get(data["response"]["song"]["url"])

    page = response.text

    #print(page)

    soup = BeautifulSoup(page, 'html.parser')

    lyrics_div = soup.find('div', class_='lyrics')

    if lyrics_div is not None:
        lyrics = lyrics_div.text.strip()
    else:
        lyrics = ''
        for elem in soup.find_all('div', class_=lambda value: value and value.startswith("Lyrics__Container")):
            # print(elem.decode_contents())
            if elem.text:
                snippet = elem.decode_contents().replace('<br/>', '\n').replace('<br>', '\n')
                snippet = snippet.replace('<i>', '').replace('</i>', '').replace('<b>', '').replace('</b>', '')
                # print(snippet)
                clean_snippet = BeautifulSoup(snippet, 'html.parser').get_text(separator='\n')
                print(clean_snippet, 'clean_snippet')
                lyrics += clean_snippet.strip() + '\n\n'

    if not lyrics:
        return None
    lyrics, sections = clean_lyrics(lyrics.strip())

    print(lyrics, sections)
    return lyrics, sections
    #if is_english(lyrics):
    #    return lyrics, sections
    #else:
    #    return None, None 



def clean_lyrics(lyrics):
    sections = []
    cleaned_lyrics = []
    lines = lyrics.split('\n')  # split the lyrics into lines
    current_section = None
    current_lyrics = []

    for line in lines:
        print(line, 'is a line')
        line = re.sub(r'\(.*?\)', '', line) # remove all words in parentheses
        if line.startswith('[') and line.endswith(']'): # if the line is a section title
            if current_section is not None: # if there's a current section
                # append the section and the lyrics to sections list
                if len(current_lyrics) > 0:
                    sections.append({'section_title': current_section, 'lyrics': ' '.join(current_lyrics)})
                    current_lyrics = [] # reset current lyrics

            # set the new section    
            current_section = line.strip('[]').split(':')[0] if ':' in line else line.strip('[]')
 
        else:
            if current_section is None:
                cleaned_lyrics.append(line.encode('ascii', 'ignore').decode() + ' ')
                current_lyrics.append(line.encode('ascii', 'ignore').decode() + ' ')

    # add the last section
    if current_section is not None and current_lyrics:
        sections.append({'section_title': current_section, 'lyrics': '\n'.join(current_lyrics)})

    # join the cleaned lyrics with a newline character and return
    return '\n'.join(cleaned_lyrics), sections

if __name__ == '__main__':
    # songs = [
    #     {'song_title': 'Better', 'artist_name': 'Khalid'},
    #     {'song_title': 'deja vu', 'artist_name': 'Olivia Rodrigo'},
    #     {'song_title': 'Flowers', 'artist_name': 'Miley Cyrus'},
    #     {'song_title': 'positions', 'artist_name': 'Ariana Grande'},
    #     {'song_title': '34+35', 'artist_name': 'Ariana Grande'},
    #     {'song_title': 'Die For You', 'artist_name': 'The Weeknd'},
    #     {'song_title': 'I Like Me Better', 'artist_name': 'Lauv'},
    #     {'song_title': 'Attention', 'artist_name': 'Charlie Puth'},
    #     {'song_title': 'Glimpse of Us', 'artist_name': 'Joji'},
    #     {'song_title': 'I Like You (A Happier Song)', 'artist_name': 'Post Malone'},
    #     {'song_title': 'Until I Found You', 'artist_name': 'Stephen Sanchez'},
    #     {'song_title': 'Sunroof', 'artist_name': 'Nicky Youre'},
    #     {'song_title': 'Fingers Crossed', 'artist_name': 'Lauren Spencer Smith'},
    #     {'song_title': 'Butter', 'artist_name': 'BTS'},
    #     {'song_title': 'Heartbreak Anniversary', 'artist_name': 'Giveon'},
    #     {'song_title': 'Watermelon Sugar', 'artist_name': 'Harry Styles'},
    #     {'song_title': "Don't Start Now", 'artist_name': 'Dua Lipa'},
    #     {'song_title': 'everything i wanted', 'artist_name': 'Billie Eilish'},
    #     {'song_title': 'No Idea', 'artist_name': 'Don Toliver'},
    #     {'song_title': 'you broke me first', 'artist_name': 'Tate McRae'}
    # ]

    # song_file = "sabrina_songs.jsonl"
    # new_file = "sabrina_songs_with_lyrics.jsonl"

    # i = 0
    # with open(new_file, 'a') as jsonl_file:
    #     with open(song_file, mode='r') as infile:
    #         for line in infile:
    #             track = json.loads(line)
    #             try:
    #                 print(track['artist'], track['title'])
    #                 lyrics, sections = get_song_lyrics(track['artist'], track['title'], ACCESS_TOKEN)
                    
    #                 track['lyrics'] = lyrics
    #                 track['sections'] = sections

    #                     # track['video'] = get_youtube_link(track['artist_name'], track['track_name'])
    #                     # print('video link at ', track['video'])

    #                 #     if track['video'] is not None:
    #                 jsonl_file.write(json.dumps(track) + '\n')
    #                 #         print('lyrics info dumped')
    #                 # else:
    #                 #     print('genius link not found or corrupt lyrics or lyrics not english')
    #             except Exception as e:
    #                 continue
    #             if i % 100 == 0:
    #                 print(i)
    #             i += 1
                


    # for song in songs:
    #     lyrics, sections = get_song_lyrics(song['artist_name'], song['track_name'], ACCESS_TOKEN)
    #     song['lyrics'] = lyrics
    #     song['sections'] = sections
    #     print('----------------------------------')

    #     video = get_video(song['artist_name'], song['song_title'])
    #     song['video'] = video
    #     print('----------------------------------')

    #     # key, bpm = extract_key_bpm(song['artist_name'], song['song_title'])
    #     # song['key'] = key
    #     # song['bpm'] = bpm
    #     # print(key, bpm)
    #     print('----------------------------------')

    # # export to json
    # with open('songs_v2.json', 'w') as f:
    #     json.dump(songs, f)
                
    print(get_song_lyrics("Lupe Fiasco", "Black SkinHead", ACCESS_TOKEN))