from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.utils import imageFromFile

if TYPE_CHECKING:
	from scal3.ui_gtk.pytypes import StackPageType
	from scal3.ui_gtk.stack import MyStack

__all__ = ["newWideButton"]


class PrefWinType(Protocol):
	spacing: int
	stack: MyStack

	def onPageButtonClicked(self, _w: gtk.Widget, page: StackPageType) -> None: ...


def newWideButton(prefWin: PrefWinType, page: StackPageType) -> gtk.Button:
	spacing = prefWin.spacing
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
	hbox.set_border_width(spacing)
	label = gtk.Label(label=page.pageLabel)
	label.set_use_underline(True)
	pack(hbox, gtk.Label(), 1, 1)
	iconSize = page.iconSize or prefWin.stack.iconSize()
	if page.pageIcon and conf.buttonIconEnable.v:
		pack(hbox, imageFromFile(page.pageIcon, iconSize))
	pack(hbox, label, 0, 0)
	pack(hbox, gtk.Label(), 1, 1)
	button = gtk.Button()
	button.add(hbox)

	button.connect("clicked", prefWin.onPageButtonClicked, page)
	return button
