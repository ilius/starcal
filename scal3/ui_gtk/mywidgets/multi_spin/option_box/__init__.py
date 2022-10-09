#!/usr/bin/env python3
from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import imageClassButton
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton


@registerSignals
class MultiSpinOptionBox(gtk.Box):
	signals = [
		("activate", [])
	]

	def _entry_activate(self, widget):
		# self.spin.update() #?????
		# self.add_history()
		self.emit("activate")
		return False

	def __init__(
		self,
		sep,
		fields,
		spacing=0,
		is_hbox=False,
		hist_size=10,
		**kwargs
	):
		if not is_hbox:
			gtk.Box.__init__(
				self,
				orientation=gtk.Orientation.HORIZONTAL,
				spacing=spacing,
			)
		self.spin = MultiSpinButton(sep=sep, fields=fields, **kwargs)
		pack(self, self.spin, 1, 1)
		self.hist_size = hist_size
		self.option = imageClassButton(
			"pan-down-symbolic",
			"down",  # FIXME: same class as decrease button?
			MultiSpinButton.buttonSize,
		)
		pack(self, self.option, 1, 1)
		self.menu = Menu()
		#self.menu.show()
		self.option.connect("button-press-event", self.option_pressed)
		self.menuItems = []
		# self.option.set_sensitive(False) #???????
		# self.spin._entry_activate = self._entry_activate
		self.spin.connect("activate", self._entry_activate)
		self.get_value = self.spin.get_value
		self.set_value = self.spin.set_value

	def option_pressed(self, widget, gevent):
		#x, y, w, h = self.option.
		self.menu.popup(None, None, None, None, gevent.button, gevent.time)

	def find_text(self, text):
		for index, item in enumerate(self.menuItems):
			if item.text == text:
				return index
		return -1

	def add_history(self):
		self.spin.update()
		text = self.spin.get_text()
		index = self.find_text(text)
		if index == 0:
			return
		if index > 0:
			self.menu.remove(self.menuItems.pop(index))
		# m.prepend([text]) # self.combo.prepend_text(text)
		item = MenuItem(text)
		item.connect("activate", lambda obj: self.spin.set_text(text))
		item.text = text
		self.menu.add(item)
		self.menu.reorder_child(item, 0)
		self.menuItems.insert(0, item)
		if len(self.menuItems) > self.hist_size:
			self.menu.remove(self.menuItems.pop(-1))
		self.menu.show_all()
		# self.option.set_sensitive(True) #???????

	def clear_history(self):
		for item in self.menu.get_children():
			self.menu.remove(item)
