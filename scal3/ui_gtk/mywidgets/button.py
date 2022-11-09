#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

from typing import Optional
from time import time as now
import sys

from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud


class ConButtonBase:
	def __init__(self, button: Optional[int] = None):
		self.pressTm = 0
		self.counter = 0
		self._button = button
		###
		self.connect("button-press-event", self.onPress)
		self.connect("button-release-event", self.onRelease)

	def doTrigger(self):
		return self.emit("con-clicked")

	def onPress(self, widget, event):
		if self._button is not None:
			if event.button != self._button:
				return
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

	def onRelease(self, widget, event):
		self.counter += 1
		return True

	def onPressRemain(self, func, counter):
		if (
			counter == self.counter and
			now() - self.pressTm >= ui.timeout_repeat / 1000
		):
			func()
			timeout_add(
				ui.timeout_repeat,
				self.onPressRemain,
				self.doTrigger,
				self.counter,
			)


@registerSignals
class ConButton(gtk.Button, ConButtonBase):
	signals = [
		("con-clicked", []),
	]

	def __init__(self, *args, **kwargs):
		gtk.Button.__init__(self, *args, **kwargs)
		ConButtonBase.__init__(self)


if __name__ == "__main__":
	win = gtk.Dialog()
	button = ConButton("Press")

	def con_clicked(arg):
		log.info(f"{now():.4f}\tcon-clicked")

	button.connect("con-clicked", con_clicked)
	pack(win.vbox, button, 1, 1)
	win.vbox.show_all()
	win.resize(100, 100)
	win.run()
