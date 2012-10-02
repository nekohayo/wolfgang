#!/usr/bin/python
# -*- coding: utf-8 -*-
# Wolfgang is a very simple audio player demo using media indexing
# Copyright 2012 Jean-François Fortin Tam, Luis de Bethencourt
from gi.repository import Gtk
from gi.repository import Gst
from gi.repository import GObject
from os import path
from sys import exit
import random
# In a separate "samples" file, use a list in a tuple (the "LIBRARY" constant).
# Each list is composed of strings for URI, title, artist, album.
from samples import LIBRARY

class GhettoBlaster():

    def __init__(self):
        Gst.init(None)
        self.tune = Gst.ElementFactory.make("playbin", "John Smith")
        self.is_playing = False
        # An internal list matching self.queue_store to allow shuffling:
        self._internal_queue = []

        self.builder = Gtk.Builder()
        self.builder.add_from_file(path.join(path.curdir, "wolfgang.ui"))
        self.builder.connect_signals(self)

        # Sup dawg, I heard you like black,
        # so I put a dark UI in your car so you can drive through the night.
        gtksettings = Gtk.Settings.get_default()
        gtksettings.set_property("gtk-application-prefer-dark-theme", True)
        self.main_toolbar = self.builder.get_object("main_toolbar")
        self.main_toolbar.get_style_context().add_class("primary-toolbar")
        self.main_toolbar.set_sensitive(False)

        self.previous_button = self.builder.get_object("previous_button")
        self.play_button = self.builder.get_object("play_button")
        self.next_button = self.builder.get_object("next_button")
        self.time_slider = self.builder.get_object("time_slider")
        self.next_button.set_sensitive(False)
        self.previous_button.set_sensitive(False)

        self._prepare_treeviews()
        self._populate_library()

        self.window = self.builder.get_object("window1")
        self.window.set_icon_name("rhythmbox")
        self.window.maximize()
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
        self.playlist_store = Gtk.ListStore(str, str)  # title, URI
        self.queue_store = Gtk.ListStore(str, str, str)  # cursor, title, URI
        self.queue_current_iter = None  # To keep track of where the cursor was

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

        # Queue: 3 columns in store, 1 shown for cursor, 1 for the track title
        column = Gtk.TreeViewColumn("Cursor")
        cursor = Gtk.CellRendererText()
        column.pack_start(cursor, True)
        column.add_attribute(cursor, "text", 0)
        self.queue_treeview.append_column(column)
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


    """
    UI methods and callbacks
    """
    def previous(self, unused_widget=None):
        if self.queue_current_iter is None:
            return False
        prev_iter = self.queue_store.iter_previous(self.queue_current_iter)
        if prev_iter is None:
            return False
        uri = self.queue_store.get_value(prev_iter, 2)
        self.set_uri(uri)
        self.play()
        self.queue_store.set_value(self.queue_current_iter, 0, "")  # remove the ♪ cursor
        self.queue_store.set_value(prev_iter, 0, "♪")
        self.queue_current_iter = prev_iter
        self.next_button.set_sensitive(True)
        if not self.queue_store.iter_previous(self.queue_current_iter):
            self.previous_button.set_sensitive(False)

    def _play_pause(self, widget):
        """
        Callback for the Play pushbutton
        """
        if widget.props.active:
            self.play()
        else:
            self.pause()

    def next(self, unused_widget=None):
        if self.queue_current_iter is None:
            return False
        next_iter = self.queue_store.iter_next(self.queue_current_iter)
        if next_iter is None:
            return False
        uri = self.queue_store.get_value(next_iter, 2)
        self.set_uri(uri)
        self.play()
        self.queue_store.set_value(self.queue_current_iter, 0, "")  # remove the ♪ cursor
        self.queue_store.set_value(next_iter, 0, "♪")
        self.queue_current_iter = next_iter
        self.previous_button.set_sensitive(True)
        if not self.queue_store.iter_next(self.queue_current_iter):
            self.next_button.set_sensitive(False)

    def shuffle(self, unused_widget=None):
        random.shuffle(self._internal_queue)
        self.queue_store = Gtk.ListStore(str, str, str)
        for item in self._internal_queue:
            self.queue_store.append(item)
        self.queue_treeview.set_model(self.queue_store)
        self.queue_current_iter = None

    def addToQueue(self, unused_widget=None):
        """
        Add the playlist's selected item to the queue. If no item is selected,
        add them all and let the norse gods sort them out.
        """
        # Warning: this all assumes we only allow single item selections.
        # get_selected will fail to work if we allow multiple selections.
        (treemodel, current_iter) = self.playlist_treeview.get_selection().get_selected()
        column = 0

        def _addIterToQueue(current_iter):
            uri = treemodel.get_value(current_iter, 0)
            title = treemodel.get_value(current_iter, 1)
            self.queue_store.append([None, uri, title])
            # This will be used for the shuffle function. The first item is for
            # the cursor/playback indicator column, but it's not used here: None
            if self._internal_queue == []:
                self.queue_current_iter = self.queue_store.get_iter_first()
            self._internal_queue.append([None, uri, title])

        if current_iter is None:
            current_iter = treemodel.get_iter_first()
            while current_iter:  # Loop through iters until we get False
                _addIterToQueue(current_iter)
                current_iter = treemodel.iter_next(current_iter)
        else:
            _addIterToQueue(current_iter)
        self.main_toolbar.set_sensitive(True)

    def clearQueue(self, unused_widget=None):
        # C-style "no messing around with loops, just drop the pointer" tactic
        self.queue_store = Gtk.ListStore(str, str, str)
        self.queue_treeview.set_model(self.queue_store)
        self.queue_current_iter = None
        self._internal_queue = []
        self.main_toolbar.set_sensitive(False)

    def _removeFromQueue(self, widget):
        model, row_iter = self.queue_treeview.get_selection().get_selected()
        # Now look at what you've done! This messes up everything.
        # We need to check if the removed item was the current iter. If so,
        # do a bunch of black magic to figure out who should be its replacement.
        if row_iter is self.queue_current_iter:
            # FIXME: if you remove the currently playing row,
            # you'll get a segfault later when you try to play another track.
            next_item = self.queue_store.iter_next(row_iter)
            if next_item is not None:
                self.queue_current_iter = next_item
            else:
                prev_item = self.queue_store.iter_previous(row_iter)
                if prev_item is not None:
                    self.queue_current_iter = prev_item
                else:
                    self.queue_current_iter = None
        self.queue_store.remove(row_iter)
        # FIXME: remove it from self._internal_queue too

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

    def _queueTreeviewRowActivated(self, treeview, unused_position, unused_column):
        """
        When a row is activated in the queue treeview, start playback.
        """
        (treemodel, current_iter) = treeview.get_selection().get_selected()
        previous_iter = self.queue_current_iter
        if previous_iter:
            treemodel.set_value(previous_iter, 0, "")  # remove the ♪ cursor
        treemodel.set_value(current_iter, 0, "♪")
        self.queue_current_iter = current_iter
        self.pause()
        uri = treemodel.get_value(current_iter, 2)
        self.set_uri(uri)
        self.play()

        self.previous_button.set_sensitive(False)
        self.next_button.set_sensitive(False)
        if self.queue_store.iter_previous(self.queue_current_iter):
            self.previous_button.set_sensitive(True)
        if self.queue_store.iter_next(self.queue_current_iter):
            self.next_button.set_sensitive(True)

    def _sliderMouseEvent(self, widget, event):
        """
        Override the event button to use a middle-click when left-clicking
        the slider. This should be called by the button-press-event signal to
        override the button, then by button-release-event to free the button.
        
        This is also where seeks are triggered on click.
        """
        event.button = 2
        target_percent = widget.get_adjustment().props.value / 100.0
        target_position = target_percent * self.tune.query_duration(Gst.Format.TIME)[1]
        self.tune.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, target_position)
        
    def _updateSliderPosition(self):
        if self.is_playing:
            pos = self.tune.query_position(Gst.Format.TIME)[1]
            duration = self.tune.query_duration(Gst.Format.TIME)[1]
            if duration == 0:  # GStreamer nonsense, occurring randomly.
                return
            new_slider_pos = pos / float(duration) * 100
            self.time_slider.get_adjustment().props.value = new_slider_pos
        return self.is_playing

    def quit(self, unused_window=None, unused_event=None):
        Gtk.main_quit
        # TODO: destroy any running pipeline
        exit(0)

    """
    Public playback methods (not callbacks)
    """
    def play(self):
        if self.tune.props.uri is None:
            # The user clicked play without selecting a track, play the 1st
            self.set_uri(self.queue_store.get_value(self.queue_current_iter, 2))
            self.queue_store.set_value(self.queue_current_iter, 0, "♪")
        self.tune.set_state(Gst.State.PLAYING)
        self.is_playing = True
        self.play_button.props.active = True
        self.time_slider.set_sensitive(True)
        GObject.timeout_add(500, self._updateSliderPosition)
        if self.queue_store.iter_next(self.queue_current_iter):
            self.next_button.set_sensitive(True)
        if self.queue_store.iter_previous(self.queue_current_iter):
            self.previous_button.set_sensitive(True)

    def pause(self):
        self.tune.set_state(Gst.State.PAUSED)
        self.play_button.props.active = False
        self.is_playing = False

    def set_uri(self, uri):
        self.time_slider.set_value(0)
        self.tune.set_state(Gst.State.NULL)
        self.tune.props.uri = uri
        self.tune.set_state(Gst.State.READY)

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
