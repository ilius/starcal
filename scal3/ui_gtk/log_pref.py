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

from typing import Optional

from scal3.locale_man import tr as _
from scal3.json_utils import dataToCompactJson

from scal3.ui_gtk import *
from scal3.ui_gtk.pref_utils import PrefItem

class LogLevelComboBox(gtk.ComboBox):
	levels = [
		(0, _("All Messages")),
		(10, _("Debug")),
		(20, _("Info")),
		(30, _("Warning")),
		(40, _("Error")),
		(50, _("Critical")),
	]
	def __init__(self):
		gtk.ComboBox.__init__(self)
		###
		model = gtk.ListStore(int, str)
		self.set_model(model)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 1)
		###
		for num, name in self.levels:
			model.append([num, name])

	def get_value(self) -> Optional[int]:
		index = self.get_active()
		if index is None:
			return None
		return self.levels[index][0]

	def set_value(self, levelNum: int) -> None:
		for index, (num, name) in enumerate(self.levels):
			if num == levelNum:
				self.set_active(index)
				return


class LogLevelPrefItem(PrefItem):
	def __init__(self):
		self.obj = logger
		self.attrName = "logLevel"
		###
		self.combo = LogLevelComboBox()
		###
		hbox = HBox(spacing=5)
		pack(hbox, gtk.Label(label=_("Log Level")))
		pack(hbox, self.combo)
		pack(hbox, gtk.Label(), 1, 1)
		hbox.show_all()
		self._widget = hbox

	def get(self) -> int:
		return self.combo.get_value()

	def set(self, levelNum: int) -> None:
		self.combo.set_value(levelNum)

	def save(self):
		logData = {"logLevel": logger.logLevel}
		logJson = dataToCompactJson(logData)
		with open(logger.confPath, "w") as file:
			file.write(logJson)



