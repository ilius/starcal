from __future__ import annotations

from os.path import join

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.path import pixDir
from scal3.ui import conf
from scal3.ui_gtk import Menu, gdk, gtk
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import (
	dialog_add_button,
	getGtkWindow,
	pixbufFromFile,
	resolveImagePath,
)

__all__ = ["IconSelectButton"]
# FIXME
# for uknown reason, the file chooser dialog comes logically behind it's parent
# so it's not capturing mouse and keyboard unless you press Escape that closes
# the parent, and so making this widget useless unless you use icons from the
# right-click menu


@registerSignals
class IconSelectButton(gtk.Button):
	signals = [
		("changed", [str]),
	]

	def __init__(self, filename: str = "") -> None:
		gtk.Button.__init__(self)
		self.image = gtk.Image()
		self.add(self.image)
		self._dialog: gtk.FileChooserDialog | None = None
		# ---
		menu = Menu()
		self.menu = menu
		menu.add(
			ImageMenuItem(
				_("None"),
				func=self.menuItemActivate,
				args=("",),
			),
		)
		for item in ui.eventTags:
			icon = item.getIconRel()
			if not icon:
				continue
			menu.add(
				ImageMenuItem(
					_(item.desc),
					imageName=icon,
					func=self.menuItemActivate,
					args=(icon,),
				),
			)
		menu.show_all()
		# ---
		# self.connect("clicked", lambda button: button.dialog.run())
		self.connect("button-press-event", self.onButtonPressEvent)
		# ---
		self.set_filename(filename)

	def createDialog(self) -> gtk.FileChooserDialog:
		if self._dialog:
			return self._dialog

		dialog = gtk.FileChooserDialog(
			title=_("Select Icon File"),
			action=gtk.FileChooserAction.OPEN,
			transient_for=getGtkWindow(self),
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			dialog,
			res=gtk.ResponseType.REJECT,
			imageName="sweep.svg",
			label=_("Clear", ctx="window action"),
		)

		dialog.connect("file-activated", self.fileActivated)
		dialog.connect("response", self.dialogResponse)
		self._dialog = dialog

		return dialog

	def onButtonPressEvent(self, _w: gtk.Widget, gevent: gdk.EventButton) -> None:
		button = gevent.button
		if button == 1:
			dialog = self.createDialog()
			dialog.set_filename(self.filename or "")
			dialog.run()
		elif button == 3:
			self.menu.popup(None, None, None, None, button, gevent.time)

	def menuItemActivate(self, _w: gtk.Widget, icon: str) -> None:
		self.set_filename(icon)
		self.emit("changed", icon)

	def dialogResponse(
		self,
		dialog: gtk.FileChooserDialog,
		response: gtk.ResponseType = gtk.ResponseType.OK,
	) -> None:
		dialog.hide()
		if response == gtk.ResponseType.OK:
			fname = dialog.get_filename()
		elif response == gtk.ResponseType.REJECT:
			fname = ""
		else:
			return
		self.set_filename(fname)
		self.emit("changed", fname)

	def _setImage(self, filename: str) -> None:
		self.image.set_from_pixbuf(
			pixbufFromFile(
				filename,
				conf.imageInputIconSize.v,
			),
		)

	def fileActivated(self, dialog: gtk.FileChooserDialog) -> None:
		fname = dialog.get_filename()
		self.filename = fname
		if fname:
			self._setImage(fname)
		self.emit("changed", fname)
		dialog.hide()

	def get_filename(self) -> str:
		return self.filename or ""

	def set_filename(self, filename: str | None) -> None:
		if filename is None:
			filename = ""
		if filename:
			filename = resolveImagePath(filename)
		self.filename = filename
		self._setImage(filename or join(pixDir, "empty.png"))
