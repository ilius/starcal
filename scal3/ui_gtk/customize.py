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

from os.path import join, isfile

from scal3.path import confDir
from scal3.utils import myRaise
from scal3.json_utils import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from gi.overrides.GObject import Object

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk import gtk_ud as ud




if 'mainMenu' not in dict(ud.wcalToolbarData['items']):
	ud.wcalToolbarData['items'].insert(0, ('mainMenu', True))


@registerSignals
class DummyCalObj(Object):
	loaded = False
	signals = [
		('config-change', []),
		('date-change', []),
	]
	def __init__(self, name, desc, pkg, customizable):
		Object.__init__(self)
		self.enable = False
		self._name = name
		self.desc = desc
		self.moduleName = '.'.join([pkg, name])
		self.customizable = customizable
		self.optionsWidget = None
		self.items = []
	def getLoadedObj(self):
		try:
			module = __import__(
				self.moduleName,
				fromlist=['CalObj'],
			)
			CalObj = module.CalObj
		except:
			myRaise()
			return
		obj = CalObj()
		obj.enable = self.enable
		return obj
	def updateVars(self):
		pass
	#def getData(self):## FIXME a real problem
	#	return None
	def optionsWidgetCreate(self):
		pass
	def showHide(self):
		pass

class CustomizableCalObj(ud.BaseCalObj):
	customizable = True
	expand = False
	params = ()
	myKeys = ()
	def initVars(self, optionsWidget=None):
		ud.BaseCalObj.initVars(self)
		self.itemWidgets = {} ## for lazy construction of widgets
		self.optionsWidget = optionsWidget
		if self.optionsWidget:
			self.optionsWidget.show_all()
		try:
			self.connect('key-press-event', self.keyPress)## FIXME
		except:
			pass
	getItemsData = lambda self: [(item._name, item.enable) for item in self.items]
	def updateVars(self):
		for item in self.items:
			if item.customizable:
				item.updateVars()
	#def getData(self):## remove? FIXME
	#	data = {}
	#	for mod_attr in self.params:
	#		try:
	#			value = eval(mod_attr)
	#		except:
	#			myRaise()
	#		else:
	#			data[mod_attr] = value
	#	for item in self.items:
	#		if item.customizable:
	#			itemData = item.getData()
	#			if itemData:
	#				data.update(itemData)
	#	return data
	def keyPress(self, arg, gevent):
		kname = gdk.keyval_name(gevent.keyval).lower()
		for item in self.items:
			if item.enable and kname in item.myKeys:
				if item.keyPress(arg, gevent):
					break
	def optionsWidgetCreate(self):
		pass

class CustomizableCalBox(CustomizableCalObj):
	## for GtkBox (HBox and VBox)
	def appendItem(self, item):
		CustomizableCalObj.appendItem(self, item)
		if item.loaded:
			pack(self, item, item.expand, item.expand)
			item.showHide()
	def moveItemUp(self, i):
		if i > 0:
			if self.items[i].loaded and self.items[i-1].loaded:
				self.reorder_child(self.items[i], i-1)
		CustomizableCalObj.moveItemUp(self, i)
	def insertItemWidget(self, i):
		item = self.items[i]
		if not item.loaded:
			return
		pack(self, item, item.expand, item.expand)
		self.reorder_child(item, i)





