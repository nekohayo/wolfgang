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

"""GStreamer engine class"""

from gi.repository import Gst
from gi.repository import GObject

#from signal import SignalGroup, Signallable

class Engine (GObject.GObject):
    '''GStreamer engine class. Encapsulates all the core gstreamer work in
       simple function per feature for the HMI'''

    __gsignals__ = {
        'about_to_finish': (GObject.SIGNAL_RUN_FIRST, None,
                      ()),
        'error': (GObject.SIGNAL_RUN_FIRST, None,
                      ())
    }

    def __init__ (self):
        GObject.GObject.__init__(self)
        Gst.init (None)
        print "Running with GStreamer", str(Gst.version()[0]) + "." + \
            str(Gst.version()[1]) + "." + str(Gst.version()[2])
        self.IS_GST010 = Gst.version()[0] == 0
        if self.IS_GST010:
            PLAYBIN_ELEMENT = "playbin2"
            print "Only GStreamer 1.0 is supported for this demo."
            exit(1)
        else:
            PLAYBIN_ELEMENT = "playbin"

        self.player = Gst.ElementFactory.make(PLAYBIN_ELEMENT, "Player")
        self.is_playing = False
        self._seeking = False

        self._current_position = self._target_position = 0

        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self._onBusMessage)
        self.player.connect("about-to-finish",  self._about_to_finish)

    def play (self, uri):
        self.player.set_state (Gst.State.NULL)
        self.player.props.uri = uri
        self.player.set_state (Gst.State.PLAYING)
        self.is_playing = True

    def pause (self):
        self.player.set_state (Gst.State.PAUSED)

    def seek (self, target_position):
        self.player.seek_simple (Gst.Format.TIME, \
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, \
            target_position)

    def next_uri (self, uri):
        self.player.props.uri = uri
        self.player.set_state (Gst.State.PLAYING)

    def _seek (self):
        if not self._seeking and self._current_position != self._target_position:
            self._seeking = True
            print "Seek to", self._target_position
            self.seek(self._target_position)
            self._current_position = self._target_position

    def query_duration (self):
        return self.player.query_duration (Gst.Format.TIME)[1]

    def query_position (self):
        return self.player.query_position (Gst.Format.TIME)[1]


    """ 
    GStreamer callbacks
    """
    def _onBusMessage(self, bus, message):
        if message is None: 
            # This doesn't make any sense, but it happens all the time.
            return
        elif message.type is Gst.MessageType.TAG:
            # TODO: do something with ID3 tags or not?
            pass
        elif message.type is Gst.MessageType.ASYNC_DONE:
            print "Async done, now try seeking"
            self._seeking = False
            self._seek()
        elif message.type is Gst.MessageType.ERROR:
            print "Got message of type ", message.type
            print "Got message of src ", message.src
            print "Got message of error ", message.parse_error()
            self.emit ("error")

    def _about_to_finish (self, playbin):
        print "engine: about to finish"
        self.emit ("about_to_finish");


if __name__ == "__main__":
    import os, optparse

    usage = """engine.py -i [file]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-i", "--input", action="store", type="string", \
        dest="input", help="Input video     file", default="")
    (options, args) = parser.parse_args()

    print "Playing: %r" % options.input

    engine = Engine()
    engine.play (options.input)
    gobject.MainLoop().run()
