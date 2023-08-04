#!/usr/bin/env python3
from scal3.ui_gtk import *


class MyProgressBar(gtk.ProgressBar):
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)

