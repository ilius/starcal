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

import sys

#modulesDict = {}
## we dont have the module object inside the module itself!!
## how can we register module (with its getList and setList) ?

class PluginError(Exception):
	pass

def get(moduleName, attr, default=None, absolute=False):
	if not absolute:
		moduleName = 'scal3.' + moduleName
	#module = __import__(moduleName, fromlist=['__plugin_api_get__', attr])
	#print(sorted(sys.modules.keys()))
	module = sys.modules[moduleName]
	allowed = getattr(module, '__plugin_api_get__', [])
	if not attr in allowed:
		raise PluginError('plugin is not allowed to get attribute %s from module %s'%(attr, moduleName))
	return getattr(module, attr, default)

def set(moduleName, attr, value, absolute=False):
	if not absolute:
		moduleName = 'scal3.' + moduleName
	#module = __import__(moduleName, fromlist=['__plugin_api_set__', attr])
	module = sys.modules[moduleName]
	allowed = getattr(module, '__plugin_api_set__', [])
	if not attr in allowed:
		raise PluginError('plugin is not allowed to set attribute %s to module %s'%(attr, moduleName))
	setattr(module, attr, value)

#def add(moduleName, attr, value):## FIXME
#	module = __import__(moduleName)
#	if not module.get('__plugin_api_add__', False)


