from scal3 import ui
from scal3.ui_gtk import gtk


def MyProgressBar():
	if ui.oldStyleProgressBar:
		return OldStyleProgressBar()
	return NewStyleProgressBar()


class NewStyleProgressBar(gtk.ProgressBar):
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		self.set_show_text(True)


class OldStyleProgressBar(gtk.Overlay):
	def __init__(self):
		gtk.Overlay.__init__(self)
		self.pbar = gtk.ProgressBar()
		self.pbar.set_show_text(False)
		self.label = gtk.Label()
		self.add(self.pbar)
		self.add_overlay(self.label)
		self.show_all()

	def set_text(self, text: str) -> None:
		self.label.set_text(text)

	def set_fraction(self, frac: float) -> None:
		self.pbar.set_fraction(frac)
