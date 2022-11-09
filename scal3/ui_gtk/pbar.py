#!/usr/bin/env python3
from scal3 import ui
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk import *
from scal3.ui_gtk.color_utils import gdkColorToRgb
from scal3.ui_gtk import gtk_ud as ud


class MyProgressBar(gtk.ProgressBar):
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)

