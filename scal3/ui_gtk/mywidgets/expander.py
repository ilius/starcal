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


from typing import Optional, Union

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *


class ExpanderFrameTitle(gtk.Button):
	def __init__(
		self,
		label: str = "",
		use_markup: bool = False,
		expanded: bool = True,
		icon_size: gtk.IconSize = gtk.IconSize.SMALL_TOOLBAR,
	) -> None:
		gtk.Button.__init__(self)
		self.set_relief(gtk.ReliefStyle.NONE)
		self.set_can_focus(False)
		self.get_style_context().add_class("image-button")
		##
		labelW = gtk.Label(label=label)
		labelW.set_use_markup(use_markup)
		##
		self._icon_size = icon_size
		self._image = gtk.Image()
		##
		hbox = HBox()
		pack(hbox, self._image)
		pack(hbox, labelW)
		self.add(hbox)
		hbox.show_all()
		##
		self.set_expanded(expanded)

	def _updateImage(self):
		if self.get_expanded():
			iconName = "pan-down-symbolic"
		else:
			# changes direction on RTL itself
			iconName = "pan-end-symbolic"
		self._image.set_from_icon_name(iconName, self._icon_size)
		self._image.show()

	def set_expanded(self, expanded: bool) -> None:
		self._expanded = expanded
		self._updateImage()

	def get_expanded(self) -> bool:
		return self._expanded


@registerSignals
class ExpanderFrame(gtk.Frame):
	signals = (
		("activate", []),
	)

	def __init__(
		self,
		label: str = "",
		use_markup: bool = False,
		expanded: bool = True,
		icon_size: gtk.IconSize = gtk.IconSize.SMALL_TOOLBAR,
		border_width: int = 5,
		inner_border_width: int = 5,
	) -> None:
		gtk.Frame.__init__(self)
		self._title = ExpanderFrameTitle(
			label=label,
			use_markup=use_markup,
			expanded=expanded,
			icon_size=icon_size,
		)
		self.set_label_widget(self._title)
		self._title.show()
		##
		self._box = VBox()
		gtk.Frame.add(self, self._box)
		##
		self.set_border_width(border_width)
		self._box.set_border_width(inner_border_width)
		##
		self._title.connect("clicked", self._onTitleClick)

	def add(self, child: gtk.Widget) -> None:
		pack(self._box, child, 1, 1)

	def _onTitleClick(self, button):
		self.set_expanded(not self.get_expanded())
		self.emit("activate")

	def set_expanded(self, expanded: bool) -> None:
		self._title.set_expanded(expanded)
		self._box.set_visible(expanded)

	def get_expanded(self) -> bool:
		return self._title.get_expanded()




