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

        self.library_store = Gtk.TreeStore(str)  # Only 1 "column" to contain all
        self.playlist_store = Gtk.ListStore(str, str)  # URI, title
        self.queue_store = Gtk.ListStore(str, str)  # URI, title

        self.library_treeview.set_model(self.library_store)
        self.playlist_treeview.set_model(self.playlist_store)
        self.queue_treeview.set_model(self.queue_store)

        # Library: only one column, with two visible levels (artist, album)
        column = Gtk.TreeViewColumn()
        column_contents = Gtk.CellRendererText()
        column.pack_start(column_contents, True)
        column.add_attribute(column_contents, "text", 0)
        self.library_treeview.append_column(column)

        # Playlist: two columns in the store (title, URI), but only one shown
        column = Gtk.TreeViewColumn("Title")
        title = Gtk.CellRendererText()
        column.pack_start(title, True)
        column.add_attribute(title, "text", 0)
        self.playlist_treeview.append_column(column)

        # TODO: add an icon column for the currently played track...
        column = Gtk.TreeViewColumn("Title")
        title = Gtk.CellRendererText()
        column.pack_start(title, True)
        column.add_attribute(title, "text", 1)
        self.queue_treeview.append_column(column)

        # Silly hack to steal the focus from the gtk entry:
        self.library_treeview.grab_focus()

    def _populate_library(self):
        """
        for track in LIBRARY:
            if artist not already there: add it
            if album not already there: add it as a child of the artist
            add the track title and URI
        """
        last_artist_iter = self.library_store.get_iter_first()
        # A list of tracks (and URIs) in a dic of albums in a dic of artists:
        self.library = {}
        for track in LIBRARY:
            (uri, title, artist, album) = (track[0], track[1], track[2], track[3])
            if artist not in self.library:
                self.library[artist] = {}
                last_artist_iter = self.library_store.append(None, [artist])
            if album not in self.library[artist]:
                self.library[artist][album] = []
                last_album_iter = self.library_store.append(last_artist_iter, [album])
            # Add the track title and URI to our internal tree, but not the UI
            self.library[artist][album].append([title, uri])

    def _populate_queue(self, tracks=None):
        # TODO this method should only be called by the playlist
        # for now, we just crawl the library to show some placeholder contents
        for track in LIBRARY:
            self.queue_store.append([track[0], track[1]])

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
    def previous(self, unused_widget=None):
        raise NotImplementedError

    def _play_pause(self, widget):
        if widget.props.active:
            print "Play", self.tune.props.uri
            self.tune.set_state(Gst.State.PLAYING)
            self.builder.get_object("time_slider").set_sensitive(True)
        else:
            print "Pause"
            self.tune.set_state(Gst.State.PAUSED)

    def next(self, unused_widget=None):
        raise NotImplementedError

    def _seek(self, widget):
        target_percent = widget.get_adjustment().props.value / 100.0
        target_position = target_percent * self.tune.query_duration(Gst.Format.TIME)[1]
        self.tune.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, target_position)

    def shuffle(self, unused_widget=None):
        raise NotImplementedError

    def addToQueue(self, unused_widget=None):
        raise NotImplementedError

    def clearQueue(self, unused_widget=None):
        # C-style "no messing around with loops, just drop the pointer" tactic
        self.queue_store = Gtk.ListStore(str, str)
        self.queue_treeview.set_model(self.queue_store)

    def _removeFromQueue(self, widget):
        model, row_iter = self.queue_treeview.get_selection().get_selected()
        self.queue_store.remove(row_iter)

    def _libraryTreeviewRowSelected(self, treeview):
        """
        When a row is clicked in the library treeview, check if it's an artist
        or album. Depending on the type, query self.library to find the child
        tracks (and URIs), and replace self.playlist_store with a new store
        model containing the results.
        """
        (treemodel, current_iter) = treeview.get_selection().get_selected()
        if current_iter is None:
            # Nothing selected. This happens on startup.
            return
        column = 0
        current_value = self.library_store.get_value(current_iter, column)
        if treemodel.iter_depth(current_iter) is 0:
            # An artist is selected
            tracks = []
            for album in self.library[current_value]:
                for track in self.library[current_value][album]:
                    tracks.append(track)
        else:
            # An album is selected
            temp_iter = treemodel.iter_parent(current_iter)
            artist = self.library_store.get_value(temp_iter, column)
            tracks = self.library[artist][current_value]
        # Don't bother with existing items, scrap the old model and rebuild it
        self.playlist_store = Gtk.ListStore(str, str)
        for track in tracks:
            self.playlist_store.append(track)
        self.playlist_treeview.set_model(self.playlist_store)

    def quit(self, unused_window=None, unused_event=None):
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
