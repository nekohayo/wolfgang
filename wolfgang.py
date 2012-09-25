#!/usr/bin/python
# -*- coding: utf-8 -*-
# Wolfgang is a very simple audio player demo using media indexing
# Copyright 2012 Luis de Bethencourt & Jean-François Fortin Tam
from gi.repository import Gtk
from gi.repository import Gst
from os import path
from sys import exit


SAMPLE_QUEUE_TRACKS = ["石川大阪友好条約", "Heartbreaker", "Hijo de la luna",
                        "9,000 Miles", "校庭 DAYDREAMER", "Avec ces yeux là"]
TEST_TRACK = "file://" + path.join(path.abspath(path.curdir), "test.ogg")

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
        self._populate_queue(SAMPLE_QUEUE_TRACKS)
        self.set_uri()

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

        self.library = Gtk.ListStore(str)
        self.playlist = Gtk.ListStore(str)
        self.queue = Gtk.ListStore(str)

        self.library_treeview.set_model(self.library)
        self.playlist_treeview.set_model(self.playlist)
        self.queue_treeview.set_model(self.queue)

        # TODO: add an icon column for the currently played track...
        # or remove tracks as they play, reinsert when clicking "previous"?
        column = Gtk.TreeViewColumn("Title")
        title = Gtk.CellRendererText()
        column.pack_start(title, True)
        column.add_attribute(title, "text", 0)
        self.queue_treeview.append_column(column)
        # Silly hack to steal the focus from the gtk entry:
        self.library_treeview.grab_focus()

    def _populate_queue(self, tracks):
        for track in tracks:
            self.queue.append([track])

    def set_uri(self, uri=TEST_TRACK):
        self.tune = Gst.ElementFactory.make("playbin", "John Smith")
        self.tune.props.uri = TEST_TRACK
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
            print "Play", TEST_TRACK
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
        self.queue = Gtk.ListStore(str)
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
