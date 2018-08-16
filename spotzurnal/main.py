import datetime
import locale
from pathlib import Path

import click
from yaml import safe_load

from . import croapi
from . import matcher
from .spotify import Spotify
from .cache import Cache


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
            return datetime.datetime.strptime(value, self.fmt).date()
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
    "--credentials",
    metavar="<credentials_json_file>",
    show_default=True,
    type=click.Path(dir_okay=False),
    default=str(Path(click.get_app_dir("spotzurnal")) / "credentials.json"),
    help="Path where to store credentials.",
)
@click.option(
    "--username",
    metavar="USER",
    help="Spotify user name",
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
@click.option(
    "--cache",
    metavar="<cache_sqlite_file>",
    show_default=True,
    type=click.Path(dir_okay=False),
    default=str(Path(click.get_app_dir("spotzurnal")) / "cache.sqlite"),
    help="Path to SQLite cache. (Created if necessary)",
)
@click.option(
    "--quirks",
    metavar="<quirks_yaml_file>",
    show_default=True,
    type=click.File(),
    help="Path to hand-kept quirks file",
)
def main(credentials, username, date, station, replace, cache, quirks):
    """
    Generate a Spotify playlist from a playlist published
    by the Czech Radio.
    """
    sp = Spotify(username=username, credfile=credentials)
    c = Cache(cache)
    if quirks:
        q = safe_load(quirks)
    else:
        q = {"artists": {}, "tracks": {}}
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
    spotracks = []
    undiscovered = []
    pl = croapi.get_cro_day_playlist(station, date)
    for n, track in enumerate(pl, start=1):
        print(f"{track.since:%H:%M}: {track.interpret} - {track.track}")
        c.store_cro_track(track)
        if track.track_id in q["tracks"]:
            m = q["tracks"][track.track_id]
            prefix = "spotify:track:"
            if m.startswith(prefix):
                m = m[len(prefix):]
        else:
            m = c.lookup_match(track)
        if m:
            click.secho("^ Matched from the cache/quirks", fg="green")
            t = {"id": m}
        else:
            interpret = track.interpret
            if track.interpret_id in q["artists"]:
                interpret = q["artists"][track.interpret_id]
                print(f"Corrected artist to {interpret}")
            t = matcher.search_spotify_track(sp, interpret, track.track)
            if t:
                c.store_spotify_track(t, track)
        if t:
            spotracks.append(t)
        else:
            undiscovered.append(track)
    discovered = len(spotracks)
    if discovered < 1:
        raise SystemExit("No tracks found!")
    pct = 100*discovered/n
    click.secho(f"Discovered {discovered}/{n} – {pct:.0f}%", bold=True)
    if undiscovered:
        click.secho("Undiscovered tracks:", bold=True, fg="red")
        print("\n".join(
            f"{t.since:%H:%M}: {t.interpret} ({t.interpret_id}) - "
            f"{t.track} ({t.track_id})"
            for t in undiscovered
        ))
    playlist = sp.get_or_create_playlist(plname)
    click.secho(
        "Playlist URL: https://open.spotify.com/user/"
        f"{sp.user}/playlist/{playlist}",
        bold=True,
    )
    trackids = [t["id"] for t in spotracks]
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
    else:
        sp.put_all_data(
            sp.user_playlist_add_tracks,
            trackids,
            sp.user,
            playlist,
            offset=total,
        )
