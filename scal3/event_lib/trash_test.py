from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.event_lib.handler import Handler
from scal3.event_lib.trash import EventTrash

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem


def test_trash_save_load_roundtrip(fs: FileSystem) -> None:
	"""The trash container round-trips through disk."""
	handler = Handler()
	handler.init(fs)
	handler.trash.save()
	assert fs.isfile(handler.trash.file)

	trash = EventTrash.s_load(0, fs=fs)
	assert isinstance(trash, EventTrash)
