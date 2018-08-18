from setuptools import setup
from pathlib import Path

readme = Path(__file__).with_name("README.rst").read_text()

setup(
    name="spotzurnal",
    version="0.1",
    description="Create Spotify playlists out of the playlists of Czech Radio",
    long_description=readme,
    long_description_content_type="text/x-rst",
    url="https://github.com/oskar456/spotzurnal",
    author="Ondřej Caletka",
    author_email="ondrej@caletka.cz",
    license="MIT",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
    ],
    packages=["spotzurnal"],
    install_requires=[
        "click",
        "spotipy",
        "requests",
        "python-dateutil",
    ],
    entry_points={
        "console_scripts": [
            "spotzurnal = spotzurnal.main:main",
            "spotzurnal-quirkgen = spotzurnal.quirkgen:quirkgen",
            "spotzurnal-aggregator = spotzurnal.aggregator:aggregator",
        ],
    },
)
