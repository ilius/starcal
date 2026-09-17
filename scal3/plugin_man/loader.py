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

import json
from os.path import isfile, split, splitext
from time import localtime
from typing import TYPE_CHECKING, Any

from scal3.plugin_man.base import (
	BaseJsonPlugin,
	BasePlugin,
	DummyExternalPlugin,
	getPlugPath,
	log,
	pluginClassByName,
	pluginsTitleByName,
)
from scal3.plugin_man.ics import IcsTextPlugin

if TYPE_CHECKING:
	from scal3.pytypes import PluginType

__all__ = ["loadPlugin"]


def loadExternalPlugin(
	file: str,
	**data: object,
) -> PluginType | None:
	file = getPlugPath(file)
	fname = split(file)[-1]
	if not isfile(file):
		log.error(f'plugin file "{file}" not found! maybe removed?')
		# try:
		# 	plugIndex.remove(
		return None  # FIXME
		# plug = BaseJsonPlugin(
		# 	_file,
		# 	calType=0,
		# 	title="Failed to load plugin",
		# 	enable=enable,
		# 	show_date=show_date,
		# )
		# plug.external = True
		# return plug
	# ---
	name = splitext(fname)[0]
	# ---
	if not data.get("enable"):
		return DummyExternalPlugin(
			file,
			pluginsTitleByName.get(name, name),
		)
	# ---
	mainFile: str = data.get("mainFile")  # type: ignore[assignment]
	if not mainFile:
		log.error(f'invalid external plugin "{file}"')
		return None
	# ---
	mainFile = getPlugPath(mainFile)
	# ---
	pyEnv = {
		"__file__": mainFile,
		"BasePlugin": BasePlugin,
		"BaseJsonPlugin": BaseJsonPlugin,
	}
	try:
		with open(mainFile, encoding="utf-8") as fp:
			exec(fp.read(), pyEnv)
	except Exception:
		log.error(f'error while loading external plugin "{file}"')
		log.exception("")
		return None
	# ---
	cls: type[PluginType] | None = pyEnv.get("TextPlugin")  # type: ignore[assignment]
	if cls is None:
		log.error(f'invalid external plugin "{file}", no TextPlugin class')
		return None
	# ---
	try:
		plugin = cls(file)
	except Exception:
		log.error(f'error while loading external plugin "{file}"')
		log.exception("")
		return None

	# sys.path.insert(0, direc)
	# try:
	# 	mod = ...
	# except:
	# 	log.exception("")
	# 	return None
	# finally:
	# 	sys.path.pop(0)
	# mod.module_init(sourceDir, )  # FIXME
	# try:
	# 	plugin = mod.TextPlugin(_file)
	# except:
	# 	log.exception("")
	# 	# log.debug(dir(mod))
	# 	return
	plugin.external = True
	plugin.setDict(data)
	plugin.onCurrentDateChange(localtime()[:3])
	return plugin


# must not rename _file argument
def loadPlugin(_file: str | None = None, **kwargs: Any) -> PluginType | None:
	if not _file:
		log.error(f"plugin file is empty! {kwargs=}")
		return None
	file = getPlugPath(_file)
	if not isfile(file):
		log.error(f'error while loading plugin "{file}": no such file!\n')
		return None
	ext = splitext(file)[1].lower()
	# ----
	# FIXME: should ics plugins require a json file too?
	if ext == ".ics":
		return IcsTextPlugin(file, **kwargs)
	# ----
	if ext == ".md":
		return None
	if ext != ".json":
		log.error(
			f"unsupported plugin extension {ext}, new style plugins have a json file",
		)
		return None
	try:
		with open(file, encoding="utf-8") as fp:
			text = fp.read()
	except Exception as e:
		log.error(
			f'error while reading plugin file "{file}": {e}',
		)
		return None
	try:
		data = json.loads(text)
	except Exception:
		log.error(f'invalid json file "{file}"')
		log.exception("")
		return None
	# ----
	data.update(kwargs)  # FIXME
	# ----
	name = data.get("type")
	if not name:
		log.error(f'invalid plugin "{file}", no "type" key')
		return None
	# ----
	if name == "external":
		return loadExternalPlugin(file, **data)
	# ----
	try:
		cls = pluginClassByName[name]
	except KeyError:
		log.error(f'invald plugin type "{name}" in file "{file}"')
		return None
	# ----
	for param in cls.essentialParams:
		if not data.get(param):
			log.error(
				f'invalid plugin "{file}": param "{param}" is missing',
			)
			return None
	# ----
	plug = cls(file)
	plug.setDict(data)
	# ----
	return plug
