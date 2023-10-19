from scal3.ui_gtk import gtk


class MyProgressBar(gtk.ProgressBar):
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)
