#!/usr/bin/env python3

import re
import json
from difflib import SequenceMatcher
from pathlib import Path

import spotipy
import spotipy.util
import click


class Spotify(spotipy.Spotify):
    def __init__(
        self,
        username="wx6cq56wxecdscpcmaiu2gd9r",
        scope="playlist-modify-public",
        credfile="clientid.json",
    ):
        credfile = Path(credfile)
        with credfile.open() as f:
            creds = json.load(f)
        token = spotipy.util.prompt_for_user_token(
            username,
            scope=scope,
            cache_path=credfile.parent / f"cache-{username}.json",
            **creds,
        )
        self.user = username
        super().__init__(auth=token)

    @staticmethod
    def get_spotify_artist_title(spotrack):
        spoartist = ", ".join(a["name"] for a in spotrack["artists"])
        spotitle = spotrack["name"]
        return spoartist, spotitle

    @classmethod
    def getratios(cls, track, spotrack):
        sm = SequenceMatcher(lambda x: x in " ,;&()''`")
        artist = track.interpret.lower().replace("´", "'")
        title = track.track.lower().replace("´", "'")
        spoartist, spotitle = (x.lower() for x in
                               cls.get_spotify_artist_title(spotrack))
        sm.set_seqs(artist, spoartist)
        aratio = sm.ratio()
        sm.set_seqs(title, spotitle)
        tratio = sm.ratio()
        return aratio, tratio

    def search_track_id(self, track):
        artist = track.interpret.lower().replace("´", "'")
        title = track.track.lower().replace("´", "'")
        artist, title = [re.sub(r"([,.])([^\s])", r"\1 \2", x)
                         for x in [artist, title]]
        r = self.search(
            f"artist:{artist} "
            f"track:{title}",
            type="track",
            limit=1,
            market="CZ",
        )
        items = r["tracks"]["items"]
        if not items:
            # Retry with only first artist and without parentheses in title
            artist = artist.split(",")[0].split("/")[0].split("&")[0]
            artist = artist.split("feat")[0].split("ft. ")[0]
            title = title.split("(")[0].split("feat")[0].split("ft. ")[0]
            click.secho(f"^ Retried as {artist} - {title}", fg="yellow")
            r = self.search(
                f"artist:{artist} "
                f"track:{title}",
                type="track",
                limit=1,
                market="CZ",
            )
            items = r["tracks"]["items"]
        if not items:
            # Retry with just title
            click.secho(f"^ Retried as track:{title}", fg="yellow")
            r = self.search(
                f"track:{title}",
                type="track",
                limit=1,
                market="CZ",
            )
            items = r["tracks"]["items"]
            if items:
                ar, tr = self.getratios(track, items[0])
                if ar < 0.5:
                    click.secho(
                        "^ Sp.: {} - {}".format(
                            *self.get_spotify_artist_title(items[0])
                        ),
                        fg="red",
                    )
                    click.secho(
                        f"^ Unmatched with {ar:.2f}, {tr:.2f}",
                        fg="red",
                    )
                    items = []
            else:
                click.secho("^ Not found", fg="red")
        if items:
            ar, tr = self.getratios(track, items[0])
            click.secho(
                "^ Sp.: {} - {}".format(
                    *self.get_spotify_artist_title(items[0])
                ),
                fg="green",
            )
            click.secho(f"^ Matched with {ar:.2f}, {tr:.2f}", fg="green")
            return items[0]["id"]

    def add_tracks_to_playlist(
        self, trackids, username="0skat-cz",
        playlistid="2wrkilEEx7SD0OnyZwtGk8",
    ):
        if not isinstance(trackids, list):
            trackids = [trackids, ]
        self.user_playlist_add_tracks(username, playlistid, trackids)

    def get_all_data(self, func, *args, **kwargs):
        r = func(*args, **kwargs)
        results = r["items"]
        while r["next"]:
            r = self.next(r)
            results.extend(r["items"])
        return results

    @staticmethod
    def put_all_data(func, data, *args, limit=100, offset=0, **kwargs):
        for i in range(offset, len(data), limit):
            func(*args, data[i:i + limit], **kwargs)

    def get_or_create_playlist(self, name, description=""):
        playlists = self.get_all_data(self.current_user_playlists, limit=50)
        for p in playlists:
            if p["name"] == name:
                return p["id"]
        r = self.user_playlist_create(
            self.user,
            name,
        )
        return r["id"]
