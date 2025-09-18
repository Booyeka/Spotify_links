from sqlalchemy import (
    create_engine, Column, Integer, String, Table,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from db_connection import get_db_conn_alc
Base = declarative_base()

# Association tables
album_artists = Table(
    "album_artists", Base.metadata,
    Column("album_id", ForeignKey("albums.id"), primary_key=True),
    Column("artist_id", ForeignKey("artists.id"), primary_key=True)
)

album_genres = Table(
    "album_genres", Base.metadata,
    Column("album_id", ForeignKey("albums.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True)
)

# Tables
class Album(Base):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    release_date = Column(String(255))  # keep as string if API returns YYYY or YYYY-MM-DD
    spotify_url = Column(String(255), unique=True)
    cover_image = Column(String(255))

    # Prevent duplicate albums with same name + release_date
    __table_args__ = (
        UniqueConstraint("name", "release_date", name="uix_album_name_date"),
    )

    artists = relationship("Artist", secondary=album_artists, back_populates="albums")
    genres = relationship("Genre", secondary=album_genres, back_populates="albums")


class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)

    albums = relationship("Album", secondary=album_artists, back_populates="artists")


class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)

    albums = relationship("Album", secondary=album_genres, back_populates="genres")




''' create tables in db '''
# engine = get_db_conn_alc()

# Drop all tables (careful — this wipes existing data!)
# Base.metadata.drop_all(engine)

# One line to create all tables
# Base.metadata.create_all(engine)

