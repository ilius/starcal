from __future__ import annotations

import shutil
import tempfile
from typing import TYPE_CHECKING

import pytest

from scal3.event_lib import state
from scal3.event_lib.state import InfoWrapper, LastIdsWrapper
from scal3.filesystem import DefaultFileSystem

if TYPE_CHECKING:
	from collections.abc import Generator


@pytest.fixture  # type: ignore[untyped-decorator]
def fs() -> Generator[DefaultFileSystem, None, None]:
	"""
	Yield an isolated filesystem rooted in a fresh /tmp directory.

	The event data state is set up by hand instead of calling
	``event_lib.init()``: ``event_lib.init()`` writes a lock file into the real
	config directory (``~/.starcal3``) and reads its read-only flag. These
	tests must never read from or write to ``~/.starcal3``.
	"""
	tmpDir = tempfile.mkdtemp(prefix="starcal-event_lib-fs-test-")
	filesystem = DefaultFileSystem(tmpDir)
	filesystem.makeDir("event/events")
	filesystem.makeDir("event/groups")
	filesystem.makeDir("event/accounts")
	filesystem.makeDir("objects")

	state.allReadOnly = False
	state.info = InfoWrapper.s_load(0, fs=filesystem)
	state.lastIds = LastIdsWrapper.s_load(0, fs=filesystem)

	yield filesystem

	state.allReadOnly = False
	state.info = None
	state.lastIds = None
	shutil.rmtree(tmpDir)
