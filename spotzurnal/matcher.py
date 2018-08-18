
from difflib import SequenceMatcher

import click


def get_spotify_artist_title(spotrack):
    spoartist = ", ".join(a["name"] for a in spotrack["artists"])
    spotitle = spotrack["name"]
    return spoartist, spotitle


def print_spotify_track(spotrack, **kwargs):
    click.secho(
        "^ Sp.: {} - {}".format(
            *get_spotify_artist_title(spotrack)
        ),
        **kwargs,
    )


def get_ratios(spotrack, croartist, crotitle):
    sm = SequenceMatcher(lambda x: x in " ,;&()''`")
    artist = croartist.lower().replace("´", "'")
    title = crotitle.lower().replace("´", "'")
    spoartist, spotitle = (x.lower() for x in
                           get_spotify_artist_title(spotrack))
    sm.set_seqs(artist, spoartist)
    aratio = sm.ratio()
    sm.set_seqs(title, spotitle)
    tratio = sm.ratio()
    return aratio, tratio


def search_spotify_track(sp, croartist, crotitle):
    """Do a Spotify search for a track of an artist."""

    artist = croartist.lower().replace("´", "'").replace("+", " ")
    title = crotitle.lower().replace("´", "'").replace("+", " ")
    r = sp.search(
        f"artist:{artist} "
        f"track:{title}",
        type="track",
        limit=10,
        market="CZ",
    )
    items = r["tracks"]["items"]
    if not items:
        # Retry with only first artist and without parentheses in title
        artist2 = artist.split(",")[0].split("/")[0].split("&")[0]
        artist2 = artist2.split("feat")[0].split("ft.")[0]
        title2 = title.split("(")[0].split("feat")[0].split("ft. ")[0]
        if artist2 != artist or title2 != title:
            click.secho(f"^ Retrying as {artist2} - {title2}", fg="yellow")
            r = sp.search(
                f"artist:{artist2} track:{title2}",
                type="track",
                limit=10,
                market="CZ",
            )
            items = r["tracks"]["items"]
    if not items:
        # Retry with just title
        title = title.translate(str.maketrans(",;&()", "     ", ".''`"))
        click.secho(f"^ Retrying as track:{title}", fg="yellow")
        r = sp.search(
            f"track:{title}",
            type="track",
            limit=10,
            market="CZ",
        )
        items = r["tracks"]["items"]
        if items:
            ara = []
            for i in items:
                ar, tr = get_ratios(i, croartist, crotitle)
                ara.append(ar)
            n, ar = max(enumerate(ara), key=lambda x: x[1])
            if ar < 0.5:
                print_spotify_track(items[n], fg="red")
                click.secho(
                    f"^ Unmatched with {ar:.2f}, {tr:.2f}",
                    fg="red",
                )
                return
    if not items:
        click.secho("^ Not found", fg="red")
        return
    ara, tra, ra = [], [], []
    for i in items:
        ar, tr = get_ratios(i, croartist, crotitle)
        ara.append(ar)
        tra.append(tr)
        ra.append(ar+tr)
    n, r = max(enumerate(ra), key=lambda x: x[1])
    print_spotify_track(items[n], fg="green")
    click.secho(f"^ Matched with {ara[n]:.2f}, {tra[n]:.2f}", fg="cyan")
    return items[n]
