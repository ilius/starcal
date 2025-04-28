from __future__ import annotations

from scal3 import logger

log = logger.get()

import json
import os
import os.path
import sys
from collections import OrderedDict
from hashlib import sha1
from os.path import join
from time import time as now

from scal3.path import sourceDir

sys.path.insert(0, join(sourceDir, "libs", "bson"))

from typing import TYPE_CHECKING

import bson

from scal3.json_utils import dataToPrettyJson

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any, Self

	from scal3.filesystem import FileSystem

__all__ = [
	"SObj",
	"SObjBinaryModel",
	"SObjTextModel",
	"loadBinaryObject",
	"makeOrderedData",
	"objectDirName",
	"saveBinaryObject",
]


dataToJson = dataToPrettyJson
# from scal3.core import dataToJson  # FIXME

objectDirName = "objects"


class SObj:
	@classmethod
	def getSubclass(cls, typeName: str) -> type:  # noqa: ARG003
		return cls

	params = ()  # used in getData, setData and copyFrom
	canSetDataMultipleTimes = True

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

	def copy(self) -> Self:
		newObj = self.__class__()
		newObj.fs = self.fs
		newObj.copyFrom(self)
		return newObj

	def getData(self) -> dict[str, Any]:
		return {param: getattr(self, param) for param in self.params}

	def setData(self, data: dict[str, Any] | list, force: bool = False) -> bool:
		if not force and not self.__class__.canSetDataMultipleTimes:
			if getattr(self, "dataIsSet", False):
				raise RuntimeError(
					"can not run setData multiple times "
					f"for {self.__class__.__name__} instance",
				)
			self.dataIsSet = True
		# -----------
		# if isinstance(data, dict):  # FIXME
		for key, value in data.items():
			if key in self.params:
				setattr(self, key, value)

	def getIdPath(self) -> str:
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
		path = []
		if ident is not None:
			path.append(ident)
		if parent is None:
			return path
		return parent.getIdPath() + path

	def getPath(self) -> list[str]:
		parent = self.parent
		if parent is None:
			return []
		index = parent.index(self.id)
		return parent.getPath() + [index]


def makeOrderedData(
	data: dict[str, Any] | Sequence,
	params: Sequence[str],
) -> dict[str, Any] | list:
	if isinstance(data, dict) and params:
		data = list(data.items())

		def paramIndex(key: str) -> int:
			try:
				return params.index(key)
			except ValueError:
				return len(params)

		data.sort(key=lambda x: paramIndex(x[0]))
		data = OrderedDict(data)

	return data


class SObjTextModel(SObj):
	canSetDataMultipleTimes = False
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	paramsOrder = ()

	@classmethod
	def getFile(cls, ident: int | None = None) -> str:  # noqa: ARG003
		return cls.file

	@classmethod
	def load(
		cls,
		fs: FileSystem,
		*args,  # noqa: ANN002
	) -> Self:
		fpath = cls.getFile(*args)
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
		obj = subCls(*args)
		obj.fs = fs
		obj.setData(data)
		return obj

	# -----

	def getDataOrdered(self) -> dict[str, Any]:
		return makeOrderedData(self.getData(), self.paramsOrder)

	def save(self) -> None:
		if self.file:
			jstr = dataToJson(self.getDataOrdered())
			with self.fs.open(self.file, "w") as fp:
				fp.write(jstr)
		else:
			log.info(
				f"save method called for object {self!r} while file is not set",
			)

	def setData(self, data: dict[str, Any]) -> None:
		SObj.setData(self, data)
		self.setModifiedFromFile()

	def setModifiedFromFile(self) -> None:
		if hasattr(self, "modified"):
			try:
				self.modified = int(os.stat(self.file).st_mtime)
			except OSError:
				log.exception("")
		# else:
		# 	log.info(f"no modified param for object {self!r}")


def getObjectPath(_hash: str) -> tuple[str, str]:
	dpath = join(objectDirName, _hash[:2])
	fpath = join(dpath, _hash[2:])
	return dpath, fpath


def saveBinaryObject(data: dict | list, fs: FileSystem) -> str:
	data = dict(sorted(data.items()))
	bsonBytes = bytes(bson.dumps(data))
	hash_ = sha1(bsonBytes).hexdigest()
	dpath, fpath = getObjectPath(hash_)
	if not fs.isfile(fpath):
		fs.makeDir(dpath)
		with fs.open(fpath, "wb") as fp:
			fp.write(bsonBytes)
	return hash_


def loadBinaryObject(hashStr: str, fs: FileSystem) -> dict | list:
	_dpath, fpath = getObjectPath(hashStr)
	with fs.open(fpath, "rb") as fp:
		bsonBytes = fp.read()
	if hashStr != sha1(bsonBytes).hexdigest():
		raise OSError(
			f"sha1 diggest does not match for object file '{fpath}'",
		)
	return bson.loads(bsonBytes)


class SObjBinaryModel(SObj):
	canSetDataMultipleTimes = False
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	lastHash = None
	# FIXME: basicParams or noHistParams
	basicParams = ()

	@classmethod
	def getFile(cls, ident: int | None = None) -> str:  # noqa: ARG003
		return cls.file

	@classmethod
	def load(
		cls,
		fs: FileSystem,
		*args,  # noqa: ANN002
	) -> Self:
		file = cls.getFile(*args)
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
			lastEpoch = now()  # FIXME

		# data is the result of json.loads,
		# so probably can be only dict or list (or str)
		type_ = data.get("type") if isinstance(data, dict) else None
		if type_ is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(type_)
		obj = subCls(*args)
		obj.fs = fs
		obj.setData(data)
		obj.lastHash = lastHash
		obj.modified = lastEpoch
		return obj

	@classmethod
	def updateBasicData(
		cls,
		data: dict | list,
		filePath: str,
		fileType: str,
		fs: FileSystem,
	) -> tuple[int, str]:
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
		data.update(loadBinaryObject(lastHash, fs))
		data["modified"] = lastEpoch  # FIXME
		return (lastEpoch, lastHash)

	# -------

	def getDataOrdered(self) -> dict[str, Any] | list:
		return makeOrderedData(self.getData(), self.paramsOrder)

	def loadBasicData(self) -> dict[str, Any] | list:
		if not self.fs.isfile(self.file):
			return {}
		with self.fs.open(self.file) as fp:
			jsonStr = fp.read()
		return json.loads(jsonStr)

	def loadHistory(self) -> list[tuple[int, str]]:  # (epoch, hashStr)
		lastBasicData = self.loadBasicData()
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

	def save(
		self,
		*histArgs,  # noqa: ANN002  # FIXME?
	) -> tuple[int, str]:
		"""Returns last history record: (lastEpoch, lastHash, **args)."""
		if not self.file:
			raise RuntimeError(
				f"save method called for object {self!r} while file is not set",
			)
		if self.fs is None:
			raise RuntimeError(f"{self} has no fs object")
		data = self.getData()
		basicData = {}
		for param in self.basicParams:
			if param not in data:
				continue
			basicData[param] = data.pop(param)
		if "modified" in data:
			del data["modified"]
		hash_ = saveBinaryObject(data, self.fs)
		# ---
		history = self.loadHistory()
		# ---
		try:
			lastHash = history[0][1]
		except IndexError:
			lastHash = None
		if hash_ != lastHash:  # or lastHistArgs != histArgs:  # FIXME
			tm = now()
			history.insert(0, [tm, hash_] + list(histArgs))
			self.modified = tm
		basicData["history"] = history
		self.saveBasicData(basicData)
		return history[0]

	def getRevision(
		self,
		revHash: str,
		*args,  # noqa: ANN002
	) -> Self:
		cls = self.__class__
		data = self.loadBasicData()
		data.update(loadBinaryObject(revHash, self.fs))
		try:
			type_ = data["type"]
		except (KeyError, TypeError):
			subCls = cls
		else:
			subCls = cls.getSubclass(type_)
		obj = subCls(*args)
		obj.setData(data)
		obj.fs = self.fs
		return obj
