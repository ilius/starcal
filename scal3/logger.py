import sys
import logging

from os.path import join
from scal3.path import confDir

confPath = join(confDir, "log.json")

log = None
logLevel = logging.INFO

def init():
	global log, logLevel
	import os
	import warnings
	import json
	from io import StringIO
	from os.path import isdir, isfile
	from scal3.path import sourceDir, APP_NAME
	from scal3.os_utils import makeDir

	if os.path.exists(confDir):
		if not isdir(confDir):
			os.rename(confDir, confDir + "-old")
			os.mkdir(confDir)
	else:
		os.mkdir(confDir)

	envValue = os.getenv("LOG_LEVEL")
	if envValue:
		logLevel = int(envValue)
	elif isfile(confPath):
		with open(confPath) as file:
			logJson = file.read().strip()
			if logJson:
				logData = json.loads(logJson)
				if "logLevel" in logData:
					logLevel = logData["logLevel"]

	makeDir(join(confDir, "log"))

	try:
		import logging.config

		with open(join(sourceDir, "conf", "logging-user.conf")) as fp:
			logConfText = fp.read()
		for varName in ("confDir", "APP_NAME"):
			logConfText = logConfText.replace(varName, eval(varName))

		logging.config.fileConfig(StringIO(logConfText))
		log = logging.getLogger(APP_NAME)
	except Exception as e:
		print(f"failed to setup logger: {e}")
		from scal3.utils import FallbackLogger
		log = FallbackLogger()

	log.setLevel(logLevel)

	# can set env var WARNINGS to: "error", "ignore", "always",
	# "default", "module", "once"
	if os.getenv("WARNINGS"):
		warnings.filterwarnings(os.getenv("WARNINGS"))


def get():
	if log is None:
		init()
	return log


def myRaise(File=None):
	typ, value, tback = sys.exc_info()
	text = f"line {tback.tb_lineno}: {typ.__name__}: {value}\n"
	if File:
		text = f"File \"{File}\", {text}"
	log.error(text)
