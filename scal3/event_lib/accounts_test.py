from __future__ import annotations

from typing import TYPE_CHECKING

from scal3 import event_lib

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem


def test_account_save_to_disk(fs: FileSystem) -> None:
	"""An account is persisted as a JSON file in the temp filesystem."""
	account = event_lib.Account()
	account.fs = fs
	account.title = "my-account"
	account.save()
	assert account.id is not None
	assert fs.isfile(account.file)
