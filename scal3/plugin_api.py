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

from scal3 import logger

log = logger.get()

import sys

# modulesDict = {}
# we dont have the module object inside the module itself!!
# how can we register module (with its getList and setList) ?


class PluginError(Exception):
	pass


def getAttr(moduleName, attr, default=None, absolute=False):
	if not absolute:
		moduleName = "scal3." + moduleName
	# module = __import__(moduleName, fromlist=["__plugin_api_get__", attr])
	# log.debug(sorted(sys.modules))
	module = sys.modules[moduleName]
	allowed = getattr(module, "__plugin_api_get__", [])
	if attr not in allowed:
		raise PluginError(
			f"plugin is not allowed to get attribute {attr!r}"
			f" from module {moduleName!r}",
		)
	return getattr(module, attr, default)


def setAttr(moduleName, attr, value, absolute=False):
	if not absolute:
		moduleName = "scal3." + moduleName
	# module = __import__(moduleName, fromlist=["__plugin_api_set__", attr])
	module = sys.modules[moduleName]
	allowed = getattr(module, "__plugin_api_set__", [])
	if attr not in allowed:
		raise PluginError(
			f"plugin is not allowed to set attribute {attr!r} to module {moduleName!r}",
		)
	setattr(module, attr, value)


# def add(moduleName, attr, value):  # FIXME
# 	module = __import__(moduleName)
# 	if not module.get("__plugin_api_add__", False)
