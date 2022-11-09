#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Based on program "pygme-0.0.6", writen by Vinay Reddy <vinayvinay@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

# use subprocess instead of os.popen* FIXME

from scal3 import logger
log = logger.get()

from time import sleep
import sys
import os
import subprocess
import re
from contextlib import suppress

from scal3 import ui
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	imageFromFile,
	pixbufFromFile,
)

# Control
SEEK_TIME_SMALL = 10 # in seconds

# Mplayer
STATUS_UPDATE_TIMEOUT = 1000
VOLUME_STEP = 5


class MPlayer:
	pbox, mplayerIn, mplayerOut = None, None, None
	eofHandle, statusQuery = 0, 0
	paused = False
	isVidOnTop = False
	mplayerOptions = None
	playTime = None

	def __init__(self, pbox):
		self.pbox = pbox

	# Play the specified file
	def play(self, path):
		log.debug(f"File path: {path}")
		mplayerOptions = self.pbox.mplayerOptions.split(" ")

		if self.pbox.isvidontop:
			mplayerOptions.insert(0, "-ontop")

		cmd = ["mplayer"] + mplayerOptions + ["-quiet", "-slave", path]
		# 2>/dev/null"
		self.mplayerIn, self.mplayerOut = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()

		try:
			import fcntl
		except ImportError:
			pass
		else:
			#set mplayerOut to non-blocking mode
			fcntl.fcntl(self.mplayerOut, fcntl.F_SETFL, os.O_NONBLOCK)

		self.startHandleEof()
		self.startStatusQuery()
		#if self.mplayerIn!=None:
		#	self.pbox.seekBar.set_sensitive(True)
		#	self.pbox.fcb.set_sensitive(False)

	# Get the length of file, format it and place it in playtime
	def getLength(self):
		self.cmd("get_time_length")
		sleep(0.1)

		status = None
		# get the last line of output
		with suppress(Exception):
			for status in self.mplayerOut:
				if not status:
					break
		if not status or not status.startswith("ANS_LENGTH="):
			return True

		length = int(float(status.replace("ANS_LENGTH=", "").strip()))
		h = length / 3600
		m = (length % 3600) / 60
		s = (length % 60)
		if h:
			self.playTime = f"{h:d}:{m:02d}:{s:02d}"
		else:
			self.playTime = f"{m:02d}:{s:02d}"
		log.debug(f"playTime={self.playTime}")

	# Toggle between play and pause
	def pause(self):
		if not self.mplayerIn:
			return
		if self.cmd("pause"):
			if self.paused:
				self.startStatusQuery()
			else:
				self.stopStatusQuery()
			self.paused = not self.paused
		else:
			self.stopStatusQuery()
			self.paused = False

	# Seek by the amount specified (in seconds)
	def seek(self, amount, mode=0):
		if not self.mplayerIn:
			return False
		self.cmd(f"seek {amount} {mode}")
		self.queryStatus()

	# Set volume    using aumix
	def setVolume(self, value):
		if self.pbox.adjustvol:
			command = ["aumix", "-v", str(value)]
		else:
			command = ["aumix", "-w", str(value)]

		try:
			subprocess.call(command)
		except Exception as e:
			log.error(f"Cannot set volume: {e}")

	# Change volume by the amount specified
	# Changing the adjustment automatically updates
	# the range widget and increases the vol
	def stepVolume(self, increase):
		if increase:
			self.pbox.volAdj.value += VOLUME_STEP
			if self.pbox.volAdj.value > 100:
				self.pbox.volAdj.value = 100

		else:
			if self.pbox.volAdj.value <= VOLUME_STEP:
				self.pbox.volAdj.value = 0
			else:
				self.pbox.volAdj.value -= VOLUME_STEP

	# Close mplayer
	def close(self):
		if self.paused:
			self.pause()
		if not self.mplayerIn:
			return
		self.stopStatusQuery()
		self.stopEofHandler()
		self.cmd("quit") # It doesn"t matter if false is returned
		with suppress(Exception):
			self.mplayerIn.close()
			self.mplayerOut.close()
		self.mplayerIn, self.mplayerOut = None, None
		self.playTime = None
		self.pbox.seekAdj.value = 0
		#self.pbox.seekBar.set_sensitive(False)
		#self.pbox.fcb.set_sensitive(True)

	def cmd(self, command):
		if not self.mplayerIn:
			return False
		try:
			self.mplayerIn.write(command + "\n")
			self.mplayerIn.flush()
		except Exception:
			return False
		return True

	# Get current playing position in song
	def queryStatus(self):
		if not self.playTime:
			self.getLength()
		self.cmd("get_percent_pos")
		sleep(0.05) # allow time for output

		status = None
		# get the last line of output
		with suppress(Exception):
			for status in self.mplayerOut:
				if not status:
					break

		if not status or not status.startswith("ANS_PERCENT_POSITION="):
			return True

		self.pbox.seekAdj.value = int(status.replace("ANS_PERCENT_POSITION=", ""))

		return True

	# Handle EOF in mplayerOut
	def handleEof(self, source, condition):
		self.stopStatusQuery()
		self.mplayerIn, self.mplayerOut = None, None
		self.pbox.seekAdj.value = 0

	# Handle EOF (basically, a connection Hung Up in mplayerOut)
	def startHandleEof(self):
		self.eofHandle = gobject.io_add_watch(
			self.mplayerOut,
			gobject.IO_HUP,
			self.handleEof,
		)

	# Stop looking for IO_HUP in mplayerOut
	def stopEofHandler(self):
		source_remove(self.eofHandle)

	# Call a function periodically to fetch status
	def startStatusQuery(self):
		log.info("start")
		self.statusQuery = timeout_add(
			STATUS_UPDATE_TIMEOUT,
			self.queryStatus,
		)

	# Stop calling the function that fetches status periodically
	def stopStatusQuery(self):
		source_remove(self.statusQuery)


class PlayerBox(gtk.Box):
	adjustvol = 0
	vollevel0 = 100
	vollevel1 = 50
	mplayerOptions = "-geometry 50:50"
	key_pause = 65
	key_stop = 39
	key_seekback = 100
	key_seekforward = 102
	key_volinc = 63
	key_voldec = 112
	isvidontop = False
	#continuous = True
	#cycle = False
	#ontop = 28
	#isvidontop = False
	###############
	forbid = [102, 100]

	def __init__(self, hasVol=False):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.fcb = gtk.FileChooserButton(title="Select Sound")
		self.fcb.set_local_only(True)
		self.fcb.set_property("width-request", 150)
		pack(self, self.fcb)
		self.mplayer = mplayer = MPlayer(self)
		self.connect("key-press-event", self.divert)
		self.connect(
			"destroy",
			lambda *args: mplayer.close(),
		)  # FIXME
		##self.toolbar.connect("key-press-event", self.toolbarKey)#??????????
		##############
		self.playPauseBut = gtk.Button()
		self.playPauseBut.add(imageFromFile(
			"media-playback-start.svg",
			size=ui.toolbarIconSize,
		))
		self.playPauseBut.connect("clicked", self.playPause)
		pack(self, self.playPauseBut)
		#######
		stopBut = gtk.Button()
		stopBut.add(imageFromFile(
			"media-playback-stop.svg",
			size=ui.toolbarIconSize,
		))
		stopBut.connect("clicked", self.stop)
		pack(self, stopBut)
		##############
		self.seekAdj = gtk.Adjustment(0, 0, 100, 1, 10, 0)
		# FIXME: use keyword args for gtk.Adjustment()
		#self.seekAdj.connect("value_changed", self.seekAdjChanged)  # FIXME
		self.seekBar = gtk.HScale()
		self.seekBar.set_adjustment(self.seekAdj)
		self.seekBar.set_value_pos(gtk.PositionType.TOP)
		self.seekBar.set_sensitive(False)
		self.seekBar.connect("key-press-event", self.divert)
		self.seekBar.set_draw_value(False)
		#self.seekBar.connect("format-value", self.displaySongString)
		self.seekBar.connect("button-release-event", self.seek)
		pack(self, self.seekBar, 1, 1, 5)
		################
		self.hasVol = hasVol
		if hasVol:
			if self.adjustvol:
				self.volAdj = gtk.Adjustment(self.vollevel1, 0, 100, 5, 10, 0)
				self.mplayer.setVolume(self.vollevel1)
			else:
				self.volAdj = gtk.Adjustment(self.vollevel0, 0, 100, 5, 10, 0)
				self.mplayer.setVolume(self.vollevel0)
			self.volAdj.connect("value_changed", self.setVolume)
			scale = gtk.HScale(self.volAdj)
			scale.set_size_request(50, -1)
			scale.set_value_pos(gtk.PositionType.TOP)
			scale.connect("format-value", self.displayVolString)
			scale.connect("key-press-event", self.divert)
			pack(self, scale, False, False, 5)  # noqa: FURB120

	def divert(self, widget, gevent):
		key = gevent.hardware_keycode
		if key == self.key_seekback: # left arrow, seek
			self.mplayer.seek(-SEEK_TIME_SMALL)
		elif key == self.key_seekforward: # right arrow, seek forward
			self.mplayer.seek(SEEK_TIME_SMALL)
		elif key == self.key_volinc: # *, increase volume
			if self.hasVol:
				self.mplayer.stepVolume(True)
		elif key == self.key_voldec: # /, decrease volume
			if self.hasVol:
				self.mplayer.stepVolume(False)
		elif key == self.key_pause: # space bar, pause
			self.mplayer.pause()
		else:
			return False

	def displaySongString(self, seekBar, value):
		if self.mplayer.playTime:
			return str(int(value)) + "% of " + self.mplayer.playTime
		if self.mplayer.mplayerIn:
			return str(int(value)) + "% of "
			#+ self.playlist.getCurrentSongTime()  # FIXME
		return str(int(value)) + "%"

	def seek(self, widget, gevent):# Seek on changing the seekBar
		# log.debug("seek", self.seekAdj.value, self.mplayer.mplayerIn)
		if not self.mplayer.mplayerIn:
			log.info("abc")
			sleep(0.05)
			self.seekAdj.value = 100
			#self.playPauseBut.get_child().set_from_pixbuf(pixbufFromFile(
			#	"media-playback-start.svg",
			#	size=ui.toolbarIconSize,
			#))
		else:
			self.mplayer.seek(int(self.seekAdj.value), 1)

	# Return formatted volume string
	def displayVolString(self, scale, value):
		return "Volume: " + str(int(value)) + "%"

	def setVolume(self, adj):# Set volume when the volume range widget is changed
		self.mplayer.setVolume(int(adj.value))
		if self.adjustvol:
			self.vollevel1 = int(adj.value)
			self.mplayer.setVolume(self.vollevel1)
		else:
			self.vollevel0 = int(adj.value)
			self.mplayer.setVolume(self.vollevel0)

	def playPause(self, button=None):
		imageName = "media-playback-start.svg"
		if self.mplayer.mplayerIn:
			if not self.mplayer.paused:
				imageName = "media-playback-pause.svg"
				imageName = ""
			self.mplayer.pause()
		else:
			imageName = "media-playback-pause.svg"
			path = self.fcb.get_filename()
			if path is None:
				return
			self.mplayer.play(path)
		self.playPauseBut.get_child().set_from_pixbuf(pixbufFromFile(
			imageName,
			size=ui.toolbarIconSize,
		))
		playing = bool(self.mplayer.mplayerIn)
		self.fcb.set_sensitive(not playing)
		self.seekBar.set_sensitive(playing)

	def stop(self, button):# Stop mplayer if it's running
		self.mplayer.close()
		button = self.playPauseBut
		button.get_child().set_from_pixbuf(pixbufFromFile(
			"media-playback-start.svg",
			size=ui.toolbarIconSize,
		))
		self.fcb.set_sensitive(self.mplayer.mplayerIn is None)
		self.seekBar.set_sensitive(self.mplayer.mplayerIn is not None)

	def decVol(self, widget):
		self.mplayer.stepVolume(False)

	def incVol(self, widget):
		self.mplayer.stepVolume(True)

	def toolbarKey(self, widget, gevent):
		# Prevent the down and up keys from taking control out of the toolbar
		keycode = gevent.hardware_keycode
		if keycode in (98, 104):
			return True
		return False

	def quit(self, event=None):
		self.mplayer.close()
		gtk.main_quit()

	def openFile(self, path, startPlaying=True):
		self.fcb.set_filename(path)
		if startPlaying:
			self.playPause()
		#self.mplayer.play(path)
		#self.playPauseBut.get_child().set_from_pixbuf(pixbufFromFile(
		#	"media-playback-pause.svg",
		#	size=ui.toolbarIconSize,
		#))
		#self.fcb.set_sensitive(self.mplayer.mplayerIn is None)
		#self.seekBar.set_sensitive(self.mplayer.mplayerIn!=None)

	def getFile(self):
		return self.fcb.get_filename()


if __name__ == "__main__":
	window = gtk.Window()
	window.set_title("Simple PyGTK Interface for MPlayer")
	mainVbox = VBox()
	pbox = PlayerBox()
	pack(mainVbox, pbox)
	window.connect("destroy", pbox.quit)
	window.add(mainVbox)
	mainVbox.show_all()
	window.show()
	if len(sys.argv) > 1:
		pbox.openFile(sys.argv[1])
	gtk.main()
