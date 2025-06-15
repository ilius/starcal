from datetime import datetime
from time import time as now

from scal3 import locale_man

__all__ = ["compressLongInt", "eventTextSep", "getCompactTime", "getCurrentJd"]


# to separate summary from description for display
eventTextSep = ": "


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


def compressLongInt(num: int) -> str:
	"""Num must be less than 2**64."""
	from base64 import b64encode
	from struct import pack

	return (
		b64encode(
			pack("L", num % 2**64).rstrip(b"\x00"),
		)[:-3]
		.decode("ascii")
		.replace("/", "_")
	)


def getCompactTime(maxDays: int = 1000, minSec: float = 0.1) -> str:
	return compressLongInt(
		int(
			now() % (maxDays * 86400) / minSec,
		),
	)
