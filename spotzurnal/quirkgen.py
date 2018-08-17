import sys
from pathlib import Path

import click
from yaml import safe_load

from .cache import Cache


@click.command()
@click.option(
    "--cache",
    metavar="<cache_sqlite_file>",
    show_default=True,
    type=click.Path(dir_okay=False),
    default=str(Path(click.get_app_dir("spotzurnal")) / "cache.sqlite"),
    help="Path to SQLite cache.",
)
@click.option(
    "--quirks",
    metavar="<quirks_yaml_file>",
    show_default=True,
    type=click.File(),
    help="File with existing quirks",
)
@click.option(
    "--output",
    metavar="<output_yaml_file>",
    show_default=True,
    type=click.File('w'),
    default=sys.stdout,
    help="Output file.",
)
def quirkgen(cache, quirks, output):
    """
    Get all unmatched songs from cache. Add them to quirks file for manual
    resolution.
    """
    if quirks:
        q = safe_load(quirks)
    else:
        q = {"artists": {}, "tracks": {}}
    c = Cache(cache)
    tracks = c.get_unmatched_tracks()
    # We generate our custom YAML with coments
    output.write("---\n\ntracks:\n")
    for t in tracks:
        quirk = q["tracks"].pop(t.track_id, "")
        output.write(
            f"# {t.interpret} ({t.interpret_id}) - {t.track}\n"
            f"  {t.track_id}: \"{quirk}\"\n",
        )
    for k, v in q["tracks"].items():
        output.write(f"  {k}: \"{v}\"\n")
    output.write("\nartists:\n")
    for k, v in q["artists"].items():
        output.write(f"  {k}: \"{v}\"\n")
    output.write("\n...\n")
