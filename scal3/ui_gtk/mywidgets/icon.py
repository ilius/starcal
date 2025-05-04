from os.path import join

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.path import (
	pixDir,
)
from scal3.ui import conf
from scal3.ui_gtk import Menu, gtk
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)
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

	def __init__(self, filename="") -> None:
		gtk.Button.__init__(self)
		self.image = gtk.Image()
		self.add(self.image)
		self._dialog = None
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

	def createDialog(self):
		if self._dialog:
			return self._dialog

		dialog = gtk.FileChooserDialog(
			title=_("Select Icon File"),
			action=gtk.FileChooserAction.OPEN,
			transient_for=getGtkWindow(self),
		)
		dialog_add_button(
			dialog,
			imageName="dialog-ok.svg",
			label=_("_Choose"),
			res=gtk.ResponseType.OK,
		)
		dialog_add_button(
			dialog,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			dialog,
			imageName="sweep.svg",
			label=_("Clear", ctx="window action"),
			res=gtk.ResponseType.REJECT,
		)

		dialog.connect("file-activated", self.fileActivated)
		dialog.connect("response", self.dialogResponse)
		self._dialog = dialog

		return dialog

	def onButtonPressEvent(self, _widget, gevent) -> None:
		b = gevent.button
		if b == 1:
			dialog = self.createDialog()
			dialog.set_filename(self.filename)
			dialog.run()
		elif b == 3:
			self.menu.popup(None, None, None, None, b, gevent.time)

	def menuItemActivate(self, _widget, icon) -> None:
		self.set_filename(icon)
		self.emit("changed", icon)

	def dialogResponse(self, dialog, response=0) -> None:
		dialog.hide()
		if response == gtk.ResponseType.OK:
			fname = dialog.get_filename()
		elif response == gtk.ResponseType.REJECT:
			fname = ""
		else:
			return
		self.set_filename(fname)
		self.emit("changed", fname)

	def _setImage(self, filename) -> None:
		self.image.set_from_pixbuf(
			pixbufFromFile(
				filename,
				conf.imageInputIconSize.v,
			),
		)

	def fileActivated(self, dialog) -> None:
		fname = dialog.get_filename()
		self.filename = fname
		self._setImage(self.filename)
		self.emit("changed", fname)
		dialog.hide()

	def get_filename(self):
		return self.filename

	def set_filename(self, filename) -> None:
		if filename is None:
			filename = ""
		if filename:
			filename = resolveImagePath(filename)
		self.filename = filename
		if not filename:
			self._setImage(join(pixDir, "empty.png"))
		else:
			self._setImage(filename)
