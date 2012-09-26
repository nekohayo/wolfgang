#!/usr/bin/python
# -*- coding: utf-8 -*-
# Wolfgang is a very simple audio player demo using media indexing
# Copyright 2012 Luis de Bethencourt & Jean-François Fortin Tam
from gi.repository import Gtk
from gi.repository import Gst
from os import path
from sys import exit
# In a separate "samples" file, use a list in a tuple (the "LIBRARY" constant).
# Each list is composed of strings for URI, title, artist, album.
from samples import LIBRARY

class GhettoBlaster():

    def __init__(self):
        Gst.init(None)
        self.builder = Gtk.Builder()
        self.builder.add_from_file(path.join(path.curdir, "wolfgang.ui"))
        self.builder.connect_signals(self)

        # Sup dawg, I heard you like black,
        # so I put a dark UI in your car so you can drive through the night.
        gtksettings = Gtk.Settings.get_default()
        gtksettings.set_property("gtk-application-prefer-dark-theme", True)
        self.main_toolbar = self.builder.get_object("main_toolbar")
        self.main_toolbar.get_style_context().add_class("primary-toolbar")

        self._prepare_treeviews()
        # FIXME: temporary test stuff:
        self._populate_library()
        self._populate_queue()
        self.set_uri(LIBRARY[-1][0])

        self.window = self.builder.get_object("window1")
        self.window.set_icon_name("rhythmbox")
        #self.window.maximize()
        self.window.connect("delete-event", self.quit)
        self.window.show_all()

    """
    UI initialization crack
    """
    def _prepare_treeviews(self):
        self.library_treeview = self.builder.get_object("library_treeview")
        self.playlist_treeview = self.builder.get_object("playlist_treeview")
        self.queue_treeview = self.builder.get_object("queue_treeview")
        # If we enable this, we'll get in trouble in the removeFromQueue method:
        # self.queue_treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        self.library = Gtk.TreeStore(str, str) # URI, artist, album, title
        self.queue = Gtk.ListStore(str, str) # URI, title

        self.library_treeview.set_model(self.library)
        self.playlist_treeview.set_model(self.library)
        self.queue_treeview.set_model(self.queue)

        # Library: URI, artist, album, title
        column = Gtk.TreeViewColumn("Artist")
        artist = Gtk.CellRendererText()
        column.pack_start(artist, True)
        column.add_attribute(artist, "text", 1)
        self.library_treeview.append_column(column)
        column = Gtk.TreeViewColumn("Album")
        album = Gtk.CellRendererText()
        column.pack_start(album, True)
        column.add_attribute(album, "text", 2)
        self.library_treeview.append_column(column)

        # TODO: add an icon column for the currently played track...
        # or remove tracks as they play, reinsert when clicking "previous"?
        column = Gtk.TreeViewColumn("Title")
        title = Gtk.CellRendererText()
        column.pack_start(title, True)
        column.add_attribute(title, "text", 1)
        self.queue_treeview.append_column(column)
        # Silly hack to steal the focus from the gtk entry:
        self.library_treeview.grab_focus()

    def _populate_library(self):
        """
        Appends albums to artists in the tree
        """
        for track in LIBRARY:
            already_there = False   # loop through artists checking if it is
                                    # already there
            # URI, artist, album, title
            it = self.library.get_iter_first()
            while (it != None) and (already_there == False):
                print self.library.get_value(it, 0)
                if track[2] == self.library.get_value(it, 0):
                    already_there = True
                else:
                    it = self.library.iter_next(it)

            if not already_there:
                it = self.library.append(None, [track[2], track[2]])
            self.library.append(it, [track[3], track[3]])

    def _populate_queue(self, tracks=None):
        for track in LIBRARY:
            self.queue.append([track[0], track[1]])

    def set_uri(self, uri):
        self.tune = Gst.ElementFactory.make("playbin", "John Smith")
        self.tune.props.uri = uri
#        bus = self.tune.get_bus()
#        bus.add_signal_watch()
#        bus.enable_sync_message_emission()
#        bus.connect("message", self._onBusMessage)
#        bus.connect("sync-message", self._onBusSyncMessage)

    """
    UI callback methods
    """
    def previous(self, widget):
        raise NotImplementedError

    def play_pause(self, widget):
        if widget.props.active:
            print "Play", self.tune.props.uri
            self.tune.set_state(Gst.State.PLAYING)
            self.builder.get_object("time_slider").set_sensitive(True)
        else:
            print "Pause"
            self.tune.set_state(Gst.State.PAUSED)

    def next(self, widget):
        raise NotImplementedError

    def seek(self, widget):
        target_percent = widget.get_adjustment().props.value / 100.0
        target_position = target_percent * self.tune.query_duration(Gst.Format.TIME)[1]
        self.tune.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, target_position)

    def shuffle(self, widget):
        raise NotImplementedError

    def addToQueue(self, widget):
        raise NotImplementedError

    def clearQueue(self, widget):
        # C-style "no messing around with loops, just drop the pointer" tactic
        self.queue = Gtk.ListStore(str, str)
        self.queue_treeview.set_model(self.queue)

    def removeFromQueue(self, widget):
        model, row_iter = self.queue_treeview.get_selection().get_selected()
        self.queue.remove(row_iter)

    def quit(self, unused_window, unused_event):
        Gtk.main_quit
        # TODO: destroy any running pipeline
        exit(0)

    """
    GStreamer callbacks
    """
    def _onBusMessage(self, bus, message):
        if message.type is Gst.MessageType.EOS:
            print "switch to the next track, if any..."
        elif message.type is Gst.MessageType.TAG:
            # TODO: do something with ID3 tags or not?
            pass

    def _onBusSyncMessage(self, bus, message):
        print "We're syncing! Abandon ship!"

Amadeus = GhettoBlaster()
Gtk.main()
