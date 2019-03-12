#!/usr/bin/env python3
from scal3 import ui
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk import *

class MyProgressBar(gtk.ProgressBar):
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)

		# removing transparency from text color
		color = self.get_style_context().get_color(gtk.StateFlags.NORMAL)
		color.alpha = 1.0
		self.override_color(gtk.StateFlags.NORMAL, color)

		# fix the font family and size
		self.update_font()

		# override_color and override_font are deprecated since version 3.16
		# override_color: doc says: Use a custom style provider and style classes instead
		# override_font: This function is not useful in the context of CSS-based rendering.
		# If you wish to change the font a widget uses to render its text you should use a custom CSS style,
		# through an application-specific Gtk.StyleProvider and a CSS style class.

	def update_font(self):
		self.override_font(pfontEncode(ui.getFont()))
