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

from gi.repository import GdkPixbuf
from gi.repository import Gio as gio
from gi.repository import Gtk as gtk

from scal3 import core

# from scal3.ui_gtk.starcal import MainWin as MainWinType

type MainWinType = gtk.ApplicationWindow


class GioNotificationWrapper(gio.Notification):
	def __init__(self, mainWin: MainWinType) -> None:
		self.mainWin = mainWin
		self.app = mainWin.app
		# --
		gio.Notification.__init__(self)
		self.set_title(core.APP_DESC)
		# self.show()

		action = gio.SimpleAction.new("onStatusIconClick")
		action.connect("activate", mainWin.onStatusIconClick)
		self.app.add_action(action)
		self.set_default_action("onStatusIconClick")

	def set_from_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf) -> None:
		# GdkPixbuf is subclass of gio.Icon
		self.set_icon(pixbuf)

	def set_from_file(self, fpath: str) -> None:
		self.set_icon(gio.FileIcon.new(gio.File.new_for_path(fpath)))

	def set_tooltip_text(self, text: str) -> None:
		# FIXME
		pass

	# def get_geometry(self, fpath):
	# 	 raise NotImplementedError

	# def connect(

	def is_embedded(self) -> bool:  # noqa: PLR6301
		# FIXME
		return True

	def set_visible(self, visible: bool) -> None:
		# FIXME
		pass
