import datetime
from collections import namedtuple

import requests
import dateutil.parser

_stationnames = {
    "radiozurnal": "Radiožurnál",
    "dvojka": "Dvojka",
    "radiowave": "Radio Wave",
    "regina": "Regina DAB Praha",
}


def get_cro_stations():
    return _stationnames.keys()


def get_cro_station_name(station):
    return _stationnames[station]


def get_cro_day_playlist(station="radiozurnal", date: datetime.date=None):
    """
    Download the playlist from CRo API for a day.
    """
    url = "https://croapi.cz/data/v2/playlist/day/"
    if date:
        url += f"{date:%Y/%m/%d/}"
    url += f"{station}.json"
    r = requests.get(url).json()
    for i in r.get("data", []):
        i['since'] = dateutil.parser.parse(i['since'])
        yield namedtuple("PlaylistItem", i.keys())(**i)
