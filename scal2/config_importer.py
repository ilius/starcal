#!/usr/bin/env python2

import sys, os, shutil
from os.path import join, isdir, isfile, dirname
print dirname(dirname(__file__))
sys.path.insert(0, dirname(dirname(__file__)))

from scal2.paths import *
from scal2.plugin_man import loadPlugin
from scal2.utils import cmpVersion

import pango

import gtk
from gtk import gdk

#from scal2.ui_gtk.preferences import gdkColorToRgb, gfontDecode


gdkColorToRgb = lambda gc: (gc.red/257, gc.green/257, gc.blue/257)
pfontDecode = lambda pfont: (pfont.get_family(),
                             pfont.get_weight()==pango.WEIGHT_BOLD,
                             pfont.get_style()==pango.STYLE_ITALIC,
                             pfont.get_size()/1024
                            )
gfontDecode = lambda gfont: pfontDecode(pango.FontDescription(gfont))## gfont is a string like "Terafik 12"

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
        print 'directory "%s" does not exist'%confDirOld
        sys.exit(1)

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
            shownCals = shownDates
            
            for item in shownDates:
                item['font'] = gfontDecode(item['font'])
                item['color'] = gdkColorToRgb(item['color'])

            fontCustom = gfontDecode(fontCustom)

            gridColor = gdkColorToRgb(gridColor) + (gridAlpha/257,)
            bgColor = gdkColorToRgb(bgColor) + (bgColorAlpha/257,)
            borderColor = gdkColorToRgb(borderColor) + (borderColorAlpha/257,)
            borderTextColor = gdkColorToRgb(borderTextColor)
            holidayColor = gdkColorToRgb(holidayColor)
            inactiveColor = gdkColorToRgb(inactiveColor) + (inactiveColorAlpha/257,)
            cursorOutColor = gdkColorToRgb(cursorOutColor)
            cursorBgColor = gdkColorToRgb(cursorBgColor) + (cursorBgAlpha/257,)
            
            maxCache *= 50
        
            text = ''
            for name in ('shownCals', 'showMain', 'winTaskbar', 'showWinController', 'showDigClockTr', 'calGrid',
            'gridColor', 'fontUseDefault', 'fontCustom', 'customdayShowIcon', 'bgUseDesk', 'bgColor',
            'borderColor', 'cursorOutColor', 'cursorBgColor', 'holidayColor', 'inactiveColor', 'borderTextColor',
            'calLeftMargin', 'calTopMargin', 'cursorD', 'cursorR', 'cursorFixed', 'cursorW', 'cursorH', 'dragIconCell',
            'maxCache', 'extradayTray', 'showYmArrows', 'prefPagesOrder'):
                text += '%s = %r\n'%(name, eval(name))
            open(ui_conf, 'w').write(text)
        ui_gtk_conf = join(confDir, 'ui-gtk.conf')
        if overwrite or not isfile(ui_gtk_conf):
            open(ui_gtk_conf, 'w').write(\
'''dateFormat=%r
clockFormat=%r
prevStock=%r
nextStock=%r
'''%(dateFormat, clockFormat, prevStock, nextStock))


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
        calHeight = calHeightReq
        open(join(confDir, 'ui-customize.conf'), 'w').write(
'''
ui.calHeight=%s
'''%calHeight
        )





