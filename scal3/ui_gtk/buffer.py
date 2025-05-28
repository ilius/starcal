from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterable

	from gi.repository import Gtk as gtk

__all__ = ["GtkBufferFile"]

"""Thanks to "Pier Carteri" <m3tr0@dei.unipd.it> for program Py_Shell.py."""


class GtkBufferFile:
	"""Implements a file-like object for redirect the stream to the buffer."""

	def __init__(self, buff: gtk.TextBuffer, tag: gtk.TextTag) -> None:
		self.buffer = buff
		self.tag = tag

	def write(self, text: str) -> None:
		"""Write text into the buffer and apply self.tag."""
		# text = text.replace("\x00", "")
		self.buffer.insert_with_tags(
			self.buffer.get_end_iter(),
			text,
			self.tag,
		)

	def writelines(self, lines: Iterable[str]) -> None:
		list(map(self.write, lines))

	def flush(self) -> None:  # noqa: PLR6301
		return None

	def isatty(self) -> bool:  # noqa: PLR6301
		return False
