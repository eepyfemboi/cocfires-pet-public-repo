import sqlite3
from typing import Dict, Literal
import traceback

conn = sqlite3.connect("music.db")
c = conn.cursor()

def set_metadata(file_path: str, ytid: str, metadata: Dict[str, str], overwrite = True):
    file_path = file_path.replace('/', '\\')
    file_path = 'musicmp3\\' + file_path if 'musicmp3' not in file_path else file_path
    try:
        new = False
        #conn = sqlite3.connect("music.db")
        #c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS songs (path TEXT PRIMARY KEY, title TEXT, artist TEXT, album TEXT, genre TEXT, artwork TEXT, youtubeid TEXT, views INTEGER)")
        try:
            c.execute("SELECT * FROM songs WHERE path = ?", (file_path, ))
            existing = c.fetchone()
            if existing is None:
                new = True
        except Exception as e:
            pass
        if new:
            c.execute(
                "INSERT INTO songs (path, title, artist, album, genre, artwork, youtubeid, views) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                (file_path, metadata.get('title', 'Unknown Title'), metadata.get('artist', 'Unknown Artist'), metadata.get('album', 'Unknown Album'), metadata.get('genre', 'Unknown Genre'), metadata.get('artwork', ''), ytid, 0)
            )
        else:
            if overwrite:
                c.execute(
                    "UPDATE songs SET title = ?, artist = ?, album = ?, genre = ?, artwork = ?, youtubeid = ? WHERE path = ?",
                    (metadata.get('title', 'Unknown Title'), metadata.get('artist', 'Unknown Artist'), metadata.get('album', 'Unknown Album'), metadata.get('genre', 'Unknown Genre'), metadata.get('artwork', ''), ytid, file_path)
                )
        conn.commit()
    except Exception as e:
        traceback.print_exception(e)
    #finally:
        #conn.close()

def update_song_views(file_path: str):
    file_path = file_path.replace('/', '\\')
    file_path = 'musicmp3\\' + file_path if 'musicmp3' not in file_path else file_path
    try:
        #conn = sqlite3.connect("music.db")
        #c = conn.cursor()
        c.execute("SELECT views FROM songs WHERE path = ?", (file_path, ))
        views = int(c.fetchone()) + 1
        c.execute("UPDATE songs SET views = ? WHERE path = ?", (views, file_path))
        conn.commit()
    except Exception as e:
        traceback.print_exception(e)
    #finally:
        #conn.close()

def get_song(file_path: str):
    file_path = file_path.replace('/', '\\')
    file_path = 'musicmp3\\' + file_path if 'musicmp3' not in file_path else file_path
    try:
        #conn = sqlite3.connect("music.db")
        #c = conn.cursor()
        c.execute("SELECT * FROM songs WHERE path LIKE ?", (file_path, ))
        metadata = c.fetchone()
        path, title, artist, album, genre, artwork, ytid, views = metadata
        metadata = {
            'title': title,
            'artist': artist,
            'album': album,
            'genre': genre,
            'artwork': artwork,
            'ytid': ytid,
            'views': views
        }
        return metadata
    except Exception as e:
        traceback.print_exception(e)
        return None
    #finally:
        #conn.close()

def search_songs(query: str, meta: Literal['title', 'artist', 'album', 'genre'] = None):
    try:
        songs = []
        #conn = sqlite3.connect("music.db")
        #c = conn.cursor()
        queries = query.split(" ")
        fields = ['title', 'artist', 'album', 'genre']
        for query in queries:
            for field in fields:
                c.execute(f"SELECT * FROM songs WHERE {field} LIKE ?", ('%' + query + '%',))
                results = c.fetchall()
                for result in results:
                    if result not in songs:
                        songs.append(result)
        return songs
    except Exception as e:
        traceback.print_exception(e)
    #finally:
        #conn.close()

def search_songs_by_meta(meta: Dict[str, str]):
    try:
        songs = []
        #conn = sqlite3.connect("music.db")
        #c = conn.cursor()
        insert = ''
        if len(meta) == 0:
            return []
        artist = None
        album = None
        genre = None
        items = []
        fields = []
        if meta.get('artist', None) is not None:
            insert += 'CASE WHEN artist LIKE ? THEN 1 ELSE 0 END + CASE WHEN artist = ? THEN 3 ELSE 0 END'
            artist = meta.get('artist')
            items.append('artist')
            fields.append(artist)
            fields.append(artist)
        if meta.get('album', None) is not None:
            if insert != '':
                insert += ' + '
            insert += 'CASE WHEN album LIKE ? THEN 1 ELSE 0 END + CASE WHEN album = ? THEN 3 ELSE 0 END'
            album = meta.get('album')
            items.append('album')
            fields.append(album)
            fields.append(album)
        if meta.get('genre', None) is not None:
            if insert != '':
                insert += ' + '
            insert += 'CASE WHEN genre LIKE ? THEN 1 ELSE 0 END + CASE WHEN album = ? THEN 3 ELSE 0 END'
            genre = meta.get('genre')
            items.append('genre')
            fields.append(genre)
            fields.append(genre)
        query = f"SELECT *, ({insert}) AS match_score FROM songs ORDER BY match_score DESC;"
        #for field, value in meta:
        #    c.execute(f"SELECT * FROM songs WHERE {field} LIKE ?", ('%' + value + '%',))
        #    results = c.fetchall()
        #    for result in results:
        #        if result not in songs:
        #            songs.append(result)
        c.execute(query, tuple(fields))
        results = c.fetchall()
        for result in results:
            if result not in songs:
                songs.append(result)
        return songs
    except Exception as e:
        traceback.print_exception(e)

def find_similar_songs(file_path: str):#, item_to_return = None):
    file_path = file_path.replace('/', '\\')
    file_path = 'musicmp3\\' + file_path if 'musicmp3' not in file_path else file_path
    try:
        songs = []
        #conn = sqlite3.connect('music.db')
        #c = conn.cursor()
        existing = get_song(file_path)
        if existing is not None:
            album = existing.get('album', None)
            artist = existing.get('artist', None)
            genre = existing.get('genre', None)
            if album == 'Unknown Album':
                album = None
            if artist == 'Unknown Artist':
                artist = None
            if genre == 'Unknown Genre':
                genre = None
            meta = {}
            if artist is not None:
                meta['artist'] = artist
            if album is not None:
                meta['album'] = album
            if genre is not None:
                meta['genre'] = genre
            songs = search_songs_by_meta(meta)
            #print(songs)
            return songs
    except Exception as e:
        traceback.print_exception(e)
