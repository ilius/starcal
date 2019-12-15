#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

import os
from os.path import isfile, exists
from time import time as now
from collections import OrderedDict
import atexit


import psutil

from scal3.json_utils import jsonToData, dataToPrettyJson


def get_cmdline(proc):
	# log.debug(psutil.version_info, proc.cmdline)
	if isinstance(proc.cmdline, list):## psutil < 2.0
		return proc.cmdline
	else:## psutil >= 2.0
		return proc.cmdline()


def checkAndSaveJsonLockFile(fpath):
	locked = False
	my_pid = os.getpid()
	if isfile(fpath):
		try:
			with open(fpath) as fp:
				text = fp.read()
		except Exception:
			log.exception("")
			locked = True
		else:
			try:
				data = jsonToData(text)
			except Exception:
				log.info(f"lock file {fpath} is not valid")
			else:
				try:
					pid = data["pid"]
					cmd = data["cmd"]
				except KeyError:
					log.info(f"lock file {fpath} is not valid")
				else:
					try:
						proc = psutil.Process(pid)
					except psutil.NoSuchProcess:
						log.info(f"lock file {fpath}: pid {pid} does not exist")
					else:
						if pid == my_pid:
							log.info(f"lock file {fpath}: pid == my_pid == {pid}")
						elif get_cmdline(proc) != cmd:
							log.info(f"lock file {fpath}: cmd does match: get_cmdline(proc) != cmd")
						else:
							locked = True

	elif exists(fpath):
		# FIXME: what to do?
		pass
	######
	if not locked:
		my_proc = psutil.Process(my_pid)
		my_cmd = get_cmdline(my_proc)
		my_text = dataToPrettyJson(OrderedDict([
			("pid", my_pid),
			("cmd", my_cmd),
			("time", now()),
		]))
		try:
			with open(fpath, "w") as fp:
				fp.write(my_text)
		except Exception as e:
			log.error(f"failed to write lock file {fpath}: {e}")
		else:
			atexit.register(os.remove, fpath)
	######
	return locked
