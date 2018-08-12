#!/usr/bin/env python3

import datetime
import locale
import re
import json
from collections import namedtuple
from difflib import SequenceMatcher
from pathlib import Path

import requests
import dateutil.parser
import spotipy
import spotipy.util
import click
from click_datetime import Datetime


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
            **creds
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
            print(f"↓ Retried as {artist} - {title}")
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
            print(f"↓ Retried as track:{title}")
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
                    print(f"↓ Unmatched with {ar:.2f}, {tr:.2f}")
                    print(
                        "↓ Sp.: {} - {}".format(
                            *self.get_spotify_artist_title(items[0])
                        ),
                    )
                    items = []
        if items:
            ar, tr = self.getratios(track, items[0])
            print(f"↓ Matched with {ar:.2f}, {tr:.2f}")
            print(
                "↓ Sp.: {} - {}".format(
                    *self.get_spotify_artist_title(items[0])
                ),
            )
            return items[0]["id"]

    def add_tracks_to_playlist(
        self, trackids, username="0skat-cz",
        playlistid="2wrkilEEx7SD0OnyZwtGk8",
    ):
        if not isinstance(trackids, list):
            trackids = [trackids, ]
        self.user_playlist_add_tracks(username, playlistid, trackids)

    @staticmethod
    def get_all_data(func, *args, maxlimit=50, **kwargs):
        offset = 0
        results = []
        while True:
            kwargs['limit'] = maxlimit
            kwargs['offset'] = offset
            r = func(*args, **kwargs)
            results.extend(r["items"])
            if r["next"] is None:
                break
            offset += maxlimit
        return results

    @staticmethod
    def put_all_data(func, data, *args, maxlimit=100, offset=0, **kwargs):
        for i in range(offset, len(data), maxlimit):
            func(*args, data[i:i + maxlimit], **kwargs)

    def get_or_create_playlist(self, name, description=""):
        playlists = self.get_all_data(self.current_user_playlists)
        for p in playlists:
            if p["name"] == name:
                return p["id"]
        r = self.user_playlist_create(
            self.user,
            name,
        )
        return r["id"]


def get_cro_day_playlist(station="radiozurnal", date: datetime.date=None):
    """
    Download the playlist from CRo API for a day.
    """
    url = "https://croapi.cz/data/v2/playlist/day/"
    if date:
        url += f"{date:%Y/%m/%d/}"
    url += f"{station}.json"
    r = requests.get(url).json()
    for i in r.get("data", []):
        i['since'] = dateutil.parser.parse(i['since'])
        yield namedtuple("PlaylistItem", i.keys())(**i)


stationnames = {
    "radiozurnal": "Radiožurnál",
    "dvojka": "Dvojka",
    "radiowave": "Radio Wave",
    "regina": "Regina DAB Praha",
}


@click.command()
@click.option(
    "--clientid",
    metavar="<client_secrets_json_file>",
    show_default=True,
    type=click.Path(dir_okay=False, readable=True, exists=True),
    default=str(Path(click.get_app_dir("spotzurnal")) / "clientid.json"),
    help="Path to OAuth2 client secret JSON file.",
)
@click.option(
    "--date",
    type=Datetime(format='%Y-%m-%d'),
    default=datetime.datetime.now(),
)
@click.option(
    "--station",
    type=click.Choice(stationnames.keys()),
    default="radiozurnal",
)
@click.option("--replace/--no-replace")
def main(clientid, date, station, replace):
    sp = Spotify(credfile=clientid)
    locale.setlocale(locale.LC_TIME, "cs_CZ")
    mname = (
        None, "ledna", "února", "března", "dubna", "května", "června",
        "července", "srpna", "září", "října", "listopadu", "prosince",
    )
    plname = "{} {} {}. {} {}".format(
        stationnames[station],
        date.strftime("%A").lower(),
        date.day,
        mname[date.month],
        date.year,
    )
    print(plname)
    playlist = sp.get_or_create_playlist(plname)
    trackids = []
    undiscovered = []
    pl = get_cro_day_playlist(station, date)
    for n, track in enumerate(pl, start=1):
        tid = sp.search_track_id(track)
        print(f"{track.since:%H:%M}: {track.interpret} - {track.track}")
        if tid:
            trackids.append(tid)
        else:
            undiscovered.append(track)
    pct = 100*len(trackids)/n
    print("Discovered {}/{} – {:.0f}%".format(len(trackids), n, pct))
    print("Undiscovered tracks:")
    print("\n".join(
        f"{t.since:%H:%M}: {t.interpret} - {t.track}"
        for t in undiscovered
    ))
    print(
        f"Playlist URL: https://open.spotify.com/user/"
        f"{sp.user}/playlist/{playlist}",
    )
    if replace:
        r = sp.user_playlist_replace_tracks(sp.user, playlist, trackids[:100])
    r = sp.user_playlist_tracks(sp.user, playlist, fields="total")
    sp.put_all_data(
        sp.user_playlist_add_tracks,
        trackids,
        sp.user,
        playlist,
        offset=r["total"],
    )


if __name__ == "__main__":
    main()
