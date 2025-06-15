from datetime import datetime
from time import time as now

from scal3 import locale_man

__all__ = ["eventTextSep", "getCurrentJd"]

eventTextSep = ": "  # to separate summary from description for display


def getCurrentJd() -> int:
	tz = locale_man.localTz
	assert tz is not None
	epoch = now()
	return (
		int(
			(
				epoch + int(tz.utcoffset(datetime.fromtimestamp(epoch)).total_seconds())  # noqa: DTZ006
			)
			/ 86400
		)
		+ 2440588
	)
