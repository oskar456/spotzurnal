import datetime
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
