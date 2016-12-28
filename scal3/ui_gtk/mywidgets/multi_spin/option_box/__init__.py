from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton


@registerSignals
class MultiSpinOptionBox(gtk.HBox):
	signals = [
		('activate', [])
	]

	def _entry_activate(self, widget):
		#self.spin.update() #?????
		#self.add_history()
		self.emit('activate')
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
			gtk.HBox.__init__(self, spacing=spacing)
		self.spin = MultiSpinButton(sep, fields, **kwargs)
		pack(self, self.spin, 1, 1)
		self.hist_size = hist_size
		self.option = gtk.Button()
		self.option.add(gtk.Arrow(gtk.ArrowType.DOWN, gtk.ShadowType.IN))
		pack(self, self.option, 1, 1)
		self.menu = gtk.Menu()
		#self.menu.show()
		self.option.connect('button-press-event', self.option_pressed)
		self.menuItems = []
		#self.option.set_sensitive(False) #???????
		#self.spin._entry_activate = self._entry_activate
		self.spin.connect('activate', self._entry_activate)
		self.get_value = self.spin.get_value
		self.set_value = self.spin.set_value

	def option_pressed(self, widget, gevent):
		#x, y, w, h = self.option.
		self.menu.popup(None, None, None, None, gevent.button, gevent.time)

	def add_history(self):
		self.spin.update()
		text = self.spin.get_text()
		found = -1
		n = len(self.menuItems)
		for i in range(n):
			if self.menuItems[i].text == text:
				found = i
				break
		if found > -1:
			self.menu.remove(self.menuItems.pop(found))
		else:
			n += 1
		#m.prepend([text])#self.combo.prepend_text(text)
		item = MenuItem(text)
		item.connect('activate', lambda obj: self.spin.set_text(text))
		item.text = text
		self.menu.add(item)
		self.menu.reorder_child(item, 0)
		if n > self.hist_size:
			self.menu.remove(self.menuItems.pop(n - 1))
		self.menu.show_all()
		#self.option.set_sensitive(True) #???????

	def clear_history(self):
		for item in self.menu.get_children():
			self.menu.remove(item)
