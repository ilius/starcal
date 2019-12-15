#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

import sys
import os
import os.path
from os.path import join
from time import time as now
from collections import OrderedDict
from hashlib import sha1
from typing import Tuple

from scal3.path import objectDir, sourceDir

sys.path.insert(0, join(sourceDir, "libs", "bson"))
import bson

from scal3.os_utils import makeDir
from scal3.json_utils import *

dataToJson = dataToPrettyJson
#from scal3.core import dataToJson## FIXME


class FileSystem:
	def open(self, fpath, mode="r", encoding=None):
		raise NotImplementedError

	def listdir(self, dpath: str):
		raise NotImplementedError

	def makeDir(self, dpath: str) -> None:
		raise NotImplementedError

	def removeFile(self, fpath: str) -> None:
		raise NotImplementedError


class DefaultFileSystem(FileSystem):
	def __init__(self, rootPath):
		self._rootPath = rootPath

	def open(self, fpath, mode="r", encoding=None):
		fpath = join(self._rootPath, fpath)
		if mode == "r" and encoding is None:
			encoding = "utf-8"
		return open(fpath, mode=mode, encoding=encoding)

	def listdir(self, dpath):
		return os.listdir(join(self._rootPath, dpath))

	def isfile(self, fpath):
		return os.path.isfile(join(self._rootPath, fpath))

	def isdir(self, dpath):
		return os.path.isdir(join(self._rootPath, dpath))

	def makeDir(self, dpath: str) -> None:
		dpathAbs = join(self._rootPath, dpath)
		if not os.path.isdir(dpathAbs):
			os.makedirs(dpathAbs)

	def removeFile(self, fpath: str) -> None:
		os.remove(join(self._rootPath, fpath))


class SObj:
	@classmethod
	def getSubclass(cls, _type):
		return cls

	params = ()  # used in getData, setData and copyFrom
	canSetDataMultipleTimes = True

	def __nonzero__(self):
		return self.__bool__()

	def __bool__(self):
		raise NotImplementedError

	def copyFrom(self, other):
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

	def copy(self):
		newObj = self.__class__()
		newObj.fs = self.fs
		newObj.copyFrom(self)
		return newObj

	def getData(self):
		return {
			param: getattr(self, param)
			for param in self.params
		}

	def setData(self, data: "Union[Dict, List]", force=False):
		if not force and not self.__class__.canSetDataMultipleTimes:
			if getattr(self, "dataIsSet", False):
				raise RuntimeError(
					"can not run setData multiple times " +
					f"for {self.__class__.__name__} instance"
				)
			self.dataIsSet = True
		###########
		#if isinstance(data, dict):## FIXME
		for key, value in data.items():
			if key in self.params:
				setattr(self, key, value)

	def getIdPath(self):
		try:
			parent = self.parent
		except AttributeError:
			raise NotImplementedError(
				f"{self.__class__.__name__}.getIdPath: no parent attribute"
			)
		try:
			_id = self.id
		except AttributeError:
			raise NotImplementedError(
				f"{self.__class__.__name__}.getIdPath: no id attribute"
			)
		######
		path = []
		if _id is not None:
			path.append(_id)
		if parent is None:
			return path
		else:
			return parent.getIdPath() + path

	def getPath(self):
		parent = self.parent
		if parent is None:
			return []
		index = parent.index(self.id)
		return parent.getPath() + [index]


def makeOrderedData(data: "Union[Dict, List]", params):
	if isinstance(data, dict):
		if params:
			data = list(data.items())

			def paramIndex(key):
				try:
					return params.index(key)
				except ValueError:
					return len(params)

			data.sort(key=lambda x: paramIndex(x[0]))
			data = OrderedDict(data)

	return data


def getSortedDict(data):
	return OrderedDict(sorted(data.items()))


class JsonSObj(SObj):
	canSetDataMultipleTimes = False
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	paramsOrder = ()

	@classmethod
	def getFile(cls, _id=None):
		return cls.file

	@classmethod
	def load(cls, fs: FileSystem, *args):
		fpath = cls.getFile(*args)
		data = {}
		if fs.isfile(fpath):
			try:
				with fs.open(fpath) as fp:
					jsonStr = fp.read()
				data = jsonToData(jsonStr)
			except Exception as e:
				if not cls.skipLoadExceptions:
					raise e
		else:
			if not cls.skipLoadNoFile:
				raise FileNotFoundError(f"{fpath} : file not found")

		# data is the result of json.loads,
		# so probably can be only dict or list (or str)
		_type = data.get("type") if isinstance(data, dict) else None
		if _type is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(_type)
		obj = subCls(*args)
		obj.fs = fs
		obj.setData(data)
		return obj
	#####

	def getDataOrdered(self):
		return makeOrderedData(self.getData(), self.paramsOrder)

	def getJson(self):
		return dataToJson(self.getDataOrdered())

	def setJson(self, jsonStr):
		return self.setData(jsonToData(jsonStr))

	def save(self):
		if self.file:
			jstr = self.getJson()
			with self.fs.open(self.file, "w") as fp:
				fp.write(jstr)
		else:
			log.info(
				f"save method called for object {self!r}" +
				" while file is not set"
			)

	def setData(self, data):
		SObj.setData(self, data)
		self.setModifiedFromFile()

	def setModifiedFromFile(self):
		if hasattr(self, "modified"):
			try:
				self.modified = int(os.stat(self.file).st_mtime)
			except OSError:
				pass
		#else:
		#	log.info(f"no modified param for object {self!r}")


def getObjectPath(_hash: str) -> Tuple[str, str]:
	dpath = join(objectDir, _hash[:2])
	fpath = join(dpath, _hash[2:])
	return dpath, fpath


def iterObjectFiles(fs: FileSystem):
	for dname in fs.listdir(objectDir):
		dpath = join(objectDir, dname)
		if not fs.isdir(dpath):
			continue
		if len(dname) != 2:
			log.error(f"Unexpected directory: {dname}")  # do not skip it!
		for fname in fs.listdir(dpath):
			fpath = join(dpath, fname)
			if not fs.isfile(fpath):
				log.error(f"Object file does not exist or not a file: {fpath}")
				continue
			_hash = dname + fname
			if len(_hash) != 40:
				log.debug(f"Skipping non-object file {fpath}")
				continue
			try:
				int(_hash, 16)
			except ValueError:
				log.debug(f"Skipping non-object file {fpath}  (not hexadecimal)")
				continue
			yield _hash, fpath


def saveBsonObject(data: "Union[Dict, List]", fs: FileSystem):
	data = getSortedDict(data)
	bsonBytes = bytes(bson.dumps(data))
	_hash = sha1(bsonBytes).hexdigest()
	dpath, fpath = getObjectPath(_hash)
	if not fs.isfile(fpath):
		makeDir(dpath)
		with fs.open(fpath, "wb") as fp:
			fp.write(bsonBytes)
	return _hash


def loadBsonObject(_hash, fs: FileSystem):
	dpath, fpath = getObjectPath(_hash)
	with fs.open(fpath, "rb") as fp:
		bsonBytes = fp.read()
	if _hash != sha1(bsonBytes).hexdigest():
		raise IOError(
			f"sha1 diggest does not match for object file '{fpath}'"
		)
	return bson.loads(bsonBytes)


def updateBasicDataFromBson(
	data: "Union[Dict, List]",
	filePath: str,
	fileType: str,
	fs: FileSystem,
):
	"""
		fileType: "event" | "group" | "account"...,
			display only, does not matter much
		return lastHistRecord = (lastEpoch, lastHash)
	"""
	try:
		lastHistRecord = data["history"][0]
		lastEpoch = lastHistRecord[0]
		lastHash = lastHistRecord[1]
	except (KeyError, IndexError):
		raise ValueError(
			f"invalid {fileType} file \"{filePath}\", no \"history\""
		)
	data.update(loadBsonObject(lastHash, fs))
	data["modified"] = lastEpoch ## FIXME
	return (lastEpoch, lastHash)


class BsonHistObj(SObj):
	canSetDataMultipleTimes = False
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	lastHash = None
	# FIXME: basicParams or noHistParams
	basicParams = (
	)

	@classmethod
	def getFile(cls, _id=None):
		return cls.file

	@classmethod
	def load(cls, fs: FileSystem, *args):
		_file = cls.getFile(*args)
		data = {}
		lastEpoch, lastHash = None, None
		try:
			with fs.open(_file) as fp:
				jsonStr = fp.read()
			data = jsonToData(jsonStr)
		except FileNotFoundError:
			if not cls.skipLoadNoFile:
				raise FileNotFoundError(f"{_file} : file not found")
		except Exception as e:
			if not cls.skipLoadExceptions:
				log.error(f"error while opening json file \"{_file}\"")
				raise e
		else:
			lastEpoch, lastHash = updateBasicDataFromBson(data, _file, cls.name, fs)

		# data is the result of json.loads,
		# so probably can be only dict or list (or str)
		_type = data.get("type") if isinstance(data, dict) else None
		if _type is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(_type)
		obj = subCls(*args)
		obj.fs = fs
		obj.setData(data)
		obj.lastHash = lastHash
		obj.modified = lastEpoch
		return obj
	#######

	def getDataOrdered(self):
		return makeOrderedData(self.getData(), self.paramsOrder)

	def loadBasicData(self):
		if not self.fs.isfile(self.file):
			return {}
		with self.fs.open(self.file) as fp:
			jsonStr = fp.read()
		return jsonToData(jsonStr)

	def loadHistory(self):
		lastBasicData = self.loadBasicData()
		history = lastBasicData.get("history")
		if history is None:
			if lastBasicData:
				log.info(f"no \"history\" in json file \"{self.file}\"")
			history = []
		return history

	def saveBasicData(self, basicData):
		jsonStr = dataToJson(basicData)
		with self.fs.open(self.file, "w") as fp:
			fp.write(jsonStr)

	def save(self, *histArgs):
		"""
			returns last history record: (lastEpoch, lastHash, **args)
		"""
		if not self.file:
			raise RuntimeError(
				f"save method called for object {self!r}" +
				" while file is not set"
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
		_hash = saveBsonObject(data, self.fs)
		###
		history = self.loadHistory()
		###
		try:
			lastHash = history[0][1]
		except IndexError:
			lastHash = None
		if _hash != lastHash:## or lastHistArgs != histArgs:## FIXME
			tm = now()
			history.insert(0, [tm, _hash] + list(histArgs))
			self.modified = tm
		basicData["history"] = history
		self.saveBasicData(basicData)
		return history[0]

	def getRevision(self, revHash, *args):
		cls = self.__class__
		data = self.loadBasicData()
		data.update(loadBsonObject(revHash, self.fs))
		try:
			_type = data["type"]
		except (KeyError, TypeError):
			subCls = cls
		else:
			subCls = cls.getSubclass(_type)
		obj = subCls(*args)
		obj.setData(data)
		return obj
