from __future__ import annotations

from typing import Protocol

from scal3.ui import conf
from scal3.ui_gtk import gtk

__all__ = ["MyProgressBar"]


class ProgressBarType(Protocol):
	w: gtk.Widget

	def set_text(self, text: str) -> None: ...

	def set_fraction(self, frac: float) -> None: ...


def MyProgressBar() -> ProgressBarType:
	if conf.oldStyleProgressBar.v:
		return OldStyleProgressBar()
	return NewStyleProgressBar()


class NewStyleProgressBar(gtk.ProgressBar):
	def __init__(self) -> None:
		gtk.ProgressBar.__init__(self)
		self.w = self
		self.set_show_text(True)


class OldStyleProgressBar(gtk.Overlay):
	def __init__(self) -> None:
		gtk.Overlay.__init__(self)
		self.w = self
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
