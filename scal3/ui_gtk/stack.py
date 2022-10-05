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

import time

from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import imageFromFile


class StackPage:
	def __init__(self):
		self.pageWidget = None
		self.pageParent = ""
		self.pageName = ""
		self.pagePath = ""
		self.pageTitle = ""
		self.pageLabel = ""
		self.pageIcon = ""
		self.pageExpand = True
		self.pageItem = None

	def __str__(self):
		return (
			f"StackPage(name={self.pageName!r}, path={self.pagePath!r}, "
			f"parent={self.pageParent!r})"
		)


class MyStack(gtk.Stack):
	def __init__(
		self,
		iconSize: int = 22,
		header: bool = True,
		headerSpacing: int = 5,
		verticalSlide: bool = False,
	):
		gtk.Stack.__init__(self)
		self.set_transition_duration(300) # milliseconds
		###
		self._header = header
		self._rtl = self.get_direction() == gtk.TextDirection.RTL # type: bool
		self._iconSize = iconSize  # type: int
		self._headerSpacing = headerSpacing # type: int
		self._verticalSlide = verticalSlide # type: bool
		###
		self._parentPaths = {} # Dict[str, str]
		self._currentPagePath = ""
		self._titles = {} # Dict[str, str]
		###
		self.connect("key-press-event", self.onKeyPress)
		###
		self._titleFontSize = "x-small"
		self._titleCentered = False
		###
		self._windowTitleEnable = False
		self._window = None
		self._windowTitleMain = ""
		self._windowTitleMainFirst = False

	def iconSize(self) -> int:
		return self._iconSize

	def currentPagePath(self) -> str:
		return self._currentPagePath

	def setTitleFontSize(self, fontSize: str):
		'''
		Font size in 1024ths of a point, or one of the absolute sizes
		'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large',
		or one of the relative sizes 'smaller' or 'larger'.
		If you want to specify a absolute size, it's usually easier to take
		advantage of the ability to specify a partial font description using 'font';
		you can use font='12.5' rather than size='12800'.
		https://developer.gnome.org/pango/stable/PangoMarkupFormat.html#PangoMarkupFormat
		'''
		self._titleFontSize = fontSize

	def setTitleCentered(self, centered: bool):
		self._titleCentered = centered

	def setupWindowTitle(
		self,
		window: gtk.Window,
		mainTitle: str,
		mainTitleFirst: bool,
	):
		self._windowTitleEnable = True
		self._window = window
		self._windowTitleMain = mainTitle
		self._windowTitleMainFirst = mainTitleFirst

	def onKeyPress(self, arg, gevent):
		if gdk.keyval_name(gevent.keyval) == "BackSpace":
			if self._currentPagePath:
				parentPath = self._parentPaths[self._currentPagePath]
				if parentPath:
					self.gotoPage(parentPath, backward=True)
					return True
		return False

	def _setSlideForward(self):
		self.set_transition_type(
			gtk.RevealerTransitionType.SLIDE_DOWN if self._verticalSlide else
			gtk.RevealerTransitionType.SLIDE_LEFT
		)

	def _setSlideBackward(self):
		self.set_transition_type(
			gtk.RevealerTransitionType.SLIDE_UP if self._verticalSlide else
			gtk.RevealerTransitionType.SLIDE_RIGHT
		)

	def _newHeaderBox(self, parentName: str, title: str = "", icon: str = ""):
		spacing = 10
		hbox = HBox(spacing=spacing)
		# hbox.set_direction(gtk.TextDirection.LTR)
		backButton = gtk.Button()
		backHbox = HBox(spacing=3)
		backHbox.set_border_width(5)
		backLabel = _("Back")
		if ui.buttonIconEnable:
			pack(backHbox, imageFromFile(
				"go-next.svg" if self._rtl else "go-previous.svg",
				size=self._iconSize,
			))
		else:
			backLabel = "  " + backLabel + "  "  # to make it bigger
		pack(backHbox, gtk.Label(label=backLabel))
		backButton.add(backHbox)
		backButton.connect(
			"clicked",
			lambda w: self.gotoPage(parentName, backward=True),
		)
		pack(hbox, backButton)
		pack(hbox, gtk.Label(), 1, 1)
		if icon:
			pack(hbox, imageFromFile(icon, self._iconSize), 0, 0)
		if title:
			if self._titleFontSize:
				title = f"<span font_size=\"{self._titleFontSize}\">{title}</span>"
			label = gtk.Label(label=title)
			if self._titleFontSize:
				label.set_use_markup(True)
			pack(hbox, label, 0, 0)
			if self._titleCentered:
				if icon:
					pack(hbox, imageFromFile("empty.png", self._iconSize + spacing), 0, 0)
				pack(hbox, gtk.Label(), 1, 1)
		hbox.show_all()
		return hbox

	def addPage(self, page: StackPage):
		pagePath = page.pagePath
		log.debug(f"MyStack: {pagePath=}")
		parentName = page.pageParent
		widget = page.pageWidget

		if pagePath in self._titles:
			raise ValueError(f"addPage: duplicate {pagePath=}")

		if not isinstance(widget, gtk.Widget):
			raise ValueError(f"invalid {widget=}, {pagePath=}")

		widget.show()
		if self._header and parentName:
			vbox = VBox(spacing=self._headerSpacing)
			pack(vbox, self._newHeaderBox(
				parentName,
				title=page.pageTitle,
				icon=page.pageIcon,
			))
			pack(vbox, widget, expand=page.pageExpand, fill=page.pageExpand)
			vbox.show()
			widget = vbox
		self.add_named(widget, name=pagePath)
		##
		self._parentPaths[pagePath] = parentName
		self._titles[pagePath] = page.pageTitle
		##
		if not self._currentPagePath:
			self.gotoPage(pagePath)

	def hasPage(self, pagePath: str):
		return self.get_child_by_name(name=pagePath) is not None

	def _setPageWindowTitle(self, pagePath: str):
		if not self._windowTitleEnable:
			return
		title = self._titles[pagePath]
		if not title:
			self._window.set_title(self._windowTitleMain)
			return
		if self._windowTitleMain:
			if self._windowTitleMainFirst:
				title = self._windowTitleMain + " - " + title
			else:
				title = title + " - " + self._windowTitleMain
		self._window.set_title(title)

	def tryToGotoPage(self, pagePath: str):
		while pagePath and not self.gotoPage(pagePath):
			dot = pagePath.rfind(".")
			if dot < 1:
				return
			pagePath = pagePath[:dot]

	def gotoPage(self, path: str, backward: bool = False) -> bool:
		log.debug(f"MyStack: gotoPage: {path=}, {backward=}")
		if not path:
			raise ValueError(f"gotoPage: empty page path")
		if path not in self._titles:
			log.error(f"gotoPage: invalid page {path=}")
			return False
		if backward:
			self._setSlideBackward()
		else:
			self._setSlideForward()
		self.set_visible_child_name(path)
		self.show()
		self._currentPagePath = path
		self._setPageWindowTitle(path)
		return True
