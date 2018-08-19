import datetime
from pathlib import Path

import click
from yaml import safe_load

from . import croapi
from . import matcher
from .spotify import Spotify
from .cache import Cache
from .clickdate import ClickDate
from .aggregator import parse_plname


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
    "--date", "-d",
    type=ClickDate('%Y-%m-%d'),
    default=datetime.date.today(),
    show_default=True,
    help="Date of the playlist",
)
@click.option(
    "--station", "-s",
    type=click.Choice(croapi.get_cro_stations()),
    default="radiozurnal",
)
@click.option(
    "--replace/--no-replace", "-r",
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
    "--quirks", "-q",
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
        q = None
    matcher.match_cro_playlist(sp, date, station, replace, c, q)


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
    type=ClickDate('%Y-%m'),
    default=datetime.date.today(),
    show_default=True,
    help="Month of the playlist",
)
@click.option(
    "--station", "-s",
    type=click.Choice(croapi.get_cro_stations()),
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
    "--quirks", "-q",
    metavar="<quirks_yaml_file>",
    show_default=True,
    type=click.File(),
    help="Path to hand-kept quirks file",
)
def rematch(credentials, username, month, station, cache, quirks):
    """
    Regenerate Spotify playlists from a playlist published
    by the Czech Radio -- possibly using new quirks and cache contents.
    """
    sp = Spotify(username=username, credfile=credentials)
    c = Cache(cache)
    if quirks:
        q = safe_load(quirks)
    else:
        q = None
    playlists = [
        parse_plname(p)
        for p in sp.get_all_data(sp.current_user_playlists, limit=50)
    ]
    playlists = [
        p for p in playlists
        if p
        and ((station is None) or p.station == station)
        and p.date.year == month.year
        and p.date.month == month.month
    ]
    for p in playlists:
        matcher.match_cro_playlist(sp, p.date, p.station, True, c, q)
