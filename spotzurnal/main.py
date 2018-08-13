#!/usr/bin/env python3

import datetime
import locale
from pathlib import Path

import click
from click_datetime import Datetime

from . import croapi
from .spotify import Spotify


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
    type=click.Choice(croapi.get_cro_stations()),
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
        croapi.get_cro_station_name(station),
        date.strftime("%A").lower(),
        date.day,
        mname[date.month],
        date.year,
    )
    print(plname)
    trackids = []
    undiscovered = []
    n = 0
    pl = croapi.get_cro_day_playlist(station, date)
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
    playlist = sp.get_or_create_playlist(plname)
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
