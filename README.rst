Spotžurnál
==========

This package generates Spotify_ playlists out of playlists published by
`some Czech Radio stations`_.

Usage
-----

.. NOTE::
   As of 2018-08, the version of `spotipy` library on PyPI, despite same
   version number, `lacks some features <https://github.com/plamere/spotipy/issues/311>`_
   Unless this issue is resolved, you have to use the GitHub version.

First, you need to get you OAuth 2.0 client secrets in the `Spotify
Developer Dashboard`_. You have to create an App, obtain the `Client ID`
and `Client Secret` and in the settings, whitelist some arbitrary redirect
URL like `http://localhost:8888/callback` (not actually used yet).
Save those credentials to a JSON file like this:

.. code-block:: json

        {
            "client_id": "deadbeef",
            "client_secret": "cafebabe",
            "redirect_uri": "http://localhost:8888/callback"
        }

..

See the `--help` for expected default name and path of this JSON file.
In the same directory, the renewable user tokens are cached under name
`cache-<username>.json`.

During the first run, you’ll get prompted to authenticate to a Spotify
accout by opening a webpage in a browser. After approval of the usage,
you'll get redirected to a non-functional localhost URL. Paste the whole
URL back into the app.

See the embedded help for other usage.

.. _Spotify: https://www.spotify.com/
.. _some Czech Radio stations: https://radiozurnal.rozhlas.cz/playlisty
.. _Spotify Developer Dashboard: https://developer.spotify.com/dashboard/
