#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##    Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
##
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License along
##    with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
##    If not, see <http://www.gnu.org/licenses/gpl.txt>.

APP_DESC = 'StarCalendar'

import os, shutil
from os.path import dirname
from os.path import join, isfile, isdir

from scal2.path import *
from scal2.import_config_1to2 import importConfigFrom15, getOldVersion, langDir, langConfDir

from scal2.ui_gtk import *

gtk.window_set_default_icon_from_file('%s/starcal.png'%pixDir)

langNameList = []
langCodeList = []

langDefaultCode = ''

win = gtk.Dialog(title=APP_DESC+' - First Run', buttons=(gtk.STOCK_OK, gtk.ResponseType.OK, gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL))
langHbox = gtk.HBox()
pack(langHbox, gtk.Label('Select Language:'))


importCheckb = None
oldVersion = getOldVersion()
if oldVersion and '1.5.0' < oldVersion < '1.6.0':## FIXME
    importCheckb = gtk.CheckButton('Import configurations from %s %s'%(APP_DESC, oldVersion))
    importCheckb.connect('clicked', lambda cb: langHbox.set_sensitive(not cb.get_active()))
    importCheckb.set_active(True)
    pack(win.vbox, importCheckb)


langCombo = gtk.ComboBoxText()
for fname in os.listdir(langDir):
    fpath = join(langDir, fname)
    if not os.path.isfile(fpath):
        continue
    text = open(fpath).read().strip()
    if fname=='default':
        langDefaultCode = text
        continue
    langName = text.split('\n')[0]
    langNameList.append(langName)
    langCodeList.append(fname)

    langCombo.append_text(langName)

if langDefaultCode and (langDefaultCode in langCodeList):
    langCombo.set_active(langCodeList.index(langDefaultCode))
else:
    langCombo.set_active(0)

pack(langHbox, langCombo, 1, 1)
pack(win.vbox, langHbox)
win.vbox.show_all()

if win.run()==gtk.ResponseType.OK:
    #print('RESPONSE_OK')
    if importCheckb and importCheckb.get_active():
        importConfigFrom15()
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
                dst_path = join(confDir, fname)
                #print(src_path)
                if isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy(src_path, dst_path)
        else:
            open(join(confDir, 'locale.conf'), 'w').write('lang=%r'%langCode)

win.destroy()

if not os.path.isdir(confDir):
    os.mkdir(confDir, 0o755)


