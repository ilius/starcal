import os
import re
import natz
from .exceptions import UnknownTimeZoneError
from .tzfile import build_tzinfo

def _tz_from_env(tzenv):
	if tzenv[0] == ':':
		tzenv = tzenv[1:]

	# TZ specifies a file
	if os.path.exists(tzenv):
		with open(tzenv, 'rb') as tzFp:
			return build_tzinfo('local', tzFp)

	# TZ specifies a zoneinfo zone.
	try:
		tz = natz.timezone(tzenv)
		# That worked, so we return this:
		return tz
	except UnknownTimeZoneError:
		raise UnknownTimeZoneError(
			"We don't support non-zoneinfo timezones like %s. \n"
			"Please use a timezone in the form of Continent/City")

def get_localzone(_root='/'):
	"""Tries to find the local timezone configuration.

	This method prefers finding the timezone name and passing that to natz,
	over passing in the localtime file, as in the later case the zoneinfo
	name is unknown.

	The parameter _root makes the function look for files like /etc/localtime
	beneath the _root directory. This is primarily used by the tests.
	In normal usage you call the function without parameters."""

	tzenv = os.environ.get('TZ')
	if tzenv:
		return _tz_from_env(tzenv)

	# Now look for distribution specific configuration files
	# that contain the timezone name.
	tzpath = os.path.join(_root, 'etc/timezone')
	if os.path.exists(tzpath):
		with open(tzpath, 'rb') as tzFp:
			data = tzFp.read()

			# Issue #3 was that /etc/timezone was a zoneinfo file.
			# That's a misconfiguration, but we need to handle it gracefully:
			if data[:5] != 'TZif2':
				etctz = data.strip().decode()
				# Get rid of host definitions and comments:
				if ' ' in etctz:
					etctz, dummy = etctz.split(' ', 1)
				if '#' in etctz:
					etctz, dummy = etctz.split('#', 1)
				return natz.timezone(etctz.replace(' ', '_'))

	# CentOS has a ZONE setting in /etc/sysconfig/clock,
	# OpenSUSE has a TIMEZONE setting in /etc/sysconfig/clock and
	# Gentoo has a TIMEZONE setting in /etc/conf.d/clock
	# We look through these files for a timezone:

	zone_re = re.compile('\s*ZONE\s*=\s*\"')
	timezone_re = re.compile('\s*TIMEZONE\s*=\s*\"')
	end_re = re.compile('\"')

	for filename in ('etc/sysconfig/clock', 'etc/conf.d/clock'):
		tzpath = os.path.join(_root, filename)
		if not os.path.exists(tzpath):
			continue
		with open(tzpath, 'rt') as tzFp:
			data = tzFp.readlines()

		for line in data:
			# Look for the ZONE= setting.
			match = zone_re.match(line)
			if match is None:
				# No ZONE= setting. Look for the TIMEZONE= setting.
				match = timezone_re.match(line)
			if match is not None:
				# Some setting existed
				line = line[match.end():]
				etctz = line[:end_re.search(line).start()]

				# We found a timezone
				return natz.timezone(etctz.replace(' ', '_'))

	# No explicit setting existed. Use localtime
	for filename in ('etc/localtime', 'usr/local/etc/localtime'):
		tzpath = os.path.join(_root, filename)

		if not os.path.exists(tzpath):
			continue
		with open(tzpath, 'rb') as tzFp:
			return build_tzinfo('local', tzFp)

	raise UnknownTimeZoneError('Can not find any timezone configuration')

