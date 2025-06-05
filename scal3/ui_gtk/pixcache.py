#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

import os
from os.path import isfile, join
from queue import Queue
from threading import Thread

from scal3 import logger

log = logger.get()

from scal3.os_utils import makeDir
from scal3.path import cacheDir
from scal3.ui_gtk import GdkPixbuf

__all__ = [
	"cacheSaveStart",
	"cacheSaveStop",
	"clear",
	"clearFiles",
	"getPixbuf",
	"setPixbuf",
]
pixbufCache: dict[str, GdkPixbuf.Pixbuf] = {}
saveQueue: Queue[tuple[str, GdkPixbuf.Pixbuf] | None] = Queue()
saveThread: Thread | None = None


makeDir(cacheDir)


def cacheSaveLoop() -> None:
	# Queue.get: Remove and return an item from the queue.
	# If queue is empty, wait until an item is available.
	while (qitem := saveQueue.get()) is not None:
		fpath, pixbuf = qitem
		if pixbuf is None:
			log.error(f"cacheSaveLoop: {pixbuf=}, {fpath=}")
			continue
		pixbuf.savev(
			fpath,  # filename
			"png",  # type
			[],  # optionkeys
			[],  # option_values
		)
		log.debug(f"saved: {fpath}")


def cacheSaveStart() -> None:
	global saveThread
	saveThread = Thread(
		target=cacheSaveLoop,
	)
	saveThread.start()


def cacheSaveStop() -> None:
	global saveThread
	if saveThread is None:
		return
	saveQueue.put(None)
	# should we wait here until it's stopped?
	saveThread.join()
	saveThread = None


def clear() -> None:
	pixbufCache.clear()


def clearFiles() -> None:
	for fname in os.listdir(cacheDir):
		if not fname.endswith(".png"):
			continue
		fpath = join(cacheDir, fname)
		if not isfile(fpath):
			continue
		try:
			os.remove(fpath)
		except Exception:
			log.exception("")


def getKey(name: str, size: float) -> str:
	return f"{name}_{int(size * 10)}"


def getFilePath(key: str) -> str:
	key = key.replace("/", "_")
	key = key.replace(".", "_")
	return join(cacheDir, key + ".png")


def getPixbuf(name: str, size: float) -> GdkPixbuf.Pixbuf | None:
	key = getKey(name, size)
	pixbuf = pixbufCache.get(key)
	if pixbuf is not None:
		return pixbuf
	fpath = getFilePath(key)
	if isfile(fpath):
		pixbuf = GdkPixbuf.Pixbuf.new_from_file(fpath)
		assert pixbuf is not None
		pixbufCache[key] = pixbuf
		return pixbuf
	return None


def setPixbuf(name: str, size: float, pixbuf: GdkPixbuf.Pixbuf) -> None:
	key = getKey(name, size)
	pixbufCache[key] = pixbuf
	fpath = getFilePath(key)
	saveQueue.put((fpath, pixbuf))
