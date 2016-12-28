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

import os

os.environ['LANG'] = 'en_US.UTF-8'  # FIXME

import subprocess
from time import localtime
from time import time as now
import sys
from math import ceil

from scal3 import ui

from gi.repository.GObject import timeout_add

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


_ = str ## FIXME
iceil = lambda f: int(ceil(f))


def error_exit(resCode, text, parent=None):
	d = gtk.MessageDialog(
		parent,
		gtk.DialogFlags.DESTROY_WITH_PARENT,
		gtk.MessageType.ERROR,
		gtk.ButtonsType.OK,
		text.strip(),
	)
	d.set_title('Error')
	d.run()
	sys.exit(resCode)


class AdjusterDialog(gtk.Dialog):
	xpad = 15

	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Adjust System Date & Time'))  # FIXME
		self.set_icon(self.render_icon(
			gtk.STOCK_PREFERENCES,
			gtk.IconSize.BUTTON,
		))
		#########
		self.buttonCancel = self.add_button(gtk.STOCK_CANCEL, 0)
		#self.buttonCancel.connect('clicked', lambda w: sys.exit(0))
		self.buttonSet = self.add_button(_('Set System Time'), 1)
		#self.buttonSet.connect('clicked', self.setSysTimeClicked)
		#########
		hbox = gtk.HBox()
		self.label_cur = gtk.Label(_('Current:'))
		pack(hbox, self.label_cur)
		pack(self.vbox, hbox)
		#########
		hbox = gtk.HBox()
		self.radioMan = gtk.RadioButton(None, _('Set _Manully:'), True)
		self.radioMan.connect('clicked', self.radioManClicked)
		pack(hbox, self.radioMan)
		pack(self.vbox, hbox)
		######
		vb = gtk.VBox()
		sg = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		###
		hbox = gtk.HBox()
		##
		l = gtk.Label('')
		l.set_property('width-request', self.xpad)
		pack(hbox, l)
		##
		self.ckeckbEditTime = gtk.CheckButton(_('Edit Time'))
		self.editTime = False
		self.ckeckbEditTime.connect('clicked', self.ckeckbEditTimeClicked)
		pack(hbox, self.ckeckbEditTime)
		sg.add_widget(self.ckeckbEditTime)
		self.timeInput = TimeButton() ## ??????? options
		pack(hbox, self.timeInput)
		pack(vb, hbox)
		###
		hbox = gtk.HBox()
		##
		l = gtk.Label('')
		l.set_property('width-request', self.xpad)
		pack(hbox, l)
		##
		self.ckeckbEditDate = gtk.CheckButton(_('Edit Date'))
		self.editDate = False
		self.ckeckbEditDate.connect('clicked', self.ckeckbEditDateClicked)
		pack(hbox, self.ckeckbEditDate)
		sg.add_widget(self.ckeckbEditDate)
		self.dateInput = DateButton() ## ??????? options
		pack(hbox, self.dateInput)
		pack(vb, hbox)
		###
		pack(self.vbox, vb, 0, 0, 10)#?????
		self.vboxMan = vb
		######
		hbox = gtk.HBox()
		self.radioNtp = gtk.RadioButton(
			group=self.radioMan,
			label=_('Set from NTP:'),
		)
		self.radioNtp.connect('clicked', self.radioNtpClicked)
		pack(hbox, self.radioNtp)
		pack(self.vbox, hbox)
		###
		hbox = gtk.HBox()
		##
		l = gtk.Label('')
		l.set_property('width-request', self.xpad)
		pack(hbox, l)
		##
		pack(hbox, gtk.Label(_('Server:') + ' '))
		combo = gtk.ComboBoxText.new_with_entry()
		combo.get_child().connect('changed', self.updateSetButtonSensitive)
		pack(hbox, combo, 1, 1)
		self.ntpServerEntry = combo.get_child()
		for s in ui.ntpServers:
			combo.append_text(s)
		combo.set_active(0)
		self.hboxNtp = hbox
		pack(self.vbox, hbox)
		######
		self.radioManClicked()
		#self.radioNtpClicked()
		self.ckeckbEditTimeClicked()
		self.ckeckbEditDateClicked()
		######
		self.updateTimes()
		self.vbox.show_all()

	def radioManClicked(self, radio=None):
		if self.radioMan.get_active():
			self.vboxMan.set_sensitive(True)
			self.hboxNtp.set_sensitive(False)
		else:
			self.vboxMan.set_sensitive(False)
			self.hboxNtp.set_sensitive(True)
		self.updateSetButtonSensitive()

	def radioNtpClicked(self, radio=None):
		if self.radioNtp.get_active():
			self.vboxMan.set_sensitive(False)
			self.hboxNtp.set_sensitive(True)
		else:
			self.vboxMan.set_sensitive(True)
			self.hboxNtp.set_sensitive(False)
		self.updateSetButtonSensitive()

	def ckeckbEditTimeClicked(self, checkb=None):
		self.editTime = self.ckeckbEditTime.get_active()
		self.timeInput.set_sensitive(self.editTime)
		self.updateSetButtonSensitive()

	def ckeckbEditDateClicked(self, checkb=None):
		self.editDate = self.ckeckbEditDate.get_active()
		self.dateInput.set_sensitive(self.editDate)
		self.updateSetButtonSensitive()

	#def set_sys_time(self):
	#	if os.path.isfile('/bin/date'):
	#		pass  # FIXME
	#	elif sys.platform == 'win32':
	#		import win32api
	#		win32api.SetSystemTime()##????????
	#	else:
	#		pass

	def updateTimes(self):
		dt = now() % 1
		timeout_add(iceil(1000 * (1 - dt)), self.updateTimes)
		#print('updateTimes', dt)
		lt = localtime()
		self.label_cur.set_label(
			_('Current:') +
			' %.4d/%.2d/%.2d - %.2d:%.2d:%.2d' % lt[:6]
		)
		if not self.editTime:
			self.timeInput.set_value(lt[3:6])
		if not self.editDate:
			self.dateInput.set_value(lt[:3])
		return False

	def updateSetButtonSensitive(self, widget=None):
		if self.radioMan.get_active():
			self.buttonSet.set_sensitive(self.editTime or self.editDate)
		elif self.radioNtp.get_active():
			self.buttonSet.set_sensitive(
				self.ntpServerEntry.get_text() != ''
			)

	def setSysTimeClicked(self, widget=None):
		if self.radioMan.get_active():
			if self.editTime:
				h, m, s = self.timeInput.get_value()
				if self.editDate:
					Y, M, D = self.dateInput.get_value()
					cmd = [
						'/bin/date',
						'-s',
						'%.4d/%.2d/%.2d %.2d:%.2d:%.2d' % (
							Y, M, D,
							h, m, s,
						),
					]
				else:
					cmd = [
						'/bin/date',
						'-s',
						'%.2d:%.2d:%.2d' % (h, m, s),
					]
			else:
				if self.editDate:
					Y, M, D = self.dateInput.get_value()
					##h, m, s = self.timeInput.get_value()
					h, m, s = localtime()[3:6]
					cmd = [
						'/bin/date',
						'-s',
						'%.4d/%.2d/%.2d %.2d:%.2d:%.2d' % (
							Y, M, D,
							h, m, s,
						),
					]
				else:
					error_exit('No change!', self)  # FIXME
		elif self.radioNtp.get_active():
			cmd = ['ntpdate', self.ntpServerEntry.get_text()]
			#if os.path.isfile('/usr/sbin/ntpdate'):
			#	cmd = ['/usr/sbin/ntpdate', self.ntpServerEntry.get_text()]
			#else:
			#	error_exit(
			#	'Could not find command /usr/sbin/ntpdate: no such file!',
			#	self,
			#)  # FIXME
		else:
			error_exit('Not valid option!', self)
		proc = subprocess.Popen(
			cmd,
			stderr=subprocess.PIPE,
			stdout=subprocess.PIPE,
		)
		resCode = proc.wait()
		error = proc.stderr.read().strip()
		output = proc.stdout.read().strip()
		if output:
			print(output)
		#print('resCode=%r, error=%r, output=%r' % (resCode, error, output))
		if error:
			print(error)
		if resCode != 0:
			error_exit(
				resCode,
				error,
				parent=self,
			)
		#else:
		#	sys.exit(0)


if __name__ == '__main__':
	if os.getuid() != 0:
		error_exit(1, 'This program must be run as root')
		#raise OSError('This program must be run as root')
		###os.setuid(0)  # FIXME
	d = AdjusterDialog(parent=None)
	#d.set_keap_above(True)
	if d.run() == 1:
		d.setSysTimeClicked()
