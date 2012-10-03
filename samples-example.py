#!/usr/bin/python
# -*- coding: utf-8 -*-
# A simple media library for testing the Wolfgang music player

# Each track is a list containing: URI, title, artist, album.
# URI can be a properly encoded URI, or an absolute or relative path
LIBRARY = (
    ["file:///tmp/test%20uri/foo.ogg",
    "Power Rangers", "Ron Wasserman", "Power Rangers: The Official Single"],

    ["/tmp/test uri/foo.ogg",
    "Strobe", "Deadmau5", "For Lack of a Better Name"],

    ["../foo.ogg",
    "Free Software Song (death metal version)", "Jono Bacon", "Community, community, community"],

    ["/home/foo/baz.mp3",
    "Animal Rights", "Deadmau5", "4x4=12"],
)
