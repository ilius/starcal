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

# no logging in this file

import sys
import os
from os.path import join, split, splitext, dirname, isfile, isdir
from time import time as now
import json

from collections import OrderedDict

import shutil
import re

from typing import Any, Generator

from scal3.path import confDir as newConfDir
from scal3.os_utils import makeDir
from scal3.json_utils import dataToPrettyJson, dataToCompactJson
from scal3.s_object import DefaultFileSystem, saveBsonObject

oldConfDir = newConfDir.replace("starcal3", "starcal2")

oldEventDir = join(oldConfDir, "event")
newEventDir = join(newConfDir, "event")

oldEventEventsDir = join(oldEventDir, "events")
newEventEventsDir = join(newEventDir, "events")

oldGroupsDir = join(oldEventDir, "groups")
newGroupsDir = join(newEventDir, "groups")

oldAccountsDir = join(oldEventDir, "accounts")
newAccountsDir = join(newEventDir, "accounts")

fsNew = DefaultFileSystem(newConfDir)


def loadConf(confPath) -> None:
	if not isfile(confPath):
		return
	try:
		with open(confPath) as fp:
			text = fp.read()
	except Exception as e:
		log.error(f"failed to read file {confPath!r}: {e}")
		return
	#####
	data = OrderedDict()
	exec(text, {}, data)
	return data


def loadCoreConf() -> None:
	confPath = join(oldConfDir, "core.conf")
	#####

	def loadPlugin(fname, **data):
		data["_file"] = fname
		return data

	try:
		with open(confPath) as fp:
			text = fp.read()
	except Exception as e:
		log.error(f"failed to read file {confPath!r}: {e}")
		return
	######
	text = text.replace("calTypes.activeNames", "activeCalTypes")
	text = text.replace("calTypes.inactiveNames", "inactiveCalTypes")
	######
	data = OrderedDict()
	exec(text, {
		"loadPlugin": loadPlugin
	}, data)
	return data


def loadUiCustomizeConf() -> None:
	confPath = join(oldConfDir, "ui-customize.conf")
	#####
	if not isfile(confPath):
		return
	#####
	try:
		with open(confPath) as fp:
			text = fp.read()
	except Exception as e:
		log.error(f"failed to read file {confPath!r}: {e}")
		return
	#####
	text = re.sub(r"^ui\.", "", text, flags=re.M)
	text = re.sub(r"^ud\.", "ud__", text, flags=re.M)
	######
	data = OrderedDict()
	exec(text, {}, data)
	data["wcal_toolbar_mainMenu_icon"] = "starcal.png"
	return data


def writeJsonConf(name: str, data: Any):
	if data is None:
		return
	fname = name + ".json"
	jsonPath = join(newConfDir, fname)
	text = dataToPrettyJson(data, sort_keys=True)
	try:
		open(jsonPath, "w").write(text)
	except Exception as e:
		log.error(f"failed to write file {jsonPath!r}: {e}")


def importEventsIter() -> Generator[int, None, None]:
	makeDir(newEventEventsDir)
	oldFiles = os.listdir(oldEventEventsDir)
	yield len(oldFiles)
	index = 0
	for dname in oldFiles:
		yield index; index += 1
		####
		try:
			_id = int(dname)
		except ValueError:
			continue
		dpath = join(oldEventEventsDir, dname)
		newDpath = join(newEventEventsDir, dname)
		if not isdir(dpath):
			log.info(f"{dpath!r} must be a directory")
			continue
		jsonPath = join(dpath, "event.json")
		if not isfile(jsonPath):
			log.info(f"{jsonPath!r}: not such file")
			continue
		try:
			with open(jsonPath) as fp:
				data = json.loads(fp.read())
		except Exception as e:
			log.error(f"error while loading json file {jsonPath!r}")
			continue
		try:
			tm = data.pop("modified")
		except KeyError:
			tm = now()
		###
		basicData = {}
		#basicData["modified"] = tm
		###
		# remove extra params from data and add to basicData
		for param in (
			"remoteIds",
			"notifiers", # FIXME
		):
			try:
				basicData[param] = data.pop(param)
			except KeyError:
				pass
		###
		_hash = saveBsonObject(data, fsNew)
		basicData["history"] = [(tm, _hash)]
		open(newDpath + ".json", "w").write(
			dataToPrettyJson(basicData, sort_keys=True)
		)


def importGroupsIter() -> Generator[int, None, None]:
	groupsEnableDict = {} ## {groupId -> enable}
	###
	makeDir(newGroupsDir)
	###
	oldFiles = os.listdir(oldGroupsDir)
	yield len(oldFiles) + 1
	index = 0
	###
	for fname in oldFiles:
		yield index; index += 1
		jsonPath = join(oldGroupsDir, fname)
		newJsonPath = join(newGroupsDir, fname)
		if not isfile(jsonPath):
			log.info(f"{jsonPath!r}: not such file")
			continue
		jsonPathNoX, ext = splitext(fname)
		if ext != ".json":
			continue
		try:
			_id = int(jsonPathNoX)
		except ValueError:
			continue
		try:
			with open(jsonPath) as fp:
				data = json.loads(fp.read())
		except Exception as e:
			log.error(f"error while loading json file {jsonPath!r}")
			continue
		####
		groupsEnableDict[_id] = data.pop("enable", True)
		####
		if "history" in data:
			log.info(f"skipping {jsonPath!r}: history already exists")
			continue
		try:
			tm = data.pop("modified")
		except KeyError:
			tm = now()
		###
		basicData = {}
		#basicData["modified"] = tm
		###
		# remove extra params from data and add to basicData
		for param in (
			"remoteIds",
		):
			basicData[param] = data.pop(param, None)
		for param in (
			"enable",
			"idList",
			"remoteSyncData",
			"deletedRemoteEvents",
		):
			try:
				basicData[param] = data.pop(param)
			except KeyError:
				pass
		###
		_hash = saveBsonObject(data, fsNew)
		basicData["history"] = [(tm, _hash)]
		open(newJsonPath, "w").write(dataToPrettyJson(basicData, sort_keys=True))
	####
	yield index; index += 1
	oldGroupListFile = join(oldEventDir, "group_list.json")
	newGroupListFile = join(newEventDir, "group_list.json")
	try:
		with open(oldGroupListFile) as fp:
			groupIds = json.loads(fp.read())
	except Exception as e:
		log.error(f"error while loading {oldGroupListFile!r}: {e}")
	else:
		if isinstance(groupIds, list):
			signedGroupIds = [
				(1 if groupsEnableDict.get(gid, True) else -1) * gid
				for gid in groupIds
			]
			try:
				open(newGroupListFile, "w").write(dataToPrettyJson(signedGroupIds))
			except Exception as e:
				log.error(f"error while writing {newGroupListFile!r}: {e}")
		else:
			log.info(
				f"file {oldGroupListFile!r} contains invalid data" +
				", must contain a list"
			)


def importAccountsIter() -> Generator[int, None, None]:
	makeDir(newAccountsDir)
	###
	oldFiles = os.listdir(oldAccountsDir)
	yield len(oldFiles)
	index = 0
	###
	for fname in oldFiles:
		yield index; index += 1
		jsonPath = join(oldAccountsDir, fname)
		newJsonPath = join(newAccountsDir, fname)
		if not isfile(jsonPath):
			log.info(f"{jsonPath!r}: not such file")
			continue
		jsonPathNoX, ext = splitext(fname)
		if ext != ".json":
			continue
		try:
			_id = int(jsonPathNoX)
		except ValueError:
			continue
		try:
			with open(jsonPath) as fp:
				data = json.loads(fp.read())
		except Exception as e:
			log.error(f"error while loading json file {jsonPath!r}")
			continue
		if "history" in data:
			log.info(f"skipping {jsonPath!r}: history already exists")
			continue
		try:
			tm = data.pop("modified")
		except KeyError:
			tm = now()
		###
		basicData = {}
		#basicData["modified"] = tm
		###
		# remove extra params from data and add to basicData
		for param in (
			"enable",
		):
			try:
				basicData[param] = data.pop(param)
			except KeyError:
				pass
		###
		_hash = saveBsonObject(data, fsNew)
		basicData["history"] = [(tm, _hash)]
		open(newJsonPath, "w").write(
			dataToPrettyJson(basicData, sort_keys=True)
		)


def importTrashIter() -> Generator[int, None, None]:
	yield 1
	yield 0
	jsonPath = join(oldEventDir, "trash.json")
	newJsonPath = join(newEventDir, "trash.json")
	try:
		with open(jsonPath) as fp:
			data = json.loads(fp.read())
	except Exception as e:
		log.info(e)
		return
	if "history" in data:
		log.info(f"skipping {jsonPath!r}: history already exists")
		return
	try:
		tm = data.pop("modified")
	except KeyError:
		tm = now()
	###
	basicData = {}
	#basicData["modified"] = tm
	###
	# remove extra params from data and add to basicData
	for param in (
		"idList",
	):
		try:
			basicData[param] = data.pop(param)
		except KeyError:
			pass
	###
	_hash = saveBsonObject(data, fsNew)
	basicData["history"] = [(tm, _hash)]
	open(newJsonPath, "w").write(dataToPrettyJson(basicData, sort_keys=True))


def importBasicConfigIter() -> Generator[int, None, None]:
	yield 8  # number of steps
	index = 0
	####
	coreData = loadCoreConf()
	coreData["version"] = "3.0.0" ## FIXME
	writeJsonConf("core", coreData)
	yield index; index += 1
	####
	writeJsonConf("ui-customize", loadUiCustomizeConf())
	yield index; index += 1
	# remove adjustTimeCmd from ui-gtk.conf
	for name in (
		"hijri",
		"jalali",
		"locale",
		"ui",
		"ui-gtk",
		"ui-live",
	):
		yield index; index += 1
		confPath = join(oldConfDir, name + ".conf")
		writeJsonConf(name, loadConf(confPath))


def importEventBasicJsonIter() -> Generator[int, None, None]:
	yield 4 ## number of steps
	index = 0
	####
	for name in (
		"account_list",
		"info",
		"last_ids",
	):
		yield index; index += 1
		fname = name + ".json"
		try:
			shutil.copy(
				join(oldEventDir, fname),
				join(newEventDir, fname),
			)
		except Exception as e:
			log.info(e)


def importPluginsIter() -> Generator[int, None, None]:
	oldPlugConfDir = join(oldConfDir, "plugins.conf")
	if isdir(oldPlugConfDir):
		files = os.listdir(oldPlugConfDir)
	else:
		files = []
	########
	yield len(files)
	index = 0
	####
	for plugName in files:
		writeJsonConf(
			plugName,## move it out of plugins.conf FIXME
			loadConf(
				join(oldPlugConfDir, plugName)
			),
		)
		yield index; index += 1


def importConfigIter() -> Generator[int, None, None]:
	makeDir(newConfDir)
	makeDir(newEventDir)
	#########
	funcs = [
		importBasicConfigIter,
		importEventBasicJsonIter,
		importPluginsIter,
		importGroupsIter,
		importGroupsIter,
		importAccountsIter,
		importTrashIter,
		importEventsIter,
	]
	###
	iters = [func() for func in funcs]
	###
	counts = [itr.send(None) for itr in iters]
	totalCount = sum(counts)
	###
	totalRatio = 0.0
	delta = 1.0 / totalCount
	for iterIndex, itr in enumerate(iters):
		iterCount = counts[iterIndex]
		for stepIndex in itr:
			yield totalRatio + stepIndex * delta
		totalRatio += iterCount * delta
		yield totalRatio
	###
	yield 1.0


def getOldVersion() -> str:
	"""
	return version of installed starcal 2.3.x or 2.4.x
	from user"s configuration directory (file ~/.starcal2/core.conf)

	before 2.3.0, version was not stored in configuration directory
	"""
	data = loadCoreConf()
	return data.get("version", "")

##################################


if __name__ == "__main__":
	list(importConfigIter())
