import sqlite3
from collections import namedtuple

from click import secho


class Cache:
    def __init__(self, dbfile=":memory:"):
        self.con = sqlite3.connect(dbfile)
        self.con.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.con:
            self.con.execute("""CREATE TABLE IF NOT EXISTS cro_interprets
                    (interpret_id INTEGER PRIMARY KEY,
                     interpret TEXT)""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS cro_tracks
                    (track_id INTEGER PRIMARY KEY,
                     track TEXT,
                     interpret_id INTEGER
                    )""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS spo_artists
                    (artist_id TEXT PRIMARY KEY,
                     artist TEXT)""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS spo_tracks
                    (track_id TEXT PRIMARY KEY,
                     track TEXT)""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS spo_tracks_artists
                    (track_id TEXT,
                     artist_id TEXT,
                     UNIQUE(track_id, artist_id)
                    )""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS cro_spo_artists
                    (interpret_id INT,
                     artist_id TEXT,
                     UNIQUE(interpret_id, artist_id)
                    )""")
            self.con.execute("""CREATE TABLE IF NOT EXISTS cro_spo_tracks
                    (cro_track_id INT PRIMARY KEY,
                     spo_track_id TEXT
                    )""")

    def store_cro_track(self, track):
        c = self.con.execute(
            "SELECT track_id, track, interpret_id, interpret "
            "FROM cro_tracks JOIN cro_interprets USING(interpret_id) "
            "WHERE track_id = ?",
            (track.track_id,),
        ).fetchone()
        if c:
            tid, t, iid, i = c
            # If this fails, the CRo ids cannot be trusted
            assert track.interpret_id == iid
            # Hard assertion on names fails regularly,
            # maybe some difflib could be used here.
            if track.track != t or track.interpret != i:
                secho(f"Cache: {i} - {t} ({iid} - {tid})", fg="yellow")

        with self.con:
            self.con.execute(
                "INSERT OR IGNORE INTO cro_interprets VALUES (?, ?)",
                (track.interpret_id, track.interpret),
            )
            self.con.execute(
                "INSERT OR IGNORE INTO cro_tracks VALUES (?, ?, ?)",
                (track.track_id, track.track, track.interpret_id),
            )

    def store_spotify_track(self, spotrack, crotrack=None):
        artists = [(a["id"], a["name"]) for a in spotrack["artists"]]
        tracks_artists = [(spotrack["id"], a["id"])
                          for a in spotrack["artists"]]
        with self.con:
            self.con.executemany(
                "INSERT OR IGNORE INTO spo_artists VALUES (?, ?)",
                artists,
            )
            self.con.execute(
                "INSERT OR IGNORE INTO spo_tracks VALUES (?, ?)",
                (spotrack["id"], spotrack["name"]),
            )
            self.con.executemany(
                "INSERT OR IGNORE INTO spo_tracks_artists VALUES (?, ?)",
                tracks_artists,
            )
        if crotrack:
            cro_spo_artists = [(crotrack.interpret_id, a["id"])
                               for a in spotrack["artists"]]
            with self.con:
                self.con.executemany(
                    "INSERT OR IGNORE INTO cro_spo_artists VALUES (?, ?)",
                    cro_spo_artists,
                )
                self.con.execute(
                    "INSERT OR IGNORE INTO cro_spo_tracks VALUES (?, ?)",
                    (crotrack.track_id, spotrack["id"]),
                )

    def lookup_match(self, track):
        r = self.con.execute(
            "SELECT spo_track_id FROM cro_spo_tracks WHERE cro_track_id = ?",
            (track.track_id,),
        ).fetchone()
        if r:
            return r[0]

    def get_unmatched_tracks(self):
        r = self.con.execute(
            "SELECT track_id, interpret_id, track, interpret "
            "FROM cro_tracks JOIN cro_interprets USING(interpret_id) "
            "LEFT JOIN cro_spo_tracks "
            "ON track_id = cro_track_id "
            "WHERE spo_track_id IS NULL",
        )
        for row in r:
            yield namedtuple("Track", row.keys())(**row)
