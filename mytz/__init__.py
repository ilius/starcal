# mypy: ignore-errors
# Python 3.9 added support for the IANA Time Zone Database
# in the Standard Library
# https://www.python.org/dev/peps/pep-0615/

from __future__ import annotations

import logging

log = logging.getLogger("root")

import datetime
import os
from os.path import isfile, islink
from typing import TYPE_CHECKING

import dateutil.tz

if TYPE_CHECKING:
	from dateutil.tz.tz import tzfile


__all__ = ["UTC", "defaultTZ", "gettz"]

defaultTZ: TimeZone | None = None
tzErrCount = 0


class TimeZone(datetime.tzinfo):
	def __init__(self, tz: tzfile) -> None:
		self._tz = tz
		if os.sep == "\\":
			self._name = tz.tzname(datetime.datetime.now())
		else:
			parts = tz._filename.split("/")  # noqa: SLF001
			self._name = "/".join(parts[-2:])

	def __str__(self) -> str:
		# This is the only function that we needed to override on dateutil.tz.tzfile
		return self._name

	def utcoffset(self, dt: datetime.datetime | None) -> datetime.timedelta | None:
		return self._tz.utcoffset(dt)

	def dst(self, dt: datetime.datetime | None) -> bool:
		return self._tz.dst(dt)

	def tzname(self, dt: datetime.datetime | None) -> str:
		return self._tz.tzname(dt)


def readEtcLocaltime() -> datetime.tzinfo | None:
	# TODO: maybe use tzlocal -> unix.py -> _get_localzone_name:
	# https://github.com/regebro/tzlocal/blob/master/tzlocal/unix.py
	if not islink("/etc/localtime"):
		if isfile("/var/db/zoneinfo"):
			with open("/var/db/zoneinfo", encoding="utf-8") as file:
				tzname = file.read().strip()
				return dateutil.tz.gettz(tzname)
		# 'zdump /etc/localtime' does not show timezone's name
		return dateutil.tz.tzfile("/etc/localtime")
	fpath = os.readlink("/etc/localtime")
	parts = fpath.split("/")
	try:
		index = parts.index("zoneinfo")
	except ValueError:
		log.error(f"Unexpected timezone file: {fpath}")
		return
	tzname = "/".join(parts[index + 1 :])
	return dateutil.tz.gettz(tzname)


def gettz(name: str = "") -> TimeZone | None:
	global tzErrCount
	if name and name.lstrip("/") == "etc/localtime":
		return readEtcLocaltime()
	tz = dateutil.tz.gettz(name=name)
	"""
	FileNotFoundError: [Errno 2] No such file or directory:
	'/usr/lib/python3/dist-packages/dateutil/zoneinfo/dateutil-zoneinfo.tar.gz'
	on Python 3.10.5
	tested with 2.8.1-6 from debian python3-dateutil
	tested with 2.8.2 from pip
	tested with 2.7.0 from pip
	tested with 2.6.0 from pip
	"""
	if tz is None:
		if tzErrCount < 5:
			log.error(f"failed to detect timezone: {name=}")
		tzErrCount += 1
		return defaultTZ
	if tz._filename.lstrip("/") == "etc/localtime":  # noqa: SLF001
		tz = readEtcLocaltime()
		if tz is None:
			if tzErrCount < 5:
				log.error("failed to detect timezone")
			tzErrCount += 1
			return defaultTZ
	return TimeZone(tz)


UTC = gettz("UTC")
