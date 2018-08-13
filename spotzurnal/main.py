#!/usr/bin/env python3

import datetime
import locale
from pathlib import Path

import click

from . import croapi
from .spotify import Spotify


class ClickDate(click.ParamType):
    """
    A date object parsed via datetime.strptime.
    """

    name = "date"

    def __init__(self, fmt):
        self.fmt = fmt

    def get_metavar(self, param):
        return self.fmt

    def convert(self, value, param, ctx):
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.date.strptime(value, self.fmt)
        except ValueError as ex:
            self.fail(
                'Could not parse datetime string "{datetime_str}"'
                'formatted as {format} ({ex})'.format(
                    datetime_str=value,
                    format=self.fmt,
                    ex=ex,
                ),
                param,
                ctx,
            )


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
    type=ClickDate('%Y-%m-%d'),
    default=datetime.date.today(),
    show_default=True,
    help="Date of the playlist",
)
@click.option(
    "--station",
    type=click.Choice(croapi.get_cro_stations()),
    default="radiozurnal",
)
@click.option(
    "--replace/--no-replace",
    help="Replace existing playlist instead of appending",
)
def main(clientid, date, station, replace):
    """
    Generate a Spotify playlist from a playlist published
    by the Czech Radio.
    """
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
        print(f"{track.since:%H:%M}: {track.interpret} - {track.track}")
        tid = sp.search_track_id(track)
        if tid:
            trackids.append(tid)
        else:
            undiscovered.append(track)
    discovered = len(trackids)
    pct = 100*discovered/n
    click.secho(f"Discovered {discovered}/{n} – {pct:.0f}%", bold=True)
    click.secho("Undiscovered tracks:", bold=True, fg="red")
    print("\n".join(
        f"{t.since:%H:%M}: {t.interpret} - {t.track}"
        for t in undiscovered
    ))
    playlist = sp.get_or_create_playlist(plname)
    click.secho(
        "Playlist URL: https://open.spotify.com/user/"
        f"{sp.user}/playlist/{playlist}",
        bold=True,
    )
    if replace:
        sp.user_playlist_replace_tracks(sp.user, playlist, trackids[:100])
    total = sp.user_playlist_tracks(sp.user, playlist, fields="total")["total"]
    if 0 < total < discovered and not replace:
        print(
            "Keeping {} tracks already in playlist, adding {} more.".format(
                total, discovered - total,
            ),
        )
    if total >= discovered and not replace:
        print("No new tracks discovered.")
    sp.put_all_data(
        sp.user_playlist_add_tracks,
        trackids,
        sp.user,
        playlist,
        offset=total,
    )
