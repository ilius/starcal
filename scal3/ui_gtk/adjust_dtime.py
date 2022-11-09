#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal3 import logger
log = logger.get()

import os

os.environ["LANG"] = "en_US.UTF-8"  # FIXME

from os.path import join
import subprocess
import shutil
from time import localtime
from time import time as now
import sys

from scal3.path import pixDir
from scal3 import ui
from scal3.time_utils import clockWaitMilliseconds

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import dialog_add_button
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton

from gi.repository.Gtk import IconTheme

_ = str  # FIXME


def error_exit(resCode, text, **kwargs):
	d = gtk.MessageDialog(
		destroy_with_parent=True,
		message_type=gtk.MessageType.ERROR,
		buttons=gtk.ButtonsType.OK,
		text=text.strip(),
		**kwargs
	)
	d.set_title("Error")
	d.run()
	sys.exit(resCode)


class AdjusterDialog(gtk.Dialog):
	xpad = 15

	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Adjust System Date & Time"))  # FIXME
		self.set_keep_above(True)
		self.set_icon_from_file(join(pixDir, "preferences-system-time.png"))
		#########
		self.buttonCancel = dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		# self.buttonCancel.connect("clicked", lambda w: sys.exit(0))
		self.buttonSet = dialog_add_button(
			self,
			imageName="preferences-system.svg",
			label=_("Set System Time"),
			res=gtk.ResponseType.OK,
		)
		# self.buttonSet.connect("clicked", self.onSetSysTimeClick)
		#########
		hbox = HBox()
		self.label_cur = gtk.Label(label=_("Current:"))
		pack(hbox, self.label_cur)
		pack(self.vbox, hbox)
		#########
		hbox = HBox()
		self.radioMan = gtk.RadioButton.new_with_mnemonic(
			group=None,
			label=_("Set _Manully:"),
		)
		self.radioMan.connect("clicked", self.onRadioManClick)
		pack(hbox, self.radioMan)
		pack(self.vbox, hbox)
		######
		vb = VBox()
		sg = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		###
		hbox = HBox()
		##
		self.ckeckbEditTime = gtk.CheckButton.new_with_mnemonic(_("Edit _Time"))
		self.editTime = False
		self.ckeckbEditTime.connect("clicked", self.onCkeckbEditTimeClick)
		pack(hbox, self.ckeckbEditTime, padding=self.xpad)
		sg.add_widget(self.ckeckbEditTime)
		self.timeInput = TimeButton()
		pack(hbox, self.timeInput)
		pack(vb, hbox)
		###
		hbox = HBox()
		##
		self.ckeckbEditDate = gtk.CheckButton.new_with_mnemonic(_("Edit _Date"))
		self.editDate = False
		self.ckeckbEditDate.connect("clicked", self.onCkeckbEditDateClick)
		pack(hbox, self.ckeckbEditDate, padding=self.xpad)
		sg.add_widget(self.ckeckbEditDate)
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(vb, hbox)
		###
		pack(self.vbox, vb, 0, 0, padding=10)
		self.vboxMan = vb
		######
		hbox = HBox()
		self.radioNtp = gtk.RadioButton.new_with_mnemonic_from_widget(
			radio_group_member=self.radioMan,
			label=_("Set from _NTP:"),
		)
		self.radioNtp.connect("clicked", self.onRadioNtpClick)
		pack(hbox, self.radioNtp)
		pack(self.vbox, hbox)
		###
		hbox = HBox()
		##
		pack(hbox, gtk.Label(label=_("Server:") + " "), padding=self.xpad)
		combo = gtk.ComboBoxText.new_with_entry()
		combo.get_child().connect("changed", self.updateSetButtonSensitive)
		pack(hbox, combo, 1, 1)
		self.ntpServerEntry = combo.get_child()
		for s in ui.ntpServers:
			combo.append_text(s)
		combo.set_active(0)
		self.hboxNtp = hbox
		pack(self.vbox, hbox)
		######
		self.onRadioManClick()
		# self.onRadioNtpClick()
		self.onCkeckbEditTimeClick()
		self.onCkeckbEditDateClick()
		######
		self.updateTimes()
		self.vbox.show_all()

	def onRadioManClick(self, radio=None):
		if self.radioMan.get_active():
			self.vboxMan.set_sensitive(True)
			self.hboxNtp.set_sensitive(False)
		else:
			self.vboxMan.set_sensitive(False)
			self.hboxNtp.set_sensitive(True)
		self.updateSetButtonSensitive()

	def onRadioNtpClick(self, radio=None):
		if self.radioNtp.get_active():
			self.vboxMan.set_sensitive(False)
			self.hboxNtp.set_sensitive(True)
		else:
			self.vboxMan.set_sensitive(True)
			self.hboxNtp.set_sensitive(False)
		self.updateSetButtonSensitive()

	def onCkeckbEditTimeClick(self, checkb=None):
		self.editTime = self.ckeckbEditTime.get_active()
		self.timeInput.set_sensitive(self.editTime)
		self.updateSetButtonSensitive()

	def onCkeckbEditDateClick(self, checkb=None):
		self.editDate = self.ckeckbEditDate.get_active()
		self.dateInput.set_sensitive(self.editDate)
		self.updateSetButtonSensitive()

	def runCommand(self, cmd):
		proc = subprocess.Popen(
			cmd,
			stderr=subprocess.PIPE,
			stdout=subprocess.PIPE,
		)
		resCode = proc.wait()
		error = proc.stderr.read().strip()
		output = proc.stdout.read().strip()
		if output:
			log.info(output)
		# log.debug(f"{resCode=}, {error=}, {output=}")
		if error:
			log.error(error)
		if resCode != 0:
			error_exit(
				resCode,
				error,
				transient_for=self,
			)
		# else:
		# 	sys.exit(0)

	def setSystemTimeUnix(self, timeStr: str):
		dateCmd = shutil.which("date")  # "/bin/date"
		if not dateCmd:
			error_exit(1, "Could not find command 'date'", transient_for=self)
		self.runCommand([dateCmd, "-s", timeStr])

	def setSystemTime(self, timeStr: str):
		if os.sep == "/":
			return self.setSystemTimeUnix(timeStr)

		if sys.platform == "win32":
			# TODO: test
			import win32api
			win32api.SetSystemTime(timeStr)
			return

		raise OSError("unknown or unsupported operating system")

	def updateTimes(self):
		dt = now() % 1
		timeout_add(clockWaitMilliseconds(), self.updateTimes)
		# log.debug("updateTimes", dt)
		y, m, d, H, M, S = localtime()[:6]
		self.label_cur.set_label(
			_("Current:") +
			f" {y:04d}/{m:02d}/{d:02d} - {H:02d}:{M:02d}:{S:02d}"
		)
		if not self.editTime:
			self.timeInput.set_value((H, M, S))
		if not self.editDate:
			self.dateInput.set_value((y, m, d))
		return False

	def updateSetButtonSensitive(self, widget=None):
		if self.radioMan.get_active():
			self.buttonSet.set_sensitive(self.editTime or self.editDate)
		elif self.radioNtp.get_active():
			self.buttonSet.set_sensitive(
				self.ntpServerEntry.get_text() != ""
			)

	def onSetSysTimeClick(self, widget=None):
		if self.radioMan.get_active():
			if self.editTime:
				h, m, s = self.timeInput.get_value()
				if self.editDate:
					Y, M, D = self.dateInput.get_value()
					self.setSystemTime(f"{Y:04d}/{M:02d}/{D:02d} {h:02d}:{m:02d}:{s:02d}")
				else:
					self.setSystemTime(f"{h:02d}:{m:02d}:{s:02d}")
			else:
				if not self.editDate:
					error_exit(1, "No change!", transient_for=self)  # FIXME
				Y, M, D = self.dateInput.get_value()
				# h, m, s = self.timeInput.get_value()
				h, m, s = localtime()[3:6]
				self.setSystemTime(f"{Y:04d}/{M:02d}/{D:02d} {h:02d}:{m:02d}:{s:02d}")

		elif self.radioNtp.get_active():
			ntpdate = shutil.which("ntpdate")
			if not ntpdate:
				error_exit(1, "Could not find command 'ntpdate'", transient_for=self)
			self.runCommand([ntpdate, self.ntpServerEntry.get_text()])
		else:
			error_exit(1, "Not valid option!", transient_for=self)


if __name__ == "__main__":
	if os.getuid() != 0:
		error_exit(1, "This program must be run as root")
		# raise OSError("This program must be run as root")
		# os.setuid(0)  # FIXME
	d = AdjusterDialog()
	# d.set_keap_above(True)
	if d.run() == gtk.ResponseType.OK:
		d.onSetSysTimeClick()
