import datetime
import locale
from pathlib import Path
from collections import namedtuple, defaultdict

import click

from . import croapi
from .main import ClickDate
from .spotify import Spotify


def parse_plname(spoplaylist):
    """
    Parse Spotify playlist object name into tuple containing station
    and date.
    """
    mnum = {
        "ledna": 1, "února": 2, "března": 3, "dubna": 4, "května": 5,
        "června": 6, "července": 7, "srpna": 8, "září": 9, "října": 10,
        "listopadu": 11, "prosince": 12,
    }
    try:
        *s, _, d, m, y = spoplaylist["name"].split(" ")
        d = int(d.rstrip("."))
        m = mnum.get(m)
        y = int(y)
        date = datetime.date(y, m, d)
        station = croapi.get_cro_station_id(" ".join(s))
        return namedtuple("Playlist", "station, date, id")(
            station, date, spoplaylist["id"],
        )
    except ValueError:
        pass


def get_plname(station, month):
    locale.setlocale(locale.LC_TIME, "cs_CZ")
    return "{} TOP {} {}".format(
        croapi.get_cro_station_name(station),
        month.strftime("%B").lower(),
        month.year,
    )


@click.command()
@click.option(
    "--credentials", "-c",
    metavar="<credentials_json_file>",
    show_default=True,
    type=click.Path(dir_okay=False),
    default=str(Path(click.get_app_dir("spotzurnal")) / "credentials.json"),
    help="Path where to store credentials.",
)
@click.option(
    "--username", "-u",
    metavar="USER",
    help="Spotify user name",
)
@click.option(
    "--month", "-m",
    type=ClickDate("%Y-%m"),
    default=datetime.date.today(),
    show_default=True,
    help="The month to aggregate",
)
@click.option(
    "--station", "-s",
    type=click.Choice(croapi.get_cro_stations()),
    default="radiozurnal",
)
@click.option(
    "--mintracks", "-m",
    type=click.INT,
    default=0,
    show_default=True,
    help="Minimum number of tracks in the output playlist",
)
def aggregator(credentials, username, month, station, mintracks):
    """
    Aggregate the most popular songs from daily playlists into a new playlist.
    """
    sp = Spotify(username=username, credfile=credentials)
    playlists = [
        parse_plname(p)
        for p in sp.get_all_data(sp.current_user_playlists, limit=50)
    ]
    playlists = [
        p for p in playlists
        if p
        and p.station == station
        and p.date.year == month.year
        and p.date.month == month.month
    ]
    counts = defaultdict(int)
    for p in playlists:
        print(f"Processing playlist from {p.date:%Y-%m-%d}")
        for t in sp.get_all_data(
            sp.user_playlist_tracks,
            sp.user,
            p.id,
            fields="next,items(track(id))",
        ):
            counts[t["track"]["id"]] += 1
    rating = defaultdict(list)
    for trackid, rate in counts.items():
        rating[rate].append(trackid)
    favtracks = []
    total = 0
    for rate in sorted(rating.keys(), reverse=True):
        tracks = rating[rate]
        if total < mintracks:
            favtracks.extend(tracks)
        total += len(tracks)
        print(f"Count: {rate:2} Tracks: {len(tracks):4} Total: {total:4}")
    if favtracks:
        plname = get_plname(station, month)
        print(plname)
        playlist = sp.get_or_create_playlist(plname)
        click.secho(
            "Playlist URL: https://open.spotify.com/user/"
            f"{sp.user}/playlist/{playlist}",
            bold=True,
        )
        sp.user_playlist_replace_tracks(sp.user, playlist, favtracks[:100])
        sp.put_all_data(
            sp.user_playlist_add_tracks,
            favtracks,
            sp.user,
            playlist,
            offset=100,
        )
