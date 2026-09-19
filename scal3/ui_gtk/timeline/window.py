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

from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.timeline.widget import TimeLine

__all__ = ["TimeLineWindow"]


class TimeLineWindow(CalObjWidget):
	objName = "timeLineWin"
	desc = _("Time Line")

	def __init__(self, parentWin: gtk.Window | None) -> None:
		win = gtk.Window()
		self.win = win
		self.w: gtk.Widget = win
		self.parentWin = parentWin
		self.initVars()
		ud.windowList.appendItem(self)
		# ---
		win.resize(ud.workAreaW, 150)
		win.move(0, 0)
		win.set_title(_("Time Line"))
		win.set_decorated(False)
		win.connect("delete-event", self.onDeleteEvent)
		win.connect("button-press-event", self.onButtonPress)
		self.tline = TimeLine(self.onCloseClick)
		win.connect("key-press-event", self.tline.onKeyPress)
		win.add(self.tline.w)
		self.tline.show()
		self.appendItem(self.tline)

	def showDayInWeek(self, jd: int) -> None:
		self.tline.showDayInWeek(jd)

	def onDeleteEvent(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> bool:
		if self.parentWin:
			self.hide()
		else:
			gtk.main_quit()  # FIXME
		return True

	def onCloseClick(self) -> None:
		if self.parentWin:
			self.hide()
		else:
			gtk.main_quit()  # FIXME

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button == 1:
			self.win.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
			return True
		return False
