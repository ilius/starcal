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

from scal3.locale_man import tr as _
from scal3 import ui
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	labelIconButton,
	labelImageButton,
	set_tooltip,
)


class MyHButtonBox(gtk.ButtonBox):
	def __init__(self):
		gtk.ButtonBox.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.set_layout(gtk.ButtonBoxStyle.END)
		self.set_spacing(15)
		self.set_border_width(15)

	def add_button(
		self,
		imageName="",
		label="",
		onClick=None,
		tooltip="",
	):
		if imageName:
			b = labelImageButton(
				label=label,
				imageName=imageName,
			)
		else:
			b = labelIconButton(
				label,
				iconName,
				gtk.IconSize.BUTTON,
			)
		if onClick:
			b.connect("clicked", onClick)
		if tooltip:
			set_tooltip(b, tooltip)
		self.add(b)
		return b

	def add_ok(self, onClick=None):
		return self.add_button(
			imageName="dialog-ok.svg",
			label=_("_OK"),
			onClick=onClick,
		)

	def add_cancel(self, onClick=None):
		return self.add_button(
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			onClick=onClick,
		)
