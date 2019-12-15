#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

import os
from os.path import join, split, isfile

from queue import Queue
from threading import Thread

from scal3 import logger
log = logger.get()

from scal3.path import cacheDir
from scal3.os_utils import makeDir
from scal3.ui_gtk import *

pixbufCache = {}
saveQueue = Queue()
saveThread = None


makeDir(cacheDir)


def cacheSaveLoop():
	while True:
		# Queue.get: Remove and return an item from the queue.
		# If queue is empty, wait until an item is available.
		qitem = saveQueue.get()
		if qitem is None:
			return
		fpath, pixbuf = qitem
		pixbuf.savev(
			fpath,  # filename
			"png",  # type
			[],  # optionkeys
			[],  # option_values
		)
		log.debug(f"saved: {fpath}")


def cacheSaveStart():
	global saveThread
	saveThread = Thread(
		target=cacheSaveLoop,
	)
	saveThread.start()


def cacheSaveStop():
	global saveThread
	if saveThread is None:
		return
	saveQueue.put(None)
	# should we wait here until it's stopped?
	saveThread.join()
	saveThread = None


def clear():
	global pixbufCache
	pixbufCache.clear()


def clearFiles():
	for fname in os.listdir(cacheDir):
		if not fname.endswith(".png"):
			continue
		fpath = join(cacheDir, fname)
		if not isfile(fpath):
			continue
		try:
			os.remove(fpath)
		except Exception as e:
			log.exception("")


def getKey(name: str, size: float) -> str:
	return f"{name}_{int(size*10)}"


def getFilePath(key: str) -> str:
	key = key.replace("/", "_")
	key = key.replace(".", "_")
	return join(cacheDir, key + ".png")


def getPixbuf(name: str, size: float) -> "Optional[GdkPixbuf.Pixbuf]":
	key = getKey(name, size)
	pixbuf = pixbufCache.get(key)
	if pixbuf is not None:
		return pixbuf
	fpath = getFilePath(key)
	if isfile(fpath):
		pixbuf = GdkPixbuf.Pixbuf.new_from_file(fpath)
		pixbufCache[key] = pixbuf
		return pixbuf


def setPixbuf(name: str, size: float, pixbuf: "GdkPixbuf.Pixbuf") -> None:
	key = getKey(name, size)
	pixbufCache[key] = pixbuf
	fpath = getFilePath(key)
	saveQueue.put((fpath, pixbuf))
