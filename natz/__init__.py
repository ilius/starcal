#!/usr/bin/env python3

# Python 3.9 added support for the IANA Time Zone Database
# in the Standard Library
# https://www.python.org/dev/peps/pep-0615/

import logging
log = logging.getLogger("root")

import os
from os.path import split, join, islink, isfile
import datetime
import dateutil.tz

from typing import Optional

defaultTZ = None
tzErrCount = 0


class TimeZone(datetime.tzinfo):
	def __init__(self, tz):
		self._tz = tz
		if os.sep == "\\":
			self._name = tz.tzname(datetime.datetime.now())
		else:
			parts = tz._filename.split("/")
			self._name = "/".join(parts[-2:])

	def __str__(self):
		# This is the only function that we needed to override on dateutil.tz.tzfile
		return self._name

	def utcoffset(self, dt):
		return self._tz.utcoffset(dt)

	def dst(self, dt):
		return self._tz.dst(dt)

	def tzname(self, dt):
		return self._tz.tzname(dt)


def readEtcLocaltime():
	# TODO: maybe use tzlocal -> unix.py -> _get_localzone_name:
	# https://github.com/regebro/tzlocal/blob/master/tzlocal/unix.py
	if not islink("/etc/localtime"):
		if isfile("/var/db/zoneinfo"):
			with open("/var/db/zoneinfo") as _file:
				tzname = _file.read().strip()
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
	tzname = "/".join(parts[index + 1:])
	return dateutil.tz.gettz(tzname)


def gettz(*args, **kwargs) -> Optional[TimeZone]:
	global tzErrCount
	if args and args[0].lstrip("/") == "etc/localtime":
		return readEtcLocaltime()
	tz = dateutil.tz.gettz(*args, **kwargs)
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
			log.error(f"failed to detect timezone: {args} {kwargs}")
		tzErrCount += 1
		return defaultTZ
	if tz._filename.lstrip("/") == "etc/localtime":
		tz = readEtcLocaltime()
		if tz is None:
			if tzErrCount < 5:
				log.error(f"failed to detect timezone")
			tzErrCount += 1
			return defaultTZ
	return TimeZone(tz)


UTC = gettz("UTC")
