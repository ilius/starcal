#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##	Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
##
##	This program is free software; you can redistribute it and/or modify
##	it under the terms of the GNU General Public License as published by
##	the Free Software Foundation; either version 3 of the License, or
##	(at your option) any later version.
##
##	This program is distributed in the hope that it will be useful,
##	but WITHOUT ANY WARRANTY; without even the implied warranty of
##	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##	GNU General Public License for more details.
##
##	You should have received a copy of the GNU General Public License along
##	with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
##	If not, see <http://www.gnu.org/licenses/gpl.txt>.

APP_DESC = 'StarCalendar'

import os, shutil
from os.path import dirname
from os.path import join, isfile, isdir

from scal3.path import *
from scal3.import_config_2to3 import *
from scal3.locale_man import langDict, langDefault

from scal3.ui_gtk import *

langConfDir = join(rootDir, 'conf', 'defaults')

gtk.Window.set_default_icon_from_file(join(pixDir, 'starcal.png'))

langNameList = []
langCodeList = []


win = gtk.Dialog(
	title=APP_DESC+' 3.x - First Run',
	buttons=(
		gtk.STOCK_OK,
		gtk.ResponseType.OK,
		gtk.STOCK_CANCEL,
		gtk.ResponseType.CANCEL,
	)
)
langHbox = gtk.HBox()
pack(langHbox, gtk.Label('Select Language:'))


importCheckb = None
oldVersion = getOldVersion()
if oldVersion:## and '2.2.0' <= oldVersion < '2.5.0':## FIXME
	importCheckb = gtk.CheckButton('Import configurations from %s %s'%(APP_DESC, oldVersion))
	importCheckb.connect('clicked', lambda cb: langHbox.set_sensitive(not cb.get_active()))
	importCheckb.set_active(True)
	pack(win.vbox, importCheckb)


langCombo = gtk.ComboBoxText()

for langObj in langDict.values():
	langNameList.append(langObj.name)
	langCodeList.append(langObj.code)
	langCombo.append_text(langObj.name)


if langDefault and (langDefault in langCodeList):
	langCombo.set_active(langCodeList.index(langDefault))
else:
	langCombo.set_active(0)

pack(langHbox, langCombo, 1, 1)
pack(win.vbox, langHbox)

pbarHbox = gtk.HBox()
pbar = gtk.ProgressBar()
pack(pbarHbox, pbar, 1, 1)
pack(win.vbox, pbarHbox)


win.vbox.show_all()

if win.run()==gtk.ResponseType.OK:
	#print('RESPONSE OK')
	if importCheckb and importCheckb.get_active():
		importCheckb.set_sensitive(False)
		langHbox.set_sensitive(False)
		win.get_action_area().set_sensitive(False)
		for frac in importConfigIter():
			pbar.set_fraction(frac)
			percent = frac * 100
			text = '%.1f%%'%percent ## FIXME
			pbar.set_text(text)
			while gtk.events_pending():
				gtk.main_iteration_do(False)
	else:
		i = langCombo.get_active()
		langCode = langCodeList[i]
		thisLangConfDir = join(langConfDir, langCode)
		#print('Setting language', langCode)
		if not os.path.isdir(confDir):
			os.mkdir(confDir, 0o755)
		if os.path.isdir(thisLangConfDir):
			for fname in os.listdir(thisLangConfDir):
				src_path = join(thisLangConfDir, fname)
				if not isfile(src_path):
					continue
				dst_path = join(confDir, fname)
				#print(src_path)
				shutil.copy(src_path, dst_path)
		else:
			open(join(confDir, 'locale.json'), 'w').write(
				dataToPrettyJson({
					'lang': langCode,
				})
			)

win.destroy()

if not os.path.isdir(confDir):
	os.mkdir(confDir, 0o755)


