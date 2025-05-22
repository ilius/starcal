from __future__ import annotations

from scal3 import logger

log = logger.get()

import os
import os.path
from os.path import isabs, join
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from io import IOBase

__all__ = ["DefaultFileSystem", "FileSystem"]


class FileSystem:
	def open(
		self,
		fpath: str,
		mode: str = "r",
		encoding: str | None = None,
	) -> IOBase:
		raise NotImplementedError

	def abspath(self, path: str) -> str:
		raise NotImplementedError

	def isdir(self, path: str) -> bool:
		raise NotImplementedError

	def listdir(self, dpath: str) -> list[str]:
		raise NotImplementedError

	def makeDir(self, dpath: str) -> None:
		raise NotImplementedError

	def removeFile(self, fpath: str) -> None:
		raise NotImplementedError


class DefaultFileSystem(FileSystem):
	def __init__(self, rootPath: str) -> None:
		self._rootPath = rootPath

	def abspath(self, path: str) -> str:
		if isabs(path):
			return path
		return join(self._rootPath, path)

	def isdir(self, path: str) -> bool:
		if isabs(path):
			log.warning(f"DefaultFileSystem: isdir: reading abs path {path}")
		return os.path.isdir(self.abspath(path))

	def open(
		self,
		fpath: str,
		mode: str = "r",
		encoding: str | None = None,
	) -> IOBase:
		if isabs(fpath):
			log.warning(f"DefaultFileSystem: open: reading abs path {fpath}")
		fpath = self.abspath(fpath)
		if mode == "r" and encoding is None:
			encoding = "utf-8"
		return open(fpath, mode=mode, encoding=encoding)  # noqa: SIM115

	def listdir(self, dpath: str) -> list[str]:
		if isabs(dpath):
			log.warning(f"DefaultFileSystem: listdir: reading abs path {dpath}")
		return os.listdir(self.abspath(dpath))

	def isfile(self, fpath: str) -> bool:
		if isabs(fpath):
			log.warning(f"DefaultFileSystem: isfile: reading abs path {fpath}")
		return os.path.isfile(self.abspath(fpath))

	def makeDir(self, dpath: str) -> None:
		if isabs(dpath):
			log.warning(f"DefaultFileSystem: makeDir: reading abs path {dpath}")
		dpathAbs = self.abspath(dpath)
		if not os.path.isdir(dpathAbs):
			os.makedirs(dpathAbs)

	def removeFile(self, fpath: str) -> None:
		if isabs(fpath):
			log.warning(f"DefaultFileSystem: removeFile: reading abs path {fpath}")
		os.remove(self.abspath(fpath))
