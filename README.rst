Spotžurnál
==========

This package generates Spotify_ playlists out of playlists published by
`some Czech Radio stations`_.

Usage
-----

First, you need to get you OAuth 2.0 client secrets in the `Spotify
Developer Dashboard`_. You have to create an App, obtain the `Client ID`
and `Client Secret` and in the settings, whitelist an arbitrary redirect
URL like `http://localhost:8080/` (not actually used yet).

During the first run, you’ll get prompted for `Client ID` and  `Client Secret`,
and then to authenticate to a Spotify accout by opening a webpage in a browser.
After approval of the usage, you'll get redirected to a non-functional
localhost URL. Paste the whole URL back into the app.

At last, you'll be prompted for the user name, whose playlists will be created.
All the credentials are then saved for the next runs.

See the embedded help for other parameters.

.. _Spotify: https://www.spotify.com/
.. _some Czech Radio stations: https://radiozurnal.rozhlas.cz/playlisty
.. _Spotify Developer Dashboard: https://developer.spotify.com/dashboard/
