from __future__ import annotations

from scal3 import logger

log = logger.get()

import atexit
import json
import os
from collections import OrderedDict
from os.path import exists, isfile
from time import time as now
from typing import TYPE_CHECKING

import psutil

from scal3.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	from psutil import Process

__all__ = ["checkAndSaveJsonLockFile"]


def get_cmdline(proc: Process) -> list[str]:
	# log.debug(psutil.version_info, proc.cmdline)
	if isinstance(proc.cmdline, list):  # psutil < 2.0
		return proc.cmdline
	# psutil >= 2.0
	return proc.cmdline()


def checkAndSaveJsonLockFile(fpath: str) -> bool:
	locked = False
	my_pid = os.getpid()
	if isfile(fpath):
		try:
			with open(fpath, encoding="utf-8") as fp:
				text = fp.read()
		except Exception:
			log.exception("")
			locked = True
		else:
			try:
				data = json.loads(text)
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
							log.info(
								f"lock file {fpath}: cmd does match: "
								"get_cmdline(proc) != cmd",
							)
						else:
							locked = True

	elif exists(fpath):
		# FIXME: what to do?
		pass
	# ------
	if not locked:
		my_proc = psutil.Process(my_pid)
		my_cmd = get_cmdline(my_proc)
		my_text = dataToPrettyJson(
			OrderedDict(
				[
					("pid", my_pid),
					("cmd", my_cmd),
					("time", now()),
				],
			),
		)
		try:
			with open(fpath, "w", encoding="utf-8") as fp:
				fp.write(my_text)
		except Exception as e:
			log.error(f"failed to write lock file {fpath}: {e}")
		else:
			atexit.register(os.remove, fpath)
	# ------
	return locked
