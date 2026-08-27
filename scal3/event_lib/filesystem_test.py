from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem


def test_fs_roots_under_tmp(fs: FileSystem) -> None:
	"""The test filesystem must live under /tmp, never under ~/.starcal3."""
	assert fs.abspath(".") != "/"
	assert fs.abspath(".").startswith(tempfile.gettempdir())
