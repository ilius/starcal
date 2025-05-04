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
from scal3 import logger
from scal3.ui import conf

log = logger.get()


from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, VBox, gdk, gtk, pack
from scal3.ui_gtk.utils import imageFromFile

__all__ = ["MyStack", "StackPage"]


class StackPage:
	def __init__(self) -> None:
		self.pageWidget = None
		self.pageParent = ""
		self.pageName = ""
		self.pagePath = ""
		self.pageTitle = ""
		self.pageLabel = ""
		self.pageIcon = ""
		self.pageExpand = True
		self.pageItem = None

	def __str__(self) -> str:
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
	) -> None:
		gtk.Stack.__init__(self)
		self.set_transition_duration(300)  # milliseconds
		# ---
		self._header = header
		self._rtl = self.get_direction() == gtk.TextDirection.RTL  # type: bool
		self._iconSize = iconSize  # type: int
		self._headerSpacing = headerSpacing  # type: int
		self._verticalSlide = verticalSlide  # type: bool
		# ---
		self._parentPaths: dict[str, str] = {}
		self._currentPagePath = ""
		self._titles: dict[str, str] = {}
		# ---
		self.connect("key-press-event", self.onKeyPress)
		# ---
		self._titleFontSize = "x-small"
		self._titleCentered = False
		# ---
		self._windowTitleEnable = False
		self._window = None
		self._windowTitleMain = ""
		self._windowTitleMainFirst = False

	def iconSize(self) -> int:
		return self._iconSize

	def currentPagePath(self) -> str:
		return self._currentPagePath

	def setTitleFontSize(self, fontSize: str) -> None:
		"""
		Font size in 1024ths of a point, or one of the absolute sizes
		'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large',
		or one of the relative sizes 'smaller' or 'larger'.
		If you want to specify a absolute size, it's usually easier to take
		advantage of the ability to specify a partial font description using 'font';
		you can use font='12.5' rather than size='12800'.
		https://developer.gnome.org/pango/stable/PangoMarkupFormat.html#PangoMarkupFormat.
		"""
		self._titleFontSize = fontSize

	def setTitleCentered(self, centered: bool) -> None:
		self._titleCentered = centered

	def setupWindowTitle(
		self,
		window: gtk.Window,
		mainTitle: str,
		mainTitleFirst: bool,
	) -> None:
		self._windowTitleEnable = True
		self._window = window
		self._windowTitleMain = mainTitle
		self._windowTitleMainFirst = mainTitleFirst

	def onKeyPress(self, _arg, gevent) -> bool:
		if gdk.keyval_name(gevent.keyval) == "BackSpace":  # noqa: SIM102
			if self._currentPagePath:
				parentPath = self._parentPaths[self._currentPagePath]
				if parentPath:
					self.gotoPage(parentPath, backward=True)
					return True
		return False

	def _setSlideForward(self) -> None:
		self.set_transition_type(
			gtk.RevealerTransitionType.SLIDE_DOWN
			if self._verticalSlide
			else gtk.RevealerTransitionType.SLIDE_LEFT,
		)

	def _setSlideBackward(self) -> None:
		self.set_transition_type(
			gtk.RevealerTransitionType.SLIDE_UP
			if self._verticalSlide
			else gtk.RevealerTransitionType.SLIDE_RIGHT,
		)

	def _newHeaderBox(self, parentName: str, title: str = "", icon: str = ""):
		spacing = 10
		hbox = HBox(spacing=spacing)
		# hbox.set_direction(gtk.TextDirection.LTR)
		backButton = gtk.Button()
		backHbox = HBox(spacing=3)
		backHbox.set_border_width(5)
		backText = _("Back")
		if conf.buttonIconEnable.v:
			pack(
				backHbox,
				imageFromFile(
					"go-next.svg" if self._rtl else "go-previous.svg",
					size=self._iconSize,
				),
			)
		else:
			backText = "  " + backText + "  "  # to make it bigger
		backLabel = gtk.Label(label=backText)
		pack(backHbox, backLabel)
		backButton.add(backHbox)
		backButton.connect(
			"clicked",
			lambda _w: self.gotoPage(parentName, backward=True),
		)
		pack(hbox, backButton)
		pack(hbox, gtk.Label(), 1, 1)
		if icon:
			pack(hbox, imageFromFile(icon, self._iconSize), 0, 0)
		if title:
			if self._titleFontSize:
				title = f'<span font_size="{self._titleFontSize}">{title}</span>'
			label = gtk.Label(label=title)
			if self._titleFontSize:
				label.set_use_markup(True)
			pack(hbox, label, 0, 0)
			if self._titleCentered:
				if icon:
					iconImg = imageFromFile("empty.png", self._iconSize + spacing)
					pack(hbox, iconImg, 0, 0)
				pack(hbox, gtk.Label(), 1, 1)
				dummyLabel = gtk.Label()
				sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
				sizeGroup.add_widget(dummyLabel)
				sizeGroup.add_widget(backLabel)
				pack(hbox, dummyLabel, 0, 0)
		hbox.show_all()
		return hbox

	def addPage(self, page: StackPage) -> None:
		pagePath = page.pagePath
		log.debug(f"MyStack: {pagePath=}")
		parentName = page.pageParent
		widget = page.pageWidget

		if pagePath in self._titles:
			raise ValueError(f"addPage: duplicate {pagePath=}")

		if not isinstance(widget, gtk.Widget):
			raise TypeError(f"invalid {widget=}, {pagePath=}")

		widget.show()
		if self._header and parentName:
			vbox = VBox(spacing=self._headerSpacing)
			pack(
				vbox,
				self._newHeaderBox(
					parentName,
					title=page.pageTitle,
					icon=page.pageIcon,
				),
			)
			pack(vbox, widget, expand=page.pageExpand, fill=page.pageExpand)
			vbox.show()
			widget = vbox
		self.add_named(widget, name=pagePath)
		# --
		self._parentPaths[pagePath] = parentName
		self._titles[pagePath] = page.pageTitle
		# --
		if not self._currentPagePath:
			self.gotoPage(pagePath)

	def hasPage(self, pagePath: str):
		return self.get_child_by_name(name=pagePath) is not None

	def _setPageWindowTitle(self, pagePath: str) -> None:
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

	def tryToGotoPage(self, pagePath: str) -> None:
		while pagePath and not self.gotoPage(pagePath):
			dot = pagePath.rfind(".")
			if dot < 1:
				return
			pagePath = pagePath[:dot]

	def gotoPage(self, path: str, backward: bool = False) -> bool:
		log.debug(f"MyStack: gotoPage: {path=}, {backward=}")
		if not path:
			raise ValueError("gotoPage: empty page path")
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
