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

from typing import TYPE_CHECKING, Any

from scal3 import timeline
from scal3.locale_man import tr as _
from scal3.ui import conf as uiconf
from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.stack import MyStack, StackPage
from scal3.ui_gtk.timeline.prefs.buttons import buildButtonsPages
from scal3.ui_gtk.timeline.prefs.events import buildEventsPages
from scal3.ui_gtk.timeline.prefs.general import buildGeneralPages
from scal3.ui_gtk.timeline.prefs.indicators import buildIndicatorsPages
from scal3.ui_gtk.timeline.prefs.keys import buildKeysPages
from scal3.ui_gtk.timeline.prefs.movement import buildMovementPages
from scal3.ui_gtk.timeline.prefs.zooming import buildZoomingPages
from scal3.ui_gtk.utils import imageFromFile

if TYPE_CHECKING:
	from scal3.ui_gtk.pytypes import StackPageType
	from scal3.ui_gtk.timeline.prefs.types import TimeLineType

__all__ = ["TimeLinePreferencesWindow"]


class TimeLinePreferencesWindow(gtk.Window):
	def __init__(self, timeLine: TimeLineType) -> None:
		gtk.Window.__init__(self)
		self.set_title(_("Time Line Preferences"))
		self.set_position(gtk.WindowPosition.CENTER)
		self.connect("delete-event", self.onDelete)
		self.connect("key-press-event", self.onKeyPress)
		# self.set_has_separator(False)
		# self.set_skip_taskbar_hint(True)
		# ---
		self.vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self.add(self.vbox)
		# ---
		self.buttonbox = MyHButtonBox()
		# self.buttonbox.add_button(
		# 	imageName="dialog-cancel.svg",
		# 	label=_("Cancel"),
		# 	onClick=self.onCancelClick,
		# )
		# self.buttonbox.add_button(
		# 	imageName="dialog-ok-apply.svg",
		# 	label=_("_Apply", ctx="window action"),
		# 	onClick=self.onApplyClick,
		# )
		self.buttonbox.add_button(
			imageName="document-save.svg",
			label=_("_Save"),
			onClick=self.onSaveClick,
			tooltip=_("Save Preferences"),
		)
		# -------
		self.prefPages = []
		# ----------------------------------------------------
		stack = MyStack(
			iconSize=uiconf.stackIconSize.v,
		)
		stack.setTitleFontSize("large")
		stack.setTitleCentered(True)
		stack.setupWindowTitle(self, _("Time Line Preferences"), False)
		self.stack = stack
		# ----------------------------------------------------
		self.prefPages += buildGeneralPages(timeLine)
		self.prefPages += buildButtonsPages(timeLine)
		self.prefPages += buildIndicatorsPages(self, timeLine)
		self.prefPages += buildEventsPages(timeLine)
		self.prefPages += buildMovementPages(self, timeLine)
		self.prefPages += buildZoomingPages(timeLine)
		self.prefPages += buildKeysPages()
		# --------------------------------------------------------------------
		rootPagePath = "root"
		# ---
		mainPages = []
		for page in self.prefPages:
			if page.pageParent:
				page.pagePath = page.pageParent + "." + page.pageName
				continue
			page.pageParent = rootPagePath
			page.pagePath = page.pageName
			mainPages.append(page)
		# ----
		colN = 2
		# ----
		grid = gtk.Grid()
		grid.set_row_homogeneous(True)
		grid.set_column_homogeneous(True)
		grid.set_row_spacing(15)
		grid.set_column_spacing(15)
		grid.set_border_width(20)
		# ----
		firstPageDoubleSize = len(mainPages) % 2 == 1
		if firstPageDoubleSize:
			page = mainPages.pop(0)
			button = self.newWideButton(page)
			grid.attach(button, 0, 0, colN, 1)
		# ---
		N = len(mainPages)
		colBN = (N - 1) // colN + 1
		for col_i in range(colN):
			for row_i in range(colBN):
				page_i = col_i * colBN + row_i
				if page_i >= N:
					break
				page = mainPages[page_i]
				button = self.newWideButton(page)
				grid.attach(button, col_i, row_i + 1, 1, 1)
		grid.show_all()
		pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(pageWidget, grid, True, True)
		# ---------------
		page = StackPage()
		page.pagePath = rootPagePath
		page.pageWidget = pageWidget
		page.pageExpand = True
		page.pageExpand = True
		stack.addPage(page)
		for page in self.prefPages:
			stack.addPage(page)
		# -----------------------
		pack(self.vbox, stack, 1, 1)
		pack(self.vbox, self.buttonbox)
		# ----
		self.vbox.show_all()

	def gotoPageClicked(self, _b: gtk.Widget, page: StackPageType) -> None:
		self.stack.gotoPage(page.pagePath)

	def newWideButton(self, page: StackPageType) -> gtk.Widget:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
		hbox.set_border_width(10)
		label = gtk.Label(label=page.pageLabel)
		label.set_use_underline(True)
		pack(hbox, gtk.Label(), 1, 1)
		if page.pageIcon and uiconf.buttonIconEnable.v:
			pack(hbox, imageFromFile(page.pageIcon, self.stack.iconSize()))
		pack(hbox, label, 0, 0)
		pack(hbox, gtk.Label(), 1, 1)
		button = gtk.Button()
		button.add(hbox)
		button.connect("clicked", self.gotoPageClicked, page)
		return button

	def onDelete(
		self,
		_widget: gtk.Widget | None = None,
		_data: Any = None,
	) -> bool:
		self.hide()
		return True

	def onSaveClick(self, _w: gtk.Widget) -> None:
		self.hide()
		timeline.saveConf()

	def onKeyPress(self, _arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if gdk.keyval_name(gevent.keyval) == "Escape":
			self.hide()
			return True
		return False
