from scal3.ui_gtk import *

class MyProgressBar(gtk.ProgressBar):
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)

		# removing transparency from text color
		color = self.get_style_context().get_color(gtk.StateFlags.NORMAL)
		color.alpha = 1.0
		self.override_color(gtk.StateFlags.NORMAL, color)
