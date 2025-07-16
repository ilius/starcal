#!/usr/bin/env python3
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from typing import Never

from scal3 import logger

log = logger.get()

import os

os.environ["LANG"] = "en_US.UTF-8"  # FIXME

import shutil
import subprocess
import sys
from os.path import join
from time import localtime

from scal3 import ui
from scal3.path import pixDir
from scal3.time_utils import clockWaitMilliseconds
from scal3.ui_gtk import Dialog, gtk, pack, timeout_add
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton
from scal3.ui_gtk.utils import dialog_add_button

_ = str  # FIXME


def error_exit(
	resCode: int, text: str, transient_for: gtk.Window | None = None
) -> Never:
	d = gtk.MessageDialog(
		destroy_with_parent=True,
		message_type=gtk.MessageType.ERROR,
		buttons=gtk.ButtonsType.OK,
		text=text.strip(),
		transient_for=transient_for,
	)
	d.set_title("Error")
	d.run()  # type: ignore[no-untyped-call]
	sys.exit(resCode)


class AdjusterDialog(Dialog):
	xpad = 15

	def __init__(self) -> None:
		Dialog.__init__(self)
		self.set_title(_("Adjust System Date & Time"))  # FIXME
		self.set_keep_above(True)
		self.set_icon_from_file(join(pixDir, "preferences-system-time.png"))
		# ---------
		self.buttonCancel = dialog_add_button(
			self,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		self.buttonSet = dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="preferences-system.svg",
			label=_("Set System Time"),
		)
		# self.buttonSet.connect("clicked", self.onSetSysTimeClick)
		# ---------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.label_cur = gtk.Label(label=_("Current:"))
		pack(hbox, self.label_cur)
		pack(self.vbox, hbox)
		# ---------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.radioMan = gtk.RadioButton.new_with_mnemonic(
			group=None,
			label=_("Set _Manully:"),
		)
		self.radioMan.connect("clicked", self.onRadioManClick)
		pack(hbox, self.radioMan)
		pack(self.vbox, hbox)
		# ------
		vb = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		sg = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# --
		self.ckeckbEditTime = gtk.CheckButton.new_with_mnemonic(_("Edit _Time"))
		self.editTime = False
		self.ckeckbEditTime.connect("clicked", self.onCkeckbEditTimeClick)
		pack(hbox, self.ckeckbEditTime, padding=self.xpad)
		sg.add_widget(self.ckeckbEditTime)
		self.timeInput = TimeButton()
		pack(hbox, self.timeInput)
		pack(vb, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# --
		self.ckeckbEditDate = gtk.CheckButton.new_with_mnemonic(_("Edit _Date"))
		self.editDate = False
		self.ckeckbEditDate.connect("clicked", self.onCkeckbEditDateClick)
		pack(hbox, self.ckeckbEditDate, padding=self.xpad)
		sg.add_widget(self.ckeckbEditDate)
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(vb, hbox)
		# ---
		pack(self.vbox, vb, 0, 0, padding=10)
		self.vboxMan = vb
		# ------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.radioNtp = gtk.RadioButton.new_with_mnemonic_from_widget(
			radio_group_member=self.radioMan,
			label=_("Set from _NTP:"),
		)
		self.radioNtp.connect("clicked", self.onRadioNtpClick)
		pack(hbox, self.radioNtp)
		pack(self.vbox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# --
		pack(hbox, gtk.Label(label=_("Server:") + " "), padding=self.xpad)
		combo = gtk.ComboBoxText.new_with_entry()
		comboEntry = combo.get_child()
		assert isinstance(comboEntry, gtk.Entry), f"{comboEntry=}"
		comboEntry.connect("changed", self.updateSetButtonSensitive)
		pack(hbox, combo, 1, 1)
		ntpServerEntry = combo.get_child()
		assert isinstance(ntpServerEntry, gtk.Entry), f"{ntpServerEntry=}"
		self.ntpServerEntry: gtk.Entry = ntpServerEntry
		for s in ui.ntpServers:
			combo.append_text(s)
		combo.set_active(0)
		self.hboxNtp = hbox
		pack(self.vbox, hbox)
		# ------
		self.onRadioManClick()
		# self.onRadioNtpClick()
		self.onCkeckbEditTimeClick()
		self.onCkeckbEditDateClick()
		# ------
		self.updateTimes()
		self.vbox.show_all()

	def onRadioManClick(self, _radio: gtk.Widget | None = None) -> None:
		if self.radioMan.get_active():
			self.vboxMan.set_sensitive(True)
			self.hboxNtp.set_sensitive(False)
		else:
			self.vboxMan.set_sensitive(False)
			self.hboxNtp.set_sensitive(True)
		self.updateSetButtonSensitive()

	def onRadioNtpClick(self, _radio: gtk.Widget | None = None) -> None:
		if self.radioNtp.get_active():
			self.vboxMan.set_sensitive(False)
			self.hboxNtp.set_sensitive(True)
		else:
			self.vboxMan.set_sensitive(True)
			self.hboxNtp.set_sensitive(False)
		self.updateSetButtonSensitive()

	def onCkeckbEditTimeClick(self, _checkb: gtk.Widget | None = None) -> None:
		self.editTime = self.ckeckbEditTime.get_active()
		self.timeInput.set_sensitive(self.editTime)
		self.updateSetButtonSensitive()

	def onCkeckbEditDateClick(self, _checkb: gtk.Widget | None = None) -> None:
		self.editDate = self.ckeckbEditDate.get_active()
		self.dateInput.set_sensitive(self.editDate)
		self.updateSetButtonSensitive()

	def runCommand(self, cmd: list[str]) -> None:
		proc = subprocess.Popen(
			cmd,
			stderr=subprocess.PIPE,
			stdout=subprocess.PIPE,
		)
		resCode = proc.wait()
		error = proc.stderr.read().strip().decode("utf-8")  # type: ignore[union-attr]
		output = proc.stdout.read().strip().decode("utf-8")  # type: ignore[union-attr]
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

	def setSystemTimeUnix(self, timeStr: str) -> None:
		dateCmd = shutil.which("date")  # "/bin/date"
		if not dateCmd:
			error_exit(1, "Could not find command 'date'", transient_for=self)
		self.runCommand([dateCmd, "-s", timeStr])

	def setSystemTime(self, timeStr: str) -> None:
		if os.sep == "/":
			return self.setSystemTimeUnix(timeStr)

		if sys.platform == "win32":
			# TODO: test
			import win32api

			win32api.SetSystemTime(timeStr)
			return

		raise OSError("unknown or unsupported operating system")

	def updateTimes(self) -> bool:
		# dt = now() % 1
		timeout_add(clockWaitMilliseconds(), self.updateTimes)
		# log.debug("updateTimes", dt)
		y, m, d, H, M, S = localtime()[:6]
		self.label_cur.set_label(
			_("Current:") + f" {y:04d}/{m:02d}/{d:02d} - {H:02d}:{M:02d}:{S:02d}",
		)
		if not self.editTime:
			self.timeInput.set_value((H, M, S))
		if not self.editDate:
			self.dateInput.set_value((y, m, d))
		return False

	def updateSetButtonSensitive(self, _w: gtk.Widget | None = None) -> None:
		if self.radioMan.get_active():
			self.buttonSet.set_sensitive(self.editTime or self.editDate)
		elif self.radioNtp.get_active():
			self.buttonSet.set_sensitive(
				bool(self.ntpServerEntry.get_text()),
			)

	def onSetSysTimeClick(self, _w: gtk.Widget | None = None) -> None:
		if self.radioMan.get_active():
			if self.editTime:
				h, m, s = self.timeInput.get_value()
				if self.editDate:
					Y, M, D = self.dateInput.get_value()
					self.setSystemTime(
						f"{Y:04d}/{M:02d}/{D:02d} {h:02d}:{m:02d}:{s:02d}",
					)
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
