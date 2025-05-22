from __future__ import annotations

import logging
import sys
from os.path import join
from typing import Protocol

from scal3.path import confDir
from scal3.property import Property

__all__ = ["get", "logLevel"]


confPath = join(confDir, "log.json")


class LoggerType(Protocol):
	# def __init__(self) -> None: ...
	def info(self, text: str) -> None: ...
	def error(self, text: str) -> None: ...
	def warning(self, text: str) -> None: ...
	def debug(self, text: str) -> None: ...
	def exception(self, prefix: str) -> None: ...
	def setLevel(self, level: int) -> None: ...


class FallbackLogger:
	def __init__(self) -> None:
		pass

	def info(self, text: str) -> None:  # noqa: PLR6301
		print(text)

	def error(self, text: str) -> None:  # noqa: PLR6301
		sys.stderr.write("ERROR: " + text + "\n")

	def warning(self, text: str) -> None:  # noqa: PLR6301
		print("WARNING: " + text)

	def debug(self, text: str) -> None:  # noqa: PLR6301
		print(text)

	def exception(self, prefix: str) -> None:  # noqa: PLR6301
		typ, value, tback = sys.exc_info()
		assert tback
		assert typ
		text = f"line {tback.tb_lineno}: {typ.__name__}: {value}\n"
		self.error(prefix + "\n" + text)

	def setLevel(self, level: int) -> None:
		pass


log: LoggerType = FallbackLogger()
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

	log.setLevel(logLevel.v)

	# can set env var WARNINGS to: "error", "ignore", "always",
	# "default", "module", "once"
	warningsEnv = os.getenv("WARNINGS")
	if warningsEnv:
		warnings.filterwarnings(warningsEnv)  # type: ignore[arg-type]


def get() -> LoggerType:
	if log is None:
		init()
	return log  # type: ignore[return-value]
