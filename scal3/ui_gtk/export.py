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

import os, sys

from scal3.cal_types import calTypes
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3 import ui
from scal3.monthcal import getMonthStatus, getCurrentMonthStatus
from scal3.export import exportToHtml

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import openWindow, dialog_add_button
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton
from scal3.ui_gtk.mywidgets.multi_spin.year_month import YearMonthButton
from scal3.ui_gtk.mywidgets.dialog import MyDialog


#gdkColorToHtml = lambda color: '#%.2x%.2x%.2x'%(color.red/256, color.green/256, color.blue/256)



class ExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Export to %s')%'HTML')
		## parent=None FIXME
		#self.set_has_separator(False)
		########
		hbox = gtk.HBox(spacing=2)
		pack(hbox, gtk.Label(_('Month Range')))
		combo = gtk.ComboBoxText()
		for t in ('Current Month', 'Whole Current Year', 'Custom'):
			combo.append_text(_(t))
		pack(hbox, combo)
		pack(hbox, gtk.Label(''), 1, 1)
		self.combo = combo
		###
		hbox2 = gtk.HBox(spacing=2)
		pack(hbox2, gtk.Label(_('from month')))
		self.ymBox0 = YearMonthButton()
		pack(hbox2, self.ymBox0)
		pack(hbox2, gtk.Label(''), 1, 1)
		pack(hbox2, gtk.Label(_('to month')))
		self.ymBox1 = YearMonthButton()
		pack(hbox2, self.ymBox1)
		pack(hbox, hbox2, 1, 1)
		self.hbox2 = hbox2
		combo.set_active(0)
		pack(self.vbox, hbox)
		########
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		pack(self.vbox, self.fcw, 1, 1)
		self.vbox.set_focus_child(self.fcw)## FIXME
		self.vbox.show_all()
		combo.connect('changed', self.comboChanged)
		##
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), 1, self.onDelete)
		dialog_add_button(self, gtk.STOCK_SAVE, _('_Save'), 2, self.save)
		##
		self.connect('delete-event', self.onDelete)
		try:
			self.fcw.set_current_folder(core.deskDir)
		except AttributeError:## PyGTK < 2.4
			pass
	def comboChanged(self, widget=None, ym=None):
		i = self.combo.get_active()
		if ym==None:
			ym = (ui.cell.year, ui.cell.month)
		if i==0:
			self.fcw.set_current_name('calendar-%.4d-%.2d.html'%ym)
			self.hbox2.hide()
		elif i==1:
			self.fcw.set_current_name('calendar-%.4d.html'%ym[0])
			self.hbox2.hide()
		else:#elif i==2
			self.fcw.set_current_name('calendar.html')
			self.hbox2.show()
		## select_region(0, -4) ## FIXME
	def onDelete(self, widget=None, event=None):## hide(close) File Chooser Dialog
		self.hide()
		return True
	def _save(self, path):
		comboItem = self.combo.get_active()
		months = []
		module = calTypes.primaryModule()
		if comboItem==0:
			s = getCurrentMonthStatus()
			months = [s]
			title = '%s %s'%(locale_man.getMonthName(calTypes.primary, s.month, s.year), _(s.year))
		elif comboItem==1:
			for i in range(1, 13):
				months.append(getMonthStatus(ui.cell.year, i))
			title = '%s %s'%(_('Calendar'), _(ui.cell.year))
		elif comboItem==2:
			y0, m0 = self.ymBox0.get_value()
			y1, m1 = self.ymBox1.get_value()
			for ym in range(y0*12+m0-1, y1*12+m1):
				y, m = divmod(ym, 12)
				m += 1
				months.append(getMonthStatus(y, m))
			title = _('Calendar')
		exportToHtml(path, months, title)
		self.hide()
	def save(self, widget=None):
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		path = self.fcw.get_filename()
		if path in (None, ''):
			return
		print('Exporting to html file "%s"'%path)
		self.waitingDo(
			self._save,
			path,
		)
	def showDialog(self, year, month):
		self.comboChanged(ym=(year, month))
		self.ymBox0.set_value((year, month))
		self.ymBox1.set_value((year, month))
		self.resize(1, 1)
		openWindow(self)
	'''
	def exportSvg(self, path, monthList):## FIXME
		## monthList is a list of tuples (year, month)
		#import cairo
		hspace = 20
		mcal = ui.mainWin.mcal
		x, y, w, h0 = mcal.get_allocation()
		n = len(monthList)
		h = n*h0 + (n-1)*hspace
		fo = open(path+'.svg', 'w')
		surface = cairo.SVGSurface(fo, w, h)
		cr0 = cairo.Context(surface)
		cr = gdk.CairoContext(cr0)
		year = ui.cell.year
		month = ui.cell.month
		day = self.mcal.day
		ui.mainWin.show() ## ??????????????
		for i in range(n):
			surface.set_device_offset(0, i*(h0+hspace))
			mcal.dateChange((monthList[i][0], monthList[i][1], 1))
			mcal.drawAll(cr=cr, cursor=False)
			mcal.queue_draw()
		ui.mainWin.dateChange((year, month, day))
		surface.finish()
	'''



class ExportToIcsDialog(gtk.Dialog, MyDialog):
	def __init__(self, saveIcsFunc, defaultFileName, **kwargs):
		self.saveIcsFunc = saveIcsFunc
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Export to %s')%'iCalendar')
		## parent=None FIXME
		#self.set_has_separator(False)
		########
		hbox = gtk.HBox(spacing=2)
		pack(hbox, gtk.Label(_('From')+' '))
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		pack(hbox, gtk.Label(' '+_('To')+' '))
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		pack(self.vbox, hbox)
		####
		year, month, day = ui.todayCell.dates[calTypes.primary]
		self.startDateInput.set_value((year, 1, 1))
		self.endDateInput.set_value((year+1, 1, 1))
		########
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		pack(self.vbox, self.fcw, 1, 1)
		self.vbox.set_focus_child(self.fcw)## FIXME
		self.vbox.show_all()
		##
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), 1, self.onDelete)
		dialog_add_button(self, gtk.STOCK_SAVE, _('_Save'), 2, self.save)
		##
		self.connect('delete-event', self.onDelete)
		self.fcw.connect('file-activated', self.save)## not working FIXME
		##
		try:
			self.fcw.set_current_folder(core.deskDir)
		except AttributeError:## PyGTK < 2.4
			pass
		if not defaultFileName.endswith('.ics'):
			defaultFileName += '.ics'
		self.fcw.set_current_name(defaultFileName)
	def onDelete(self, widget=None, event=None):## hide(close) File Chooser Dialog
		self.destroy()
		return True
	def _save(self, path, startJd, endJd):
		self.saveIcsFunc(path, startJd, endJd)
		self.destroy()
	def save(self, widget=None):
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		path = self.fcw.get_filename()
		if path in (None, ''):
			return
		print('Exporting to ics file "%s"'%path)
		self.waitingDo(
			self._save,
			path,
			core.primary_to_jd(*self.startDateInput.get_value()),
			core.primary_to_jd(*self.endDateInput.get_value()),
		)
