from datetime import datetime
from time import time as now

from scal3.locale_man import tr as _

__all__ = [
	"compressLongInt",
	"eventTextSep",
	"getCompactTime",
	"getCurrentJd",
	"weekDayName",
	"weekDayNameEnglish",
]


# to separate summary from description for display
eventTextSep = ": "

weekDayNameEnglish = (
	"Sunday",
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
)
weekDayName = tuple(_(name) for name in weekDayNameEnglish)


def getCurrentJd() -> int:
	return datetime.now().toordinal() + 1721425


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
