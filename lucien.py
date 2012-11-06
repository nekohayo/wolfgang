#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Collabora Ltd
# Copyright (C) 2012 Luis de Bethencourt <luis.debethencourt@collabora.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

"""Lucien class"""

from gi.repository import Gst, GstPbutils
from gi.repository import GObject

import os

class Lucien (GObject.GObject):
    '''Lucien class. Encapsulates all the indexing work in
       simple function per feature for the HMI'''

    __gsignals__ = {
        'discovered': (GObject.SIGNAL_RUN_FIRST, None,
                      (GObject.TYPE_STRING, GObject.TYPE_STRING, \
                       GObject.TYPE_STRING, GObject.TYPE_STRING, \
                       GObject.TYPE_UINT))
    }

    def __init__ (self):
        GObject.GObject.__init__(self)
        Gst.init(None)
        self.disc = GstPbutils.Discoverer.new (50000000000)
        self.disc.connect('discovered', self.discovered)
        self.disc.start()
        self.index = []

    def scan_folder_for_ext (self, folder, ext):
        scan = []
        for path, dirs, files in os.walk (folder):
            for file in files:
                if file.split('.')[-1] in ext:
                    location = os.path.join(path, file)
                    self.discover_metadata(location)
        return scan

    def collect (self, folder):
        all = []
        for media in self.scan_folder_for_ext (folder, "mp3"):
            all.append(media)
        for media in self.scan_folder_for_ext (folder, "ogg"):
            all.append(media)
        for media in self.scan_folder_for_ext (folder, "oga"):
            all.append(media)

        return all

    def discover_metadata (self, location):
        file_uri= Gst.filename_to_uri (location)
        info = self.disc.discover_uri_async (file_uri)

    def discovered (self, discoverer, info, error):
        if not error:
            uri = info.get_uri()
            tags = info.get_tags ()

            artist = album = title = "unknown"
            track = 0

            tagged, tag = tags.get_string('artist')
            if tagged:
                artist = tag

            tagged, tag = tags.get_string('album')
            if tagged:
                album = tag

            tagged, tag = tags.get_string('title')
            if tagged:
                title = tag

            tagged, tag = tags.get_uint('track-number')
            if tagged:
                track = tag

        self.emit ("discovered", uri, artist, album, title, track)
        self.index.append((uri, artist, album, title, track))

    def search_in_any (self, query):
        result = []
        for track in self.index:
            if query.lower() in track[1].lower() or \
                    query.lower() in track[2].lower() or \
                    query.lower() in track[3].lower():
                result.append(track)
        return result

    def test (self, folder):
        all = self.collect (folder)
        for a in all:
            print a


if __name__ == "__main__":
    import os, optparse

    usage = """lucien.py -i [folder]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-i", "--input", action="store", type="string", \
        dest="input", help="Input video     file", default="")
    (options, args) = parser.parse_args()

    print "Indexing: %r" % options.input

    lucien = Lucien()
    lucien.test (options.input)
