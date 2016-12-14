from time import time as now
import sys

from scal3 import ui

from gi.repository import GObject
from gi.repository.GObject import timeout_add

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud


class ConButtonBase:
	def __init__(self):
		self.pressTm = 0
		self.counter = 0
		###
		self.connect("button-press-event", self.onPress)
		self.connect("button-release-event", self.onRelease)
	def doTrigger(self):
		return self.emit("con-clicked")
	def onPress(self, widget, event=None):
		self.pressTm = now()
		self.doTrigger()
		self.counter += 1
		timeout_add(
			ui.timeout_initial,
			self.onPressRemain,
			self.doTrigger,
			self.counter,
		)
		return True
	def onRelease(self, widget, event=None):
		self.counter += 1
		return True
	def onPressRemain(self, func, counter):
		if counter == self.counter and now() - self.pressTm >= ui.timeout_repeat / 1000:
			func()
			timeout_add(
				ui.timeout_repeat,
				self.onPressRemain,
				self.doTrigger,
				self.counter,
			)


@registerSignals
class ConButton(gtk.Button, ConButtonBase):
	signals =[
		('con-clicked', []),
	]
	def __init__(self, *args, **kwargs):
		gtk.Button.__init__(self, *args, **kwargs)
		ConButtonBase.__init__(self)




if __name__=='__main__':
	win = gtk.Dialog(parent=None)
	button = ConButton('Press')
	button.connect('con-clicked', lambda obj: sys.stdout.write('%.4f\n'%now()))
	pack(win.vbox, button, 1, 1)
	win.vbox.show_all()
	win.resize(100, 100)
	win.run()



