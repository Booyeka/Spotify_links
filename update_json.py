from dotenv import load_dotenv
import os
from db_connection import get_db_conn_alc
from sqlalchemy.orm import sessionmaker
from define_db import Album, Artist, Genre, album_artists, album_genres
from sqlalchemy import select, func
from datetime import datetime, timedelta
import json

engine = get_db_conn_alc()
Session = sessionmaker(bind=engine)


# get driver with pole position
with Session() as session:
    cutoff = datetime.now() - timedelta(days=30)

    query = (
        select(
            Album.id,
            Album.name,
            Album.release_date,
            Album.spotify_url,
            Album.cover_image,
            Artist.name.label("artist"),
            Genre.name.label("genre")
        )
        .join(album_artists, Album.id == album_artists.c.album_id)
        .join(Artist, album_artists.c.artist_id == Artist.id)
        .join(album_genres, Album.id == album_genres.c.album_id)
        .join(Genre, album_genres.c.genre_id == Genre.id)
        .where(Album.release_date >= cutoff)
    )

    # print(query)

    # execute query
    results = session.execute(query, {'release_date_1': cutoff}).fetchall()

albums_json = {}

for row in results:
    album_id = row.id
    # Group multiple artists/genres per album
    if album_id not in albums_json:
        albums_json[album_id] = {
            "title": row.name,
            # "release_date": datetime.strptime(row.release_date, '%Y-%m-%d').isoformat(),
            "release_date": row.release_date,
            "spotify_link": row.spotify_url,
            "cover_art": row.cover_image,
            "artists": [row.artist],
            "genres": [row.genre]
        }
    else:
        if row.artist not in albums_json[album_id]["artists"]:
            albums_json[album_id]["artists"].append(row.artist)
        if row.genre not in albums_json[album_id]["genres"]:
            albums_json[album_id]["genres"].append(row.genre)

# convert to list for JSON
albums_list = list(albums_json.values())
albums_list.sort(key=lambda x:x["release_date"])

# write to JSON file
with open("albums.json", "w") as f:
    json.dump(albums_list, f, indent=2)