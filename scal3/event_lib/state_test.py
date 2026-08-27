from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.event_lib.state import InfoWrapper, LastIdsWrapper

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem


def test_last_ids_roundtrip(fs: FileSystem) -> None:
	"""LastIdsWrapper persists its counters to disk."""
	wrapper = LastIdsWrapper.s_load(0, fs=fs)
	wrapper.event = 5
	wrapper.group = 3
	wrapper.account = 1
	wrapper.save()
	assert fs.isfile("event/last_ids.json")

	reloaded = LastIdsWrapper.s_load(0, fs=fs)
	assert reloaded.event == 5
	assert reloaded.group == 3
	assert reloaded.account == 1


def test_info_wrapper_roundtrip(fs: FileSystem) -> None:
	"""InfoWrapper persists version and last-run to disk."""
	wrapper = InfoWrapper.s_load(0, fs=fs)
	wrapper.update()
	wrapper.save()
	assert fs.isfile("event/info.json")

	reloaded = InfoWrapper.s_load(0, fs=fs)
	assert reloaded.version == wrapper.version
	assert reloaded.last_run == wrapper.last_run
