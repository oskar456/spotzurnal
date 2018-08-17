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
    type=click.Path(dir_okay=False, exists=True),
    default=str(Path(click.get_app_dir("spotzurnal")) / "cache.sqlite"),
    help="Path to SQLite cache.",
)
@click.option(
    "--quirks", "-q",
    metavar="<quirks_yaml_file>",
    show_default=True,
    type=click.Path(dir_okay=False, exists=True),
    help="File with existing quirks",
)
@click.option(
    "--output", "-o",
    metavar="<output_yaml_file>",
    show_default=True,
    type=click.File('w'),
    default=sys.stdout,
    help="Output file.",
)
@click.option(
    "--in-place", "-i",
    is_flag=True,
    help="Edit quirks file in place.",
)
def quirkgen(cache, quirks, output, in_place):
    """
    Get all unmatched songs from cache. Add them to quirks file for manual
    resolution.
    """
    if in_place and output != sys.stdout:
        sys.exit(click.style(
            "Error: --in-place and --output cannot be used together",
            fg="red",
        ))
    if quirks:
        q = safe_load(Path(quirks).read_text())
    else:
        q = {"artists": {}, "tracks": {}}
    c = Cache(cache)
    tracks = c.get_unmatched_tracks()
    # We generate our custom YAML with coments
    out = []
    out.append("---\n\ntracks:")
    for t in tracks:
        quirk = q["tracks"].pop(t.track_id, "")
        out.append(f"# {t.interpret} ({t.interpret_id}) - {t.track}")
        out.append(f"  {t.track_id}: \"{quirk}\"")
    for k, v in q["tracks"].items():
        t = c.get_cro_track(k)
        if t:
            out.append(f"# {t.interpret} ({t.interpret_id}) - {t.track}")
        out.append(f"  {k}: \"{v}\"")
    out.append("\nartists:")
    for k, v in q["artists"].items():
        a = c.get_cro_interpret(k)
        if a:
            out.append(f"# {a.interpret}")
        out.append(f"  {k}: \"{v}\"")
    out.append("\n...\n")
    if in_place:
        output = open(quirks, "w")
    with output:
        output.write("\n".join(out))
