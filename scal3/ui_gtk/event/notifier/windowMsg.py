from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gi.repository import GLib as glib

from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, HBox, gtk, pack
from scal3.ui_gtk.utils import dialog_add_button, imageFromFile

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.event_lib.notifier_base import EventNotifier
	from scal3.event_lib.pytypes import EventNotifierType

__all__ = ["WidgetClass", "notify"]


class WidgetClass(gtk.Entry):
	def show(self) -> None:
		gtk.Entry.show(self.w)

	def __init__(self, notifier: EventNotifierType) -> None:
		self.notifier = notifier
		gtk.Entry.__init__(self)
		self.w = self

	def updateWidget(self) -> None:
		self.set_text(self.notifier.extraMessage)

	def updateVars(self) -> None:
		self.notifier.extraMessage = self.get_text()


def hideWindow(_widget: gtk.Widget, dialog: gtk.Window) -> bool:
	dialog.hide()
	return True


def response(dialog: gtk.Window, _e: Any) -> None:
	dialog.destroy()


def notify(notifier: EventNotifier, _finishFunc: Callable[[], None]) -> None:
	print("------------ windowsMsg.notify")
	glib.idle_add(_notify, notifier)


def _notify(notifier: EventNotifier) -> None:
	event = notifier.event
	dialog = Dialog()
	# ----
	lines = []
	lines.append(event.getText())
	if notifier.extraMessage:
		lines.append(notifier.extraMessage)
	text = "\n".join(lines)
	# ----
	dialog.set_title(event.getText())
	# ----
	hbox = HBox(spacing=15)
	hbox.set_border_width(10)
	if event.icon:
		pack(hbox, imageFromFile(event.icon))
		dialog.set_icon_from_file(event.icon)
	label = gtk.Label(label=text)
	label.set_selectable(True)
	pack(hbox, label, 1, 1)
	pack(dialog.vbox, hbox)  # type: ignore[arg-type]
	# ----
	okB = dialog_add_button(
		dialog,
		res=gtk.ResponseType.OK,
		imageName="dialog-ok.svg",
		label=_("_Close"),
	)
	okB.connect("clicked", lambda _w, _e: dialog.response(gtk.ResponseType.OK))
	dialog.vbox.show_all()  # type: ignore[attr-defined]
	dialog.connect("response", response)
	dialog.present()
