from __future__ import annotations

from scal3 import core, logger

log = logger.get()

import json
import os
import os.path
import sys
from hashlib import sha1
from os.path import join
from time import time as now

from scal3.path import sourceDir

sys.path.insert(0, join(sourceDir, "libs", "bson"))

from typing import TYPE_CHECKING, Protocol

import bson

from scal3.dict_utils import makeOrderedDict
from scal3.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	from typing import Any, Self

	from scal3.filesystem import FileSystem

__all__ = [
	"ParentSObj",
	"SObj",
	"SObjBase",
	"SObjBinaryModel",
	"SObjTextModel",
	"getObjectPath",
	"objectDirName",
]


dataToJson = dataToPrettyJson
# from scal3.core import dataToJson  # FIXME

objectDirName = "objects"


class ParentSObj(Protocol):
	calType: int

	def index(self, ident: int) -> int: ...
	def getIdPath(self) -> list[int]: ...
	def getPath(self) -> list[int]: ...


class SObjBase:
	name = ""
	id: int | None
	fs: FileSystem
	paramsOrder: list[str] = []
	params: list[str] = []  # used in getDict, setDict and copyFrom

	def __init__(self) -> None:
		self.fs = core.fs

	@classmethod
	def getSubclass(cls, typeName: str) -> type:  # noqa: ARG003
		return cls

	def __bool__(self) -> bool:
		raise NotImplementedError

	def copyFrom(self, other: Self) -> None:
		from copy import deepcopy

		for attr in self.params:
			try:
				value = getattr(other, attr)
			except AttributeError:
				continue
			setattr(
				self,
				attr,
				deepcopy(value),
			)


class SObj(SObjBase):
	def __init__(self) -> None:
		self.fs: FileSystem = core.fs
		self.parent: ParentSObj | None = None
		self.id: int | None = None

	def getDict(self) -> dict[str, Any]:
		return {param: getattr(self, param) for param in self.params}

	def setDict(self, data: dict[str, Any]) -> None:
		for key, value in data.items():
			if key in self.params:
				setattr(self, key, value)

	def copy(self) -> Self:
		newObj = self.__class__()
		newObj.fs = self.fs
		newObj.copyFrom(self)
		return newObj

	def getIdPath(self) -> list[int]:
		try:
			parent = self.parent
		except AttributeError:
			raise NotImplementedError(
				f"{self.__class__.__name__}.getIdPath: no parent attribute",
			) from None
		try:
			ident = self.id
		except AttributeError:
			raise NotImplementedError(
				f"{self.__class__.__name__}.getIdPath: no id attribute",
			) from None
		# ------
		path: list[int] = []
		if ident is not None:
			path.append(ident)
		if parent is None:
			return path
		return parent.getIdPath() + path

	def getPath(self) -> list[int]:
		parent = self.parent
		if parent is None:
			return []
		assert self.id is not None
		index = parent.index(self.id)
		return parent.getPath() + [index]


class SObjTextModel(SObj):
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""

	def __init__(self, ident: int | None = None) -> None:
		pass

	@classmethod
	def getFile(cls, ident: int) -> str:  # noqa: ARG003
		return cls.file

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem | None,
	) -> Self | None:
		assert fs is not None
		fpath = cls.getFile(ident)
		data = {}
		if fs.isfile(fpath):
			try:
				with fs.open(fpath) as fp:
					jsonStr = fp.read()
				data = json.loads(jsonStr)
			except Exception:
				if not cls.skipLoadExceptions:
					raise
		elif not cls.skipLoadNoFile:
			raise FileNotFoundError(f"{fpath} : file not found")

		# data is the result of json.loads,
		# so probably can be only dict or list (or str)
		type_ = data.get("type") if isinstance(data, dict) else None
		if type_ is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(type_)
		obj = subCls(ident)
		obj.fs = fs
		obj.setDict(data)
		return obj

	# -----

	def getDictOrdered(self) -> dict[str, Any]:
		return makeOrderedDict(self.getDict(), self.paramsOrder)

	def save(self) -> None:
		if not self.file:
			log.warning(
				f"save method called for object {self!r} while file is not set",
			)
			return

		jstr = dataToJson(self.getDictOrdered())
		with self.fs.open(self.file, "w") as fp:
			fp.write(jstr)

	def setDict(
		self,
		data: dict[str, Any],
	) -> None:
		# if self.dataIsSet:  # FIXME
		# 	return
		SObj.setDict(self, data)
		self.setModifiedFromFile()

	def setModifiedFromFile(self) -> None:
		if hasattr(self, "modified"):
			try:
				self.modified = os.stat(self.file).st_mtime
			except OSError:
				log.exception("")
		# else:
		# 	log.info(f"no modified param for object {self!r}")


def getObjectPath(_hash: str) -> tuple[str, str]:
	dpath = join(objectDirName, _hash[:2])
	fpath = join(dpath, _hash[2:])
	return dpath, fpath


class SObjBinaryModel(SObj):
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	lastHash: str | None = None
	# FIXME: basicParams or noHistParams
	basicParams: list[str] = []

	# def setDict(self, data: dict[str, Any]) -> None:
	# 	if self.dataIsSet:
	# 		return
	# 	SObj.setDict(self, data)

	def __init__(self, ident: int) -> None:
		pass

	@classmethod
	def getFile(cls, ident: int) -> str:  # noqa: ARG003
		return cls.file

	@classmethod
	def load(
		cls,
		ident: int,  # noqa: ANN002
		fs: FileSystem,
	) -> Self | None:
		file = cls.getFile(ident)
		data = {}
		lastEpoch, lastHash = None, None
		try:
			with fs.open(file) as fp:
				jsonStr = fp.read()
			data = json.loads(jsonStr)
		except FileNotFoundError:
			if not cls.skipLoadNoFile:
				raise FileNotFoundError(f"{file} : file not found") from None
		except Exception:
			if not cls.skipLoadExceptions:
				log.error(f'error while opening json file "{file}"')
				raise
		else:
			lastEpoch, lastHash = SObjBinaryModel.updateBasicData(
				data,
				file,
				cls.name,
				fs,
			)

		if lastEpoch is None:
			lastEpoch = now()

		# data is the result of json.loads,
		# so probably can be only dict or list (or str)
		type_ = data.get("type") if isinstance(data, dict) else None
		if type_ is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(type_)
		obj = subCls(ident)
		obj.fs = fs
		obj.setDict(data)
		obj.lastHash = lastHash
		obj.modified = lastEpoch
		return obj

	@classmethod
	def loadBinaryDict(cls, hashStr: str, fs: FileSystem) -> dict[str, Any]:
		_dpath, fpath = getObjectPath(hashStr)
		with fs.open(fpath, "rb") as fp:
			bsonBytes = fp.read()
		if hashStr != sha1(bsonBytes).hexdigest():
			raise OSError(
				f"sha1 diggest does not match for object file '{fpath}'",
			)
		data = bson.loads(bsonBytes)
		assert isinstance(data, dict)
		return data

	@classmethod
	def updateBasicData(
		cls,
		data: dict[str, Any],
		filePath: str,
		fileType: str,
		fs: FileSystem,
	) -> tuple[float, str]:
		"""
		fileType: "event" | "group" | "account"...,
		display only, does not matter much
		return lastHistRecord = (lastEpoch, lastHash).
		"""
		try:
			lastHistRecord = data["history"][0]
			lastEpoch = lastHistRecord[0]
			lastHash = lastHistRecord[1]
		except (KeyError, IndexError):
			raise ValueError(
				f'invalid {fileType} file "{filePath}", no "history"',
			) from None
		data.update(cls.loadBinaryDict(lastHash, fs))
		data["modified"] = lastEpoch  # FIXME
		return (lastEpoch, lastHash)

	# -------

	def getDictOrdered(self) -> dict[str, Any]:
		return makeOrderedDict(self.getDict(), self.paramsOrder)

	def loadBasicData(self) -> dict[str, Any] | list:
		if not self.fs.isfile(self.file):
			return {}
		with self.fs.open(self.file) as fp:
			jsonStr = fp.read()
		return json.loads(jsonStr)

	def loadHistory(self) -> list[tuple[int, str]]:  # (epoch, hashStr)
		lastBasicData = self.loadBasicData()
		assert isinstance(lastBasicData, dict)
		history = lastBasicData.get("history")
		if history is None:
			if lastBasicData:
				log.info(f'no "history" in json file "{self.file}"')
			history = []
		return history

	def saveBasicData(self, basicData: dict[str, Any]) -> None:
		jsonStr = dataToJson(basicData)
		with self.fs.open(self.file, "w") as fp:
			fp.write(jsonStr)

	@classmethod
	def saveData(cls, data: dict[str, Any], fs: FileSystem) -> str:
		data = dict(sorted(data.items()))
		bsonBytes = bytes(bson.dumps(data))
		hash_ = sha1(bsonBytes).hexdigest()
		dpath, fpath = getObjectPath(hash_)
		if not fs.isfile(fpath):
			fs.makeDir(dpath)
			with fs.open(fpath, "wb") as fp:
				fp.write(bsonBytes)
		return hash_

	def save(
		self,
		*histArgs,  # noqa: ANN002  # FIXME?
	) -> tuple[int, str] | None:
		"""Returns last history record: (lastEpoch, lastHash, **args)."""
		if not self.file:
			raise RuntimeError(
				f"save method called for object {self!r} while file is not set",
			)
		if self.fs is None:
			raise RuntimeError(f"{self} has no fs object")
		data = self.getDict()
		basicData: dict[str, Any] = {}
		for param in self.basicParams:
			if param not in data:
				continue
			basicData[param] = data.pop(param)
		if "modified" in data:
			del data["modified"]
		hash_ = self.saveData(data, self.fs)
		# ---
		history = self.loadHistory()
		# ---
		try:
			lastHash = history[0][1]
		except IndexError:
			lastHash = None
		if hash_ != lastHash:  # or lastHistArgs != histArgs:  # FIXME
			tm = now()
			history.insert(0, (tm, hash_) + histArgs)
			self.modified = tm
		basicData["history"] = history
		self.saveBasicData(basicData)
		return history[0]

	def getRevision(self, revHash: str, *args) -> Self:
		cls = self.__class__
		data = self.loadBasicData()
		assert isinstance(data, dict)
		data.update(self.loadBinaryDict(revHash, self.fs))
		try:
			type_ = data["type"]
		except (KeyError, TypeError):
			subCls = cls
		else:
			subCls = cls.getSubclass(type_)
		obj = subCls(*args)
		obj.setDict(data)
		obj.fs = self.fs
		return obj
