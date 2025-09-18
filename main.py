from bs4 import BeautifulSoup
import requests
import time
import pprint
import requests
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
import os
from db_connection import get_db_conn_alc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from define_db import Album, Artist, Genre


load_dotenv()

links = []
album_dicts = []

def add_links(response):
    # Check if request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all elements with a specific class (example: "headline")
        elements = soup.find_all("div", class_="albumTitle")


        # Example: find all elements with class "child-class"
        children = soup.find_all(class_="albumTitle")

        
        for child in children:
            # Go up one level to the parent
            parent = child.parent  
            # links.append(parent)
            # Optionally, go further up: child.parent.parent

            # Look for an <a> tag inside the parent
            # a_tag = parent.find("a")
            # if a_tag and a_tag.get("href"):
            #     links.append(a_tag["href"])
            if parent.name == "a" and parent.get("href"):
                link = parent["href"]
            links.append(link)
        
        # Print the prettified HTML
        # print(elements)
        # print(links)
    else:
        print(f"Failed to retrieve page. Status code: {response.status_code}")

    time.sleep(1)


def create_dicts(links:list):
    for link in links:
        response2 = session.get(f"https://www.albumoftheyear.org/{link}")

        soup = BeautifulSoup(response2.text, "html.parser")

        # get needed information

        # start with if it has a spotify link to check if its on spotify
        third_party_links = soup.find("div", class_="buyButtons")
        # Look through all <a> tags and check if href contains "open.spotify.com"
        spotify_links = [
            a["href"] for a in third_party_links.find_all("a", href=True)
            if "open.spotify.com" in a["href"]
        ]
        # print(spotify_links)


        # get album name, artist name, release date, genre - list incase of multiple, 
        if spotify_links:
            artist = soup.find("div", class_="artist").text
            album_title = soup.find("h1", class_="albumTitle").text

            release_date = soup.find(string="/ Release Date") # has weird "non breaking space
            parent = release_date.parent.parent.text
            release_date = parent[:-14]

            genre_meta = soup.find_all("meta", attrs={"itemprop": "genre"})
            if genre_meta:
                # Extract content safely
                genres = [tag.get("content") for tag in genre_meta]
            else:
                genres = []  # no genres found

            # print(genres) # list of genres

            album_dicts.append({
                "artist" : artist,
                "album_title" : album_title,
                "release_date" : release_date,
                "genres": genres,
                "spotify_link" : spotify_links
            }
            )
        time.sleep(0.5)


def search_album(album_id):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    url = f"https://api.spotify.com/v1/albums/{album_id}"
    response = requests.get(url, headers=headers)
    data = response.json()

    # Check for errors
    if "error" in data:
        print("Spotify API error:", data["error"])
        return None

    
    album = {
        "name": data["name"],
        "artist": ", ".join([a["name"] for a in data["artists"]]),
        "release_date": data["release_date"],
        "spotify_url": data["external_urls"]["spotify"], # web player
        # "app_uri": item["uri"], # desktop app
        "album_image": data["images"][1]["url"], # only take middle value --- should be height and width of 300
        "id": data["id"]
    }
    return album

def add_album(session, name, release_date, artists, genres, spotify_url, cover_url):
    # check if album already exists
    existing_album = session.query(Album).filter_by(name=name, release_date=release_date).first()
    if existing_album:
        print(f"Album already exists: {name} ({release_date})")
        return existing_album
    album = Album(name=name, release_date=release_date, spotify_url=spotify_url, cover_image=cover_url)
    session.add(album)

    # add artists
    for artist_name in artists:
        artist = session.query(Artist).filter_by(name=artist_name).first()
        if not artist:
            artist = Artist(name=artist_name)
        album.artists.append(artist)

    # add genres
    for genre_name in genres:
        genre = session.query(Genre).filter_by(name=genre_name).first()
        if not genre:
            genre = Genre(name=genre_name)
        album.genres.append(genre)


    print(f"Inserted: {album.name} ({album.release_date})")

    # try:
    #     session.commit()
    #     print(f"Inserted: {album.name} ({album.release_date})")
    # except SQLAlchemyError:
    #     session.rollback()
    #     print(f"Skipped duplicate: {album.name} ({album.release_date})")



if __name__ == "__main__":
    engine = get_db_conn_alc()
    Session = sessionmaker(bind=engine)
    # db_session = Session()

    session = requests.Session()


    # Add headers to mimic a browser
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0 Safari/537.36"
    })



    # Send a GET request to fetch the page content.  getting 3 pages of links incase there were a lot on one day ~ 144 albums
    response = session.get("https://www.albumoftheyear.org/releases/")
    add_links(response)
    response = session.get("https://www.albumoftheyear.org/releases/2")
    add_links(response)
    # response = session.get("https://www.albumoftheyear.org/releases/3")
    # add_links(response)
    # response = session.get("https://www.albumoftheyear.org/releases/4")
    # add_links(response)
    # response = session.get("https://www.albumoftheyear.org/releases/5")
    # add_links(response)
    # response = session.get("https://www.albumoftheyear.org/releases/6")
    # add_links(response)



    create_dicts(links=links) # appends a dictionary to album_dicts with album info
    # pprint.pprint(album_dicts)


    # iterate over album_dicts list and generate spotify links for each

    # get album art url as well

    '''SPOTIFY API'''

    # put these in .env files
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    token_url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}

    resp = requests.post(token_url, headers=headers, data=data)
    access_token = resp.json()["access_token"]

    # Replace with your access token
    ACCESS_TOKEN = access_token

    # album_dicts.sort(key=lambda x: x["release_date"], reverse=True) # sorting to get newest entries first

    with Session() as session:
        # searching spotify api for album - getting link and album art url
        for album in album_dicts:
            # Example usage
            album_id = album["spotify_link"][0].split("/album/")[-1].split("?")[0]
            api_response = search_album(album_id)
            
            if api_response is None:
                continue
            
            # print(result)
            album.update({
                "api_spotify_url" : api_response['spotify_url'],
                "album_image" : api_response['album_image'],
                "id" : api_response['id'],
                "release_date_formatted": api_response["release_date"]
            })

            add_album(session=session,
                    name=album["album_title"],
                    release_date=album["release_date_formatted"],
                    artists=[album["artist"]],
                    genres=album["genres"],
                    spotify_url=album["api_spotify_url"],
                    cover_url=album["album_image"]
                    )
            time.sleep(0.5)

        session.commit()




    