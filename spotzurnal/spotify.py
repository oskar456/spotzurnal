#!/usr/bin/env python3

import os
import os.path
import re
import json
from difflib import SequenceMatcher

import spotipy
from spotipy import oauth2
import click


def handle_oauth(credfile, username=None, scope=""):
    save_creds = False
    try:
        with open(credfile) as f:
            creds = json.load(f)
    except IOError:
        creds = {}
        save_creds = True

    if "client_id" not in creds:
        creds["client_id"] = input("Enter Spotify App Client ID: ")
        save_creds = True
    if "client_secret" not in creds:
        creds["client_secret"] = input("Enter Spotify App Client Secret: ")
        save_creds = True
    if "redirect_uri" not in creds:
        creds["redirect_uri"] = "http://localhost:8080/"
        click.secho(
            f"Please add redirect URI \"{creds['redirect_uri']}\" "
            "to the white-list in the Spotify App settings.", bold=True,
        )
        save_creds = True
    sp_oauth = oauth2.SpotifyOAuth(
        scope=scope,
        **{
            k: v for k, v in creds.items() if k in [
                "client_id",
                "client_secret",
                "redirect_uri",
            ]
        },
    )
    if "refresh_token" not in creds:
        auth_url = sp_oauth.get_authorize_url()
        print(f"\nPlease navigate to: {auth_url}")
        response = input("Enter the URL you were redirected to: ")
        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
        creds["refresh_token"] = token_info["refresh_token"]
        save_creds = True
    else:
        token_info = sp_oauth.refresh_access_token(creds["refresh_token"])
    if "username" not in creds:
        creds["username"] = username or input("Enter Spotify User name: ")
        save_creds = True
    if save_creds:
        os.makedirs(os.path.dirname(credfile), mode=0o700, exist_ok=True)
        with open(credfile, "w") as f:
            json.dump(creds, f)
    return username or creds["username"], token_info["access_token"]


class Spotify(spotipy.Spotify):
    def __init__(
        self,
        credfile="clientid.json",
        username=None,
        scope="playlist-modify-public",
    ):
        self.user, token = handle_oauth(credfile, username, scope)
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
