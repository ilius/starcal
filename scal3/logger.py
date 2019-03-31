
log = None

def init():
	global log
	import os
	from os.path import join, isdir
	from scal3.path import confDir, rootDir
	from scal3.os_utils import makeDir

	if os.path.exists(confDir):
		if not isdir(confDir):
			os.rename(confDir, confDir + "-old")
			os.mkdir(confDir)
	else:
		os.mkdir(confDir)

	makeDir(join(confDir, "log"))

	try:
		import logging
		import logging.config

		logConfText = open(join(rootDir, "conf", "logging-user.conf")).read()
		for varName in ("confDir", "APP_NAME"):
			logConfText = logConfText.replace(varName, eval(varName))

		logging.config.fileConfig(StringIO(logConfText))
		log = logging.getLogger(APP_NAME)
	except:
		from scal3.utils import FallbackLogger
		log = FallbackLogger()

def get():
	if log is None:
		init()
	return log
