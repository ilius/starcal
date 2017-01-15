from os.path import join

from scal3.path import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import labelStockMenuItem


@registerSignals
class IconSelectButton(gtk.Button):
	signals = [
		("changed", [str]),
	]

	def __init__(self, filename=""):
		gtk.Button.__init__(self)
		self.image = gtk.Image()
		self.add(self.image)
		self.dialog = gtk.FileChooserDialog(
			title=_("Select Icon File"),
			action=gtk.FileChooserAction.OPEN,
		)
		okB = self.dialog.add_button(gtk.STOCK_OK, gtk.ResponseType.OK)
		cancelB = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL)
		clearB = self.dialog.add_button(gtk.STOCK_CLEAR, gtk.ResponseType.REJECT)
		if ui.autoLocale:
			cancelB.set_label(_("_Cancel"))
			cancelB.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_CANCEL,
				gtk.IconSize.BUTTON,
			))
			okB.set_label(_("_OK"))
			okB.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_OK,
				gtk.IconSize.BUTTON,
			))
			clearB.set_label(_("Clear"))
			clearB.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_CLEAR,
				gtk.IconSize.BUTTON,
			))
		###
		menu = gtk.Menu()
		self.menu = menu
		menu.add(labelStockMenuItem(_("None"), None, self.menuItemActivate, ""))
		for item in ui.eventTags:
			icon = item.icon
			if icon:
				menuItem = ImageMenuItem(item.desc)
				menuItem.set_image(gtk.Image.new_from_file(icon))
				menuItem.connect("activate", self.menuItemActivate, icon)
				menu.add(menuItem)
		menu.show_all()
		###
		self.dialog.connect("file-activated", self.fileActivated)
		self.dialog.connect("response", self.dialogResponse)
		#self.connect("clicked", lambda button: button.dialog.run())
		self.connect("button-press-event", self.buttonPressEvent)
		###
		self.set_filename(filename)

	def buttonPressEvent(self, widget, gevent):
		b = gevent.button
		if b == 1:
			self.dialog.run()
		elif b == 3:
			self.menu.popup(None, None, None, None, b, gevent.time)

	def menuItemActivate(self, widget, icon):
		self.set_filename(icon)

	def dialogResponse(self, dialog, response=0):
		dialog.hide()
		if response == gtk.ResponseType.OK:
			fname = dialog.get_filename()
		elif response == gtk.ResponseType.REJECT:
			fname = ""
		else:
			return
		self.set_filename(fname)
		self.emit("changed", fname)

	def fileActivated(self, dialog):
		fname = dialog.get_filename()
		self.filename = fname
		self.image.set_from_file(self.filename)
		self.emit("changed", fname)
		self.dialog.hide()

	def get_filename(self):
		return self.filename

	def set_filename(self, filename):
		if filename is None:
			filename = ""
		self.dialog.set_filename(filename)
		self.filename = filename
		if not filename:
			self.image.set_from_file(join(pixDir, "empty.png"))
		else:
			self.image.set_from_file(filename)
