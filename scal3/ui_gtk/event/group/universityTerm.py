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
from time import time as now

from scal3.path import deskDir
from scal3.time_utils import hmEncode, hmDecode
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import numDecode

from gi.repository import GObject

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import toolButtonFromStock, set_tooltip
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass


class CourseListEditor(gtk.HBox):
	def __init__(
		self,
		term,
		defaultCourseName=_('New Course'),
		defaultCourseUnits=3,
		enableScrollbars=False,
	):
		self.term = term ## UniversityTerm obj
		self.defaultCourseName = defaultCourseName
		self.defaultCourseUnits = defaultCourseUnits
		#####
		gtk.HBox.__init__(self)
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(True)
		self.trees = gtk.ListStore(int, str, int)
		self.treev.set_model(self.trees)
		##########
		cell = gtk.CellRendererText()
		cell.set_property('editable', True)
		cell.connect('edited', self.courseNameEdited)
		# cell.connect('editing-started', ....)
		# cell.connect('editing-canceled', ...)
		col = gtk.TreeViewColumn(_('Course Name'), cell, text=1)
		self.treev.append_column(col)
		###
		cell = gtk.CellRendererText()
		cell.set_property('editable', True)
		cell.connect('edited', self.courseUnitsEdited)
		col = gtk.TreeViewColumn(_('Units'), cell, text=2)
		self.treev.append_column(col)
		####
		if enableScrollbars:## FIXME
			swin = gtk.ScrolledWindow()
			swin.add(self.treev)
			swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
			pack(self, swin, 1, 1)
		else:
			pack(self, self.treev, 1, 1)
		##########
		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.Orientation.VERTICAL)
		#try:## DeprecationWarning #?????????????
		#	#toolbar.set_icon_size(gtk.IconSize.SMALL_TOOLBAR)
		#	# argument to set_icon_size has no effect
		#except:
		#	pass
		size = gtk.IconSize.SMALL_TOOLBAR
		# no different(argument2 to image_new_from_stock has no effect)
		# gtk.IconSize.SMALL_TOOLBAR or gtk.IconSize.MENU
		tb = toolButtonFromStock(gtk.STOCK_ADD, size)
		set_tooltip(tb, _('Add'))
		tb.connect('clicked', self.addClicked)
		toolbar.insert(tb, -1)
		#self.buttonAdd = tb
		####
		tb = toolButtonFromStock(gtk.STOCK_DELETE, size)
		set_tooltip(tb, _('Delete'))
		tb.connect('clicked', self.deleteClicked)
		toolbar.insert(tb, -1)
		#self.buttonDel = tb
		####
		tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
		set_tooltip(tb, _('Move up'))
		tb.connect('clicked', self.moveUpClicked)
		toolbar.insert(tb, -1)
		####
		tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
		set_tooltip(tb, _('Move down'))
		tb.connect('clicked', self.moveDownClicked)
		toolbar.insert(tb, -1)
		#######
		pack(self, toolbar)

	def getSelectedIndex(self):
		cur = self.treev.get_cursor()
		try:
			path, col = cur
			index = path[0]
			return index
		except:
			return None

	def addClicked(self, button):
		index = self.getSelectedIndex()
		lastCourseId = max(
			[1] + [row[0] for row in self.trees]
		)
		row = [
			lastCourseId + 1,
			self.defaultCourseName,
			self.defaultCourseUnits,
		]
		if index is None:
			newIter = self.trees.append(row)
		else:
			newIter = self.trees.insert(index + 1, row)
		self.treev.set_cursor(self.trees.get_path(newIter))
		#col = self.treev.get_column(0)
		#cell = col.get_cell_renderers()[0]
		#cell.start_editing(...) ## FIXME

	def deleteClicked(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		del self.trees[index]

	def moveUpClicked(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.trees
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		t.swap(
			t.get_iter(index - 1),
			t.get_iter(index),
		)
		self.treev.set_cursor(index - 1)

	def moveDownClicked(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.trees
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		t.swap(
			t.get_iter(index),
			t.get_iter(index + 1),
		)
		self.treev.set_cursor(index + 1)

	def courseNameEdited(self, cell, path, newText):
		#print('courseNameEdited', newText)
		index = int(path)
		self.trees[index][1] = newText

	def courseUnitsEdited(self, cell, path, newText):
		index = int(path)
		units = numDecode(newText)
		self.trees[index][2] = units

	def setData(self, rows):
		self.trees.clear()
		for row in rows:
			self.trees.append(row)

	def getData(self):
		return [tuple(row) for row in self.trees]


class ClassTimeBoundsEditor(gtk.HBox):
	def __init__(self, term):
		self.term = term
		#####
		gtk.HBox.__init__(self)
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(False)
		self.trees = gtk.ListStore(str)
		self.treev.set_model(self.trees)
		##########
		cell = gtk.CellRendererText()
		cell.set_property('editable', True)
		cell.connect('edited', self.timeEdited)
		col = gtk.TreeViewColumn(_('Time'), cell, text=0)
		self.treev.append_column(col)
		####
		pack(self, self.treev, 1, 1)
		##########
		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.Orientation.VERTICAL)
		#try:## DeprecationWarning #?????????????
		#	#toolbar.set_icon_size(gtk.IconSize.SMALL_TOOLBAR)
		#	# no different (argument to set_icon_size has no effect) ?????????
		#except:
		#	pass
		size = gtk.IconSize.SMALL_TOOLBAR
		##no different(argument2 to image_new_from_stock has no effect) ?????????
		#### gtk.IconSize.SMALL_TOOLBAR or gtk.IconSize.MENU
		tb = toolButtonFromStock(gtk.STOCK_ADD, size)
		set_tooltip(tb, _('Add'))
		tb.connect('clicked', self.addClicked)
		toolbar.insert(tb, -1)
		#self.buttonAdd = tb
		####
		tb = toolButtonFromStock(gtk.STOCK_DELETE, size)
		set_tooltip(tb, _('Delete'))
		tb.connect('clicked', self.deleteClicked)
		toolbar.insert(tb, -1)
		#self.buttonDel = tb
		#######
		pack(self, toolbar)

	def getSelectedIndex(self):
		cur = self.treev.get_cursor()
		try:
			path, col = cur
			index = path[0]
			return index
		except:
			return None

	def addClicked(self, button):
		index = self.getSelectedIndex()
		row = ['00:00']
		if index is None:
			newIter = self.trees.append(row)
		else:
			newIter = self.trees.insert(index + 1, row)
		self.treev.set_cursor(self.trees.get_path(newIter))

	def deleteClicked(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		del self.trees[index]

	def moveUpClicked(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.trees
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		t.swap(
			t.get_iter(index - 1),
			t.get_iter(index),
		)
		self.treev.set_cursor(index - 1)

	def moveDownClicked(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.trees
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		t.swap(
			t.get_iter(index),
			t.get_iter(index + 1),
		)
		self.treev.set_cursor(index + 1)

	def timeEdited(self, cell, path, newText):
		index = int(path)
		parts = newText.split(':')
		h = numDecode(parts[0])
		m = numDecode(parts[1])
		hm = hmEncode((h, m))
		self.trees[index][0] = hm
		#self.trees.sort()## FIXME

	def setData(self, hmList):
		self.trees.clear()
		for hm in hmList:
			self.trees.append([hmEncode(hm)])

	def getData(self):
		return sorted(
			hmDecode(row[0])
			for row in self.trees
		)


class WidgetClass(NormalWidgetClass):
	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		#####
		totalFrame = gtk.Frame()
		totalFrame.set_label(group.desc)
		totalVbox = gtk.VBox()
		###
		expandHbox = gtk.HBox()## for courseList and classTimeBounds
		##
		frame = gtk.Frame()
		frame.set_label(_('Course List'))
		self.courseListEditor = CourseListEditor(self.group)
		self.courseListEditor.set_size_request(100, 150)
		frame.add(self.courseListEditor)
		pack(expandHbox, frame, 1, 1)
		##
		frame = gtk.Frame()## FIXME
		frame.set_label(_('Class Time Bounds'))
		self.classTimeBoundsEditor = ClassTimeBoundsEditor(self.group)
		self.classTimeBoundsEditor.set_size_request(50, 150)
		frame.add(self.classTimeBoundsEditor)
		pack(expandHbox, frame)
		##
		pack(totalVbox, expandHbox, 1, 1)
		#####
		totalFrame.add(totalVbox)
		pack(self, totalFrame, 1, 1)## expand? FIXME

	def updateWidget(self):  # FIXME
		NormalWidgetClass.updateWidget(self)
		self.courseListEditor.setData(self.group.courses)
		self.classTimeBoundsEditor.setData(self.group.classTimeBounds)

	def updateVars(self):
		NormalWidgetClass.updateVars(self)
		##
		self.group.setCourses(self.courseListEditor.getData())
		self.group.classTimeBounds = self.classTimeBoundsEditor.getData()


@registerType
class WeeklyScheduleWidget(gtk.DrawingArea):
	def __init__(self, term):
		self.term = term
		self.data = []
		####
		gtk.DrawingArea.__init__(self)
		#self.connect('button-press-event', self.buttonPress)
		self.connect('draw', self.onExposeEvent)
		#self.connect('event', show_event)

	def onExposeEvent(self, widget=None, event=None):
		self.drawCairo(self.get_window().cairo_create())

	def drawCairo(self, cr):
		if not self.data:
			return
		t0 = now()
		w = self.get_allocation().width
		h = self.get_allocation().height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, ui.bgColor)
		textColor = ui.textColor
		gridColor = ui.mcalGridColor ## FIXME
		###
		#classBounds = self.term.classTimeBounds
		titles, tmfactors = self.term.getClassBoundsFormatted()
		###
		weekDayLayouts = []
		weekDayLayoutsWidth = []
		for j in range(7):
			layout = newTextLayout(self, core.getWeekDayN(j))
			layoutW, layoutH = layout.get_pixel_size()
			weekDayLayouts.append(layout)
			weekDayLayoutsWidth.append(layoutW)
		leftMargin = max(weekDayLayoutsWidth) + 6
		###
		topMargin = 20 ## FIXME
		### Calc Coordinates: ycenters(list), dy(float)
		ycenters = [
			topMargin + (h - topMargin) * (1 + 2 * i) / 14
			for i in range(7)
		] ## centers y
		dy = (h - topMargin) / 7  # delta y
		### Draw grid
		## tmfactors includes 0 at the first, and 1 at the end
		setColor(cr, gridColor)
		##
		for i in range(7):
			cr.rectangle(
				0,
				ycenters[i] - dy / 2,
				w,
				1,
			)
			cr.fill()
		##
		for factor in tmfactors[:-1]:
			x = leftMargin + factor * (w - leftMargin)
			if rtl:
				x = w - x
			cr.rectangle(x, 0, 1, h)
			cr.fill()
		###
		setColor(cr, textColor)
		for i, title in enumerate(titles):
			layout = newTextLayout(self, title)
			layoutW, layoutH = layout.get_pixel_size()
			##
			dx = (w - leftMargin) * (tmfactors[i + 1] - tmfactors[i])
			if dx < layoutW:
				continue
			##
			factor = (tmfactors[i] + tmfactors[i + 1]) / 2
			x = factor * (w - leftMargin) + leftMargin
			if rtl:
				x = w - x
			x -= layoutW / 2
			##
			y = (topMargin - layoutH) / 2 - 1
			##
			cr.move_to(x, y)
			show_layout(cr, layout)
		###
		for j in range(7):
			layout = weekDayLayouts[j]
			layoutW, layoutH = layout.get_pixel_size()
			x = leftMargin / 2
			if rtl:
				x = w - x
			x -= layoutW / 2
			##
			y = topMargin + (h - topMargin) * (j + 0.5) / 7 - layoutH / 2
			##
			cr.move_to(x, y)
			show_layout(cr, layout)
		for j in range(7):
			wd = (j + core.firstWeekDay) % 7
			for i, dayData in enumerate(self.data[wd]):
				textList = []
				for classData in dayData:
					text = classData['name']
					if classData['weekNumMode']:
						text += (
							'(<span color="#f00">' +
							_(classData['weekNumMode'].capitalize()) +
							'</span>)'
						)
					textList.append(text)
				dx = (w - leftMargin) * (tmfactors[i + 1] - tmfactors[i])
				layout = newTextLayout(
					self,
					'\n'.join(textList),
					maxSize=(dx, dy),
				)
				layoutW, layoutH = layout.get_pixel_size()
				##
				factor = (tmfactors[i] + tmfactors[i + 1]) / 2
				x = factor * (w - leftMargin) + leftMargin
				if rtl:
					x = w - x
				x -= layoutW / 2
				##
				y = topMargin + (h - topMargin) * (j + 0.5) / 7 - layoutH / 2
				##
				cr.move_to(x, y)
				show_layout(cr, layout)


class WeeklyScheduleWindow(gtk.Dialog):
	def __init__(self, term, **kwargs):
		self.term = term
		gtk.Dialog.__init__(self, **kwargs)
		self.resize(800, 500)
		self.set_title(_('View Weekly Schedule'))
		self.connect('delete-event', self.onDeleteEvent)
		#####
		hbox = gtk.HBox()
		self.currentWOnlyCheck = gtk.CheckButton(_('Current Week Only'))
		self.currentWOnlyCheck.connect('clicked', lambda obj: self.updateWidget())
		pack(hbox, self.currentWOnlyCheck)
		##
		pack(hbox, gtk.Label(''), 1, 1)
		##
		button = gtk.Button(_('Export to ') + 'SVG')
		button.connect('clicked', self.exportToSvgClicked)
		pack(hbox, button)
		##
		pack(self.vbox, hbox)
		#####
		self._widget = WeeklyScheduleWidget(term)
		pack(self.vbox, self._widget, 1, 1)
		#####
		self.vbox.show_all()
		self.updateWidget()

	def onDeleteEvent(self, win, gevent):
		self.destroy()
		return True

	def updateWidget(self):
		self._widget.data = self.term.getWeeklyScheduleData(
			self.currentWOnlyCheck.get_active()
		)
		self._widget.queue_draw()

	def exportToSvg(self, fpath):
		x, y, w, h = self._widget.get_allocation()
		fo = open(fpath, 'w')
		surface = cairo.SVGSurface(fo, w, h)
		cr0 = cairo.Context(surface)
		cr = gdk.CairoContext(cr0)
		#surface.set_device_offset(0, 0)
		self._widget.drawCairo(cr)
		surface.finish()

	def exportToSvgClicked(self, obj=None):
		fcd = gtk.FileChooserDialog(parent=self, action=gtk.FileChooserAction.SAVE)
		fcd.set_current_folder(deskDir)
		fcd.set_current_name(self.term.title + '.svg')
		canB = fcd.add_button(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL)
		saveB = fcd.add_button(gtk.STOCK_SAVE, gtk.ResponseType.OK)
		if ui.autoLocale:
			canB.set_label(_('_Cancel'))
			canB.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_CANCEL,
				gtk.IconSize.BUTTON,
			))
			saveB.set_label(_('_Save'))
			saveB.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_SAVE,
				gtk.IconSize.BUTTON,
			))
		if fcd.run() == gtk.ResponseType.OK:
			self.exportToSvg(fcd.get_filename())
		fcd.destroy()


def viewWeeklySchedule(group):
	WeeklyScheduleWindow(group, parent=ui.prefDialog).show()
