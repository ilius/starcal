import os
import os.path
import datetime
from .exceptions import *
from .directory import infoDir


_tzinfo_cache = {}

__all__ = [
	'timezone',
	'infoDir',
]


def timezone(name):
	r''' Return a datetime.tzinfo implementation for the given timezone

	>>> from datetime import datetime, timedelta
	>>> utc = timezone('UTC')
	>>> eastern = timezone('US/Eastern')
	>>> eastern.zone
	'US/Eastern'
	>>> timezone(unicode('US/Eastern')) is eastern
	True
	>>> utc_dt = datetime(2002, 10, 27, 6, 0, 0, tzinfo=utc)
	>>> loc_dt = utc_dt.astimezone(eastern)
	>>> fmt = '%Y-%m-%d %H:%M:%S %Z (%z)'
	>>> loc_dt.strftime(fmt)
	'2002-10-27 01:00:00 EST (-0500)'
	>>> (loc_dt - timedelta(minutes=10)).strftime(fmt)
	'2002-10-27 00:50:00 EST (-0500)'
	>>> eastern.normalize(loc_dt - timedelta(minutes=10)).strftime(fmt)
	'2002-10-27 01:50:00 EDT (-0400)'
	>>> (loc_dt + timedelta(minutes=10)).strftime(fmt)
	'2002-10-27 01:10:00 EST (-0500)'

	Raises UnknownTimeZoneError if passed an unknown zone.

	>>> try:
	...		timezone('Asia/Shangri-La')
	... except UnknownTimeZoneError:
	...		print('Unknown')
	Unknown

	>>> try:
	...		timezone(unicode('\N{TRADE MARK SIGN}'))
	... except UnknownTimeZoneError:
	...		print('Unknown')
	Unknown

	'''
	from .tzfile import build_tzinfo
	from .exceptions import UnknownTimeZoneError
	name = str(name)

	if name.upper() == 'UTC':
		from .utc import UTC
		return UTC()

	if name not in _tzinfo_cache:
		name_parts = name.lstrip('/').split('/')
		for part in name_parts:
			if part == os.path.pardir or os.path.sep in part:
				raise ValueError('Bad path segment: %r' % part)
		try:
			fp = open(os.path.join(infoDir, *name_parts), 'rb')
		except IOError:
			raise UnknownTimeZoneError(name)
		try:
			_tzinfo_cache[name] = build_tzinfo(name, fp)
		finally:
			fp.close()

	return _tzinfo_cache[name]
