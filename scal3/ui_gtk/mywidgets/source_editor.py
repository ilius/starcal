import gi

from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk.utils import buffer_get_text

gi.require_version("GtkSource", "4")
from gi.repository import GtkSource

__all__ = ["SourceEditorWithFrame"]


class SourceEditor(GtkSource.View):
	def __init__(self, onTextChange=None) -> None:
		self.textbuffer = GtkSource.Buffer()
		GtkSource.View.__init__(self, buffer=self.textbuffer)
		self.set_editable(True)
		self.set_cursor_visible(True)
		self.set_show_line_numbers(True)
		self.set_wrap_mode(gtk.WrapMode.WORD)
		self.connect("key-press-event", self._key_press_event)

		if onTextChange is not None:
			self.textbuffer.connect("changed", onTextChange)

	def _key_press_event(self, _widget, event) -> None:
		keyvalobjName = gdk.keyval_name(event.keyval)
		ctrl = event.state & gdk.ModifierType.CONTROL_MASK
		if ctrl and keyvalobjName == "y":  # noqa: SIM102
			if self.textbuffer.can_redo():
				self.textbuffer.do_redo(self.textbuffer)


class SourceEditorWithFrame(gtk.Frame):
	def __init__(self, onTextChange=None) -> None:
		gtk.Frame.__init__(self)
		self.set_border_width(4)
		# ----
		self.editor = SourceEditor(
			onTextChange=onTextChange,
		)
		self.add(self.editor)

	def set_text(self, text) -> None:
		self.editor.textbuffer.set_text(text)

	def get_text(self):
		return buffer_get_text(self.editor.textbuffer)
