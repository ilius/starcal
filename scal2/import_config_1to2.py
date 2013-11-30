#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

import sys, os, shutil
from os.path import join, isdir, isfile, dirname
print(dirname(dirname(__file__)))
sys.path.insert(0, dirname(dirname(__file__)))

from scal2.path import *
from scal2.utils import cmpVersion
from scal2.locale_man import langDir
from scal2.plugin_man import loadPlugin


import pango

import gtk
from gtk import gdk

from scal2.ui_gtk.font_utils import gfontDecode
from scal2.ui_gtk.color_utils import gdkColorToRgb

langConfDir = join(rootDir, 'conf', 'defaults')

if os.sep=='/':## Unix-like OS
    confDirOld = homeDir + '/.starcal'
elif os.sep=='\\':## Dos/Windows OS
    confDirOld = os.getenv('APPDATA') + '\\starcal'
else:
    raise RuntimeError('bad seperator (os.sep=="%s") !! What is your Operating System?!'%os.sep)


def getOldVersion():## return version of starcal 1.*
    if isdir(confDirOld):
        pref = join(confDirOld, 'pref')
        if isfile(pref):
            for line in open(pref).readlines():
                if line.startswith('version'):
                    exec(line)
                    return version
    return ''


def importConfigFrom15(overwrite=True):
    if not isdir(confDirOld):
        print('directory "%s" does not exist'%confDirOld)
        return

    if not isdir(confDir):
        os.mkdir(confDir)

    for fname in ('hijri.conf', 'jalali.conf'):
        old_path = join(confDirOld, fname)
        if isfile(old_path):
            new_path = join(confDir, fname)
            if overwrite or not isfile(new_path):
                shutil.copy(old_path, new_path)
    '''
    plugDirOld = join(confDirOld, 'plugins')
    if isdir(plugDirOld):
        if not isdir(plugDir):
            os.mkdir(plugDir)
        for fname in os.listdir(plugDirOld):
            old_path = join(plugDirOld, fname)
            new_path = join(plugDir, fname)
            if isfile(old_path):
                try:
                    shutil.copy(old_path, new_path)
                except:
                    pass
            elif isdir(old_path):
                try:
                    shutil.copytree(old_path, new_path)
                except:
                    pass
    '''

    pref = join(confDirOld, 'pref')
    if isfile(pref):
        loadPlug = loadPlugin
        exec(open(pref).read())
        locale_conf = join(confDir, 'locale.conf')
        if overwrite or not isfile(locale_conf):
            lang = ['', 'en_US.UTF-8', 'fa_IR.UTF-8', 'ar_IQ.UTF-8'][lang]
            open(locale_conf, 'w').write('lang=%r'%lang)
        core_conf = join(confDir, 'core.conf')
        if overwrite or not isfile(core_conf):

            open(core_conf, 'w').write(\
'''
holidayWeekDays=%r
firstWeekDayAuto=%r
firstWeekDay=%r
weekNumberModeAuto=%r
weekNumberMode=%r'''%(holidayWeekDays, firstWeekDayAuto, firstWeekDay, weekNumberModeAuto, weekNumberMode))
        ui_conf = join(confDir, 'ui.conf')
        if overwrite or not isfile(ui_conf):
            for item in shownDates:
                item['font'] = gfontDecode(item['font'])
                item['color'] = gdkColorToRgb(item['color'])

            fontCustom = gfontDecode(fontCustom)

            mcalGridColor = wcalGridColor = gdkColorToRgb(gridColor) + (gridAlpha/257,)
            bgColor = gdkColorToRgb(bgColor) + (bgColorAlpha/257,)
            borderColor = gdkColorToRgb(borderColor) + (borderColorAlpha/257,)
            borderTextColor = gdkColorToRgb(borderTextColor)
            holidayColor = gdkColorToRgb(holidayColor)
            inactiveColor = gdkColorToRgb(inactiveColor) + (inactiveColorAlpha/257,)
            cursorOutColor = gdkColorToRgb(cursorOutColor)
            cursorBgColor = gdkColorToRgb(cursorBgColor) + (cursorBgAlpha/257,)

            pluginsTextTray = extradayTray
            maxDayCacheSize = maxCache*30
            maxWeekCacheSize = maxCache*4

            text = ''
            for name in (
                'showMain',
                'winTaskbar',
                'showDigClockTr',
                'mcalGrid',
                'mcalGridColor',
                'wcalGridColor',
                'fontCustom',
                'fontCustomEnable',
                'bgUseDesk',
                'bgColor',
                'borderColor',
                'cursorOutColor',
                'cursorBgColor',
                'holidayColor',
                'inactiveColor',
                'borderTextColor',
                'dragIconCell',
                'maxDayCacheSize',
                'maxWeekCacheSize'
                'pluginsTextTray',
                'showYmArrows',
                'prefPagesOrder',
            ):
                text += '%s = %r\n'%(name, eval(name))
            open(ui_conf, 'w').write(text)
        ui_gtk_conf = join(confDir, 'ui-gtk.conf')
        if overwrite or not isfile(ui_gtk_conf):
            from scal2.ui_gtk.utils import stock_arrow_repr
            open(ui_gtk_conf, 'w').write(\
'''dateFormat=%r
clockFormat=%r
'''%(
        dateFormat,
        clockFormat,
    ))

    live_conf_old = join(confDirOld, 'live-confg')
    if isfile(live_conf_old):
        live_conf = join(confDir, 'ui-live.conf')
        if overwrite or not isfile(live_conf):
            exec(open(live_conf_old).read())
            text = ''
            for name in ('winX', 'winY', 'winWidth', 'winKeepAbove', 'winSticky'):
                text += '%s = %r\n'%(name, eval(name))
            open(live_conf, 'w').write(text)

    if calHeightReq>0:
        mcalHeight = calHeightReq
        open(join(confDir, 'ui-customize.conf'), 'w').write('ui.mcalHeight=%s'%mcalHeight)



