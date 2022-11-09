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

from scal3 import logger
log = logger.get()

import sys
from time import time as now

from scal3.path import deskDir
from scal3.time_utils import hmEncode, hmDecode
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import numDecode

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	dialog_add_button,
)
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)


class CourseListEditor(gtk.Box):
	def __init__(
		self,
		term,
		defaultCourseName=_("New Course"),
		defaultCourseUnits=3,
		enableScrollbars=False,
	):
		self.term = term ## UniversityTerm obj
		self.defaultCourseName = defaultCourseName
		self.defaultCourseUnits = defaultCourseUnits
		#####
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(True)
		self.treeModel = gtk.ListStore(int, str, int)
		self.treev.set_model(self.treeModel)
		##########
		cell = gtk.CellRendererText(editable=True)
		cell.connect("edited", self.courseNameEdited)
		# cell.connect("editing-started", ....)
		# cell.connect("editing-canceled", ...)
		col = gtk.TreeViewColumn(title=_("Course Name"), cell_renderer=cell, text=1)
		self.treev.append_column(col)
		###
		cell = gtk.CellRendererText(editable=True)
		cell.connect("edited", self.courseUnitsEdited)
		col = gtk.TreeViewColumn(title=_("Units"), cell_renderer=cell, text=2)
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
		toolbar = StaticToolBox(self, vertical=True)
		####
		toolbar.extend([
			ToolBoxItem(
				name="add",
				imageName="list-add.svg",
				onClick="onAddClick",
				desc=_("Add"),
				continuousClick=False,
			),
			ToolBoxItem(
				name="delete",
				imageName="edit-delete.svg",
				onClick="onDeleteClick",
				desc=_("Delete", ctx="button"),
				continuousClick=False,
			),
			ToolBoxItem(
				name="moveUp",
				imageName="go-up.svg",
				onClick="onMoveUpClick",
				desc=_("Move up"),
				continuousClick=False,
			),
			ToolBoxItem(
				name="moveDown",
				imageName="go-down.svg",
				onClick="onMoveDownClick",
				desc=_("Move down"),
				continuousClick=False,
			),
		])
		#######
		pack(self, toolbar)

	def getSelectedIndex(self):
		cur = self.treev.get_cursor()
		try:
			path, col = cur
			index = path[0]
			return index
		except (ValueError, IndexError):
			return None

	def onAddClick(self, button):
		index = self.getSelectedIndex()
		lastCourseId = max(
			[1] + [row[0] for row in self.treeModel]
		)
		row = [
			lastCourseId + 1,
			self.defaultCourseName,
			self.defaultCourseUnits,
		]
		if index is None:
			newIter = self.treeModel.append(row)
		else:
			newIter = self.treeModel.insert(index + 1, row)
		self.treev.set_cursor(self.treeModel.get_path(newIter))
		#col = self.treev.get_column(0)
		#cell = col.get_cell_renderers()[0]
		#cell.start_editing(...) ## FIXME

	def onDeleteClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		del self.treeModel[index]

	def onMoveUpClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.treeModel
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		t.swap(
			t.get_iter(index - 1),
			t.get_iter(index),
		)
		self.treev.set_cursor(index - 1)

	def onMoveDownClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.treeModel
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		t.swap(
			t.get_iter(index),
			t.get_iter(index + 1),
		)
		self.treev.set_cursor(index + 1)

	def courseNameEdited(self, cell, path, newText):
		# log.debug("courseNameEdited", newText)
		index = int(path)
		self.treeModel[index][1] = newText

	def courseUnitsEdited(self, cell, path, newText):
		index = int(path)
		units = numDecode(newText)
		self.treeModel[index][2] = units

	def setData(self, rows):
		self.treeModel.clear()
		for row in rows:
			self.treeModel.append(row)

	def getData(self):
		return [tuple(row) for row in self.treeModel]


class ClassTimeBoundsEditor(gtk.Box):
	def __init__(self, term):
		self.term = term
		#####
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(False)
		self.treeModel = gtk.ListStore(str)
		self.treev.set_model(self.treeModel)
		##########
		cell = gtk.CellRendererText(editable=True)
		cell.connect("edited", self.timeEdited)
		col = gtk.TreeViewColumn(title=_("Time"), cell_renderer=cell, text=0)
		self.treev.append_column(col)
		####
		pack(self, self.treev, 1, 1)
		##########
		toolbar = StaticToolBox(self, vertical=True)
		####
		toolbar.extend([
			ToolBoxItem(
				name="add",
				imageName="list-add.svg",
				onClick="onAddClick",
				desc=_("Add"),
				continuousClick=False,
			),
			ToolBoxItem(
				name="delete",
				imageName="edit-delete.svg",
				onClick="onDeleteClick",
				desc=_("Delete"),
				continuousClick=False,
			),
		])
		#######
		pack(self, toolbar)

	def getSelectedIndex(self):
		cur = self.treev.get_cursor()
		try:
			path, col = cur
			index = path[0]
			return index
		except (ValueError, IndexError):
			return None

	def onAddClick(self, button):
		index = self.getSelectedIndex()
		row = ["00:00"]
		if index is None:
			newIter = self.treeModel.append(row)
		else:
			newIter = self.treeModel.insert(index + 1, row)
		self.treev.set_cursor(self.treeModel.get_path(newIter))

	def onDeleteClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		del self.treeModel[index]

	def onMoveUpClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.treeModel
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		t.swap(
			t.get_iter(index - 1),
			t.get_iter(index),
		)
		self.treev.set_cursor(index - 1)

	def onMoveDownClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.treeModel
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
		parts = newText.split(":")
		h = numDecode(parts[0])
		m = numDecode(parts[1])
		hm = hmEncode((h, m))
		self.treeModel[index][0] = hm
		#self.treeModel.sort()## FIXME

	def setData(self, hmList):
		self.treeModel.clear()
		for hm in hmList:
			self.treeModel.append([hmEncode(hm)])

	def getData(self):
		return sorted(
			hmDecode(row[0])
			for row in self.treeModel
		)


class WidgetClass(NormalWidgetClass):
	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		#####
		totalFrame = gtk.Frame()
		totalFrame.set_label(group.desc)
		totalVbox = VBox()
		###
		expandHbox = HBox()## for courseList and classTimeBounds
		##
		frame = gtk.Frame()
		frame.set_label(_("Course List"))
		self.courseListEditor = CourseListEditor(self.group)
		self.courseListEditor.set_size_request(100, 150)
		frame.add(self.courseListEditor)
		pack(expandHbox, frame, 1, 1)
		##
		frame = gtk.Frame()## FIXME
		frame.set_label(_("Class Time Bounds"))
		self.classTimeBoundsEditor = ClassTimeBoundsEditor(self.group)
		self.classTimeBoundsEditor.set_size_request(50, 150)
		frame.add(self.classTimeBoundsEditor)
		pack(expandHbox, frame)
		expandHbox.show_all()
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
		#self.connect("button-press-event", self.onButtonPress)
		self.connect("draw", self.onExposeEvent)
		#self.connect("event", show_event)

	def onExposeEvent(self, widget=None, event=None):
		win = self.get_window()
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawCairo(cr)
		finally:
			win.end_draw_frame(dctx)

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
		# calculate coordinates: ycenters(list), dy(float)
		ycenters = [
			topMargin + (h - topMargin) * (1 + 2 * i) / 14
			for i in range(7)
		] ## centers y
		dy = (h - topMargin) / 7  # delta y
		# drawing the grid
		# tmfactors includes 0 at the first, and 1 at the end
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
					text = classData.name
					if classData.weekNumMode:
						text += (
							"(<span color=\"#f00\">" +
							_(classData.weekNumMode.capitalize()) +
							"</span>)"
						)
					textList.append(text)
				dx = (w - leftMargin) * (tmfactors[i + 1] - tmfactors[i])
				layout = newTextLayout(
					self,
					"\n".join(textList),
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
		self.set_title(_("View Weekly Schedule"))
		self.connect("delete-event", self.onDeleteEvent)
		#####
		hbox = HBox()
		self.currentWOnlyCheck = gtk.CheckButton(label=_("Current Week Only"))
		self.currentWOnlyCheck.connect("clicked", lambda obj: self.updateWidget())
		pack(hbox, self.currentWOnlyCheck)
		##
		pack(hbox, gtk.Label(), 1, 1)
		##
		button = gtk.Button(label=_("Export to ") + "SVG")
		button.connect("clicked", self.onExportToSvgClick)
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
		import cairo
		aloc = self._widget.get_allocation()
		surface = cairo.SVGSurface(fpath, aloc.width, aloc.height)
		cr = cairo.Context(surface)
		self._widget.drawCairo(cr)
		surface.flush()
		surface.finish()

	def onExportToSvgClick(self, obj=None):
		fcd = gtk.FileChooserDialog(
			transient_for=self,
			action=gtk.FileChooserAction.SAVE,
		)
		fcd.set_current_folder(deskDir)
		fcd.set_current_name(self.term.title + ".svg")
		dialog_add_button(
			fcd,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			fcd,
			imageName="document-save.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
		)
		if fcd.run() == gtk.ResponseType.OK:
			self.exportToSvg(fcd.get_filename())
		fcd.destroy()


def viewWeeklySchedule(group, parentWin=None):
	WeeklyScheduleWindow(group, transient_for=parentWin).show()
