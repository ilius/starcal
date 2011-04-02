#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##    Copyright (C) 2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
##
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License,    or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful, 
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License along
##    with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
##    If not, see <http://www.gnu.org/licenses/gpl.txt>.

import os, shutil
from os.path import dirname
from os.path import join as join

import gtk

rootDir = dirname(dirname(dirname(__file__)))
langDir = join(rootDir, 'lang')

homeDir = os.getenv('HOME')
confDir = join(homeDir, '.starcal2')
pixDir = os.path.join(rootDir, 'pixmaps')

gtk.window_set_default_icon_from_file('%s/starcal2.png'%pixDir)

langNameList = []
langCodeList = []

langDefaultCode = ''

win = gtk.Dialog(title='StarCalendar: Language', buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
hbox = gtk.HBox()
hbox.pack_start(gtk.Label('Select Language:'), 0, 0)
combo = gtk.combo_box_new_text()
dirname
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

    combo.append_text(langName)

if langDefaultCode and (langDefaultCode in langCodeList):
    combo.set_active(langCodeList.index(langDefaultCode))
else:
    combo.set_active(0)

hbox.pack_start(combo, 1, 1)
win.vbox.pack_start(hbox)
win.vbox.show_all()

if win.run()==gtk.RESPONSE_OK:
    i = combo.get_active()
    langCode = langCodeList[i]
    langConfDir = join(rootDir, 'lang_config', langCode)

    print 'Setting language', langCode

    if not os.path.isdir(confDir):
        os.mkdir(confDir, 0755)

    if os.path.isdir(langConfDir):
        for fname in os.listdir(langConfDir):
            print join(langConfDir, fname)
            shutil.copy(join(langConfDir, fname), confDir)
    else:
        open(join(confDir, 'locale.conf'), 'w').write('lang=%r'%langCode)


