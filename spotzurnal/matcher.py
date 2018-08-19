import re
import locale
from difflib import SequenceMatcher

import click

from . import croapi
from .cache import Cache


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


def get_plname(station, date):
    """Return name of playlist for certain station and date."""
    locale.setlocale(locale.LC_TIME, "cs_CZ")
    mname = (
        None, "ledna", "února", "března", "dubna", "května", "června",
        "července", "srpna", "září", "října", "listopadu", "prosince",
    )
    return "{} {} {}. {} {}".format(
        croapi.get_cro_station_name(station),
        date.strftime("%A").lower(),
        date.day,
        mname[date.month],
        date.year,
    )


def get_track_quirk(quirks, cro_track_id):
    """Return Spotify track id for given CRo track id from quirks."""
    q = quirks["tracks"].get(cro_track_id)
    if q:
        m = re.search(r"(?:track.)?([0-9a-zA-Z]{22})", q)
        if m:
            return m.group(1)


def get_artist_quirk(quirks, interpret_id):
    i = quirks["artists"].get(interpret_id)
    if i:
        click.secho(f"Corrected artist to {i}.", fg="yellow")
        return i


def match_cro_playlist(
        sp, date, station, replace=False, cache=None, quirks=None,
):
    """
    Generate a Spotify playlist from a playlist published
    by the Czech Radio.
    """
    c = cache or Cache()
    q = quirks or {"artists": {}, "tracks": {}}
    trackids = []
    unmatched = []
    fromcache = 0
    pl = croapi.get_cro_day_playlist(station, date)
    for n, track in enumerate(pl, start=1):
        c.store_cro_track(track)
        m = get_track_quirk(q, track.track_id) or c.lookup_match(track)
        if m:
            fromcache += 1
        else:
            print(f"{track.since:%H:%M}: {track.interpret} - {track.track}")
            interpret = (
                get_artist_quirk(q, track.interpret_id) or track.interpret
            )
            t = search_spotify_track(sp, interpret, track.track)
            if t:
                c.store_spotify_track(t, track)
                m = t.get("id")
        if m:
            trackids.append(m)
        else:
            unmatched.append(track)
    matched = len(trackids)
    if matched < 1:
        click.secho("No tracks found!", fg="red")
        return
    pct, cachepct = 100*matched/n, 100*fromcache/matched
    click.secho(f"Matched {matched}/{n} – {pct:.0f}%", bold=True)
    click.secho(
        f"Already cached {fromcache}/{matched} – {cachepct:.0f}%",
        bold=True,
    )
    if unmatched:
        click.secho("Unmatched tracks:", bold=True)
        print("\n".join(
            f"{t.since:%H:%M}: {t.interpret} ({t.interpret_id}) - "
            f"{t.track} ({t.track_id})"
            for t in unmatched
        ))
    plname = get_plname(station, date)
    click.secho(
        f"Playlist name: {plname}",
        bold=True,
    )
    playlist = sp.get_or_create_playlist(plname)
    click.secho(
        "Playlist URL: https://open.spotify.com/user/"
        f"{sp.user}/playlist/{playlist}",
        bold=True,
    )
    if replace:
        sp.user_playlist_replace_tracks(sp.user, playlist, trackids[:100])
    total = sp.user_playlist_tracks(sp.user, playlist, fields="total")["total"]
    if 0 < total < matched and not replace:
        print(
            "Keeping {} tracks already in playlist, adding {} more.".format(
                total, matched - total,
            ),
        )
    if total >= matched and not replace:
        print("No new tracks found.")
    else:
        sp.put_all_data(
            sp.user_playlist_add_tracks,
            trackids,
            sp.user,
            playlist,
            offset=total,
        )
