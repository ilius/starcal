from __future__ import annotations

import logging
from os.path import join

from scal3.path import confDir
from scal3.property import Property

__all__ = ["get", "logLevel"]


confPath = join(confDir, "log.json")

log = None
logLevel = Property(logging.INFO)


def init() -> None:
	global log
	import json
	import os
	import warnings
	from io import StringIO
	from os.path import isdir, isfile

	from scal3.os_utils import makeDir
	from scal3.path import APP_NAME, sourceDir

	if os.path.exists(confDir):
		if not isdir(confDir):
			os.rename(confDir, confDir + "-old")
			os.mkdir(confDir)
	else:
		os.mkdir(confDir)

	envValue = os.getenv("LOG_LEVEL")
	if envValue:
		logLevel.v = int(envValue)
	elif isfile(confPath):
		with open(confPath, encoding="utf-8") as file:
			logJson = file.read().strip()
			if logJson:
				logData = json.loads(logJson)
				if "logLevel" in logData:
					logLevel.v = logData["logLevel"]

	makeDir(join(confDir, "log"))

	try:
		import logging.config

		with open(join(sourceDir, "conf", "logging-user.conf"), encoding="utf-8") as fp:
			logConfText = fp.read()

		# TODO: use str.format()
		logConfText = logConfText.replace("confDir", confDir)
		logConfText = logConfText.replace("APP_NAME", APP_NAME)

		logging.config.fileConfig(StringIO(logConfText))
		log = logging.getLogger(APP_NAME)
	except Exception as e:
		print(f"failed to setup logger: {e}")  # noqa: T201
		from scal3.utils import FallbackLogger

		log = FallbackLogger()

	log.setLevel(logLevel.v)

	# can set env var WARNINGS to: "error", "ignore", "always",
	# "default", "module", "once"
	if os.getenv("WARNINGS"):
		warnings.filterwarnings(os.getenv("WARNINGS"))


def get() -> logging.Logger:
	if log is None:
		init()
	return log
