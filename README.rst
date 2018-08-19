Spotžurnál
==========

This package generates Spotify_ playlists out of playlists published by
`some Czech Radio stations`_. You can see the generated playlists under
`Spotify user spotzurnal`_.

Matching of tracks between CRo and Spotify can be cached in a SQLite database.
For cases where matching is not successful or produce wrong results,
a manually crafted YAML file with `quirks` can be supplied.

Usage
-----

First, you need to get you OAuth 2.0 client secrets in the `Spotify
Developer Dashboard`_. You have to create an App, obtain `Client ID`
and `Client Secret`. In the App settings, whitelist an arbitrary redirect
URL like ``http://localhost:8080/`` (not actually used yet).

During the first run, you’ll be prompted for `Client ID` and  `Client Secret`.
Then you authenticate to a Spotify account by opening webpage in a browser.
After approval of the usage, you'll get redirected to a non-functional
localhost URL. Paste the whole URL back into the app.

At last, you'll be prompted for the user name, whose playlists will be managed.
All the credentials are then saved for the future.

See the embedded help for other parameters.

Available utilities
-------------------

`spotzurnal`
  Create Spotify playlist of one day on one CRo station.

`spotzurnal-quirkgen`
  Create/extend YAML file of quirks with all unmatched tracks from the cache
  database.

`spotzurnal-rematch`
  Get all Spotify playlists of given station in given month and replace them
  with newly matched tracks. Useful especially after update of the quirks file.

`spotzurnal-aggregator`
  From all Spotify playlists of given station in given month, count the
  number of occurencies for each song and create a new `TOP` playlist.

.. _Spotify: https://www.spotify.com/
.. _Spotify user spotzurnal: https://open.spotify.com/user/spotzurnal
.. _some Czech Radio stations: https://radiozurnal.rozhlas.cz/playlisty
.. _Spotify Developer Dashboard: https://developer.spotify.com/dashboard/
