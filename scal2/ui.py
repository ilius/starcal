# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from time import time
#print time(), __file__ ## FIXME

import sys, os, os.path, shutil
from os import listdir
from os.path import dirname, join, isfile, isdir, splitext
from xml.dom.minidom import parse## remove FIXME
from subprocess import Popen
from gobject import timeout_add, timeout_add_seconds ## FIXME

from scal2.utils import NullObj, toStr, cleanCacheDict, restart
from scal2.os_utils import makeDir
from scal2.paths import *

import scal2.locale_man
from scal2.locale_man import tr as _

from scal2 import core
from scal2.core import APP_NAME, myRaise, myRaiseTback, getMonthLen, getNextMonth, getPrevMonth, osName

from scal2 import event_man

uiName = ''
null = NullObj()

def parseDroppedDate(text):
    part = text.split('/')
    if len(part)==3:
        try:
            part[0] = int(part[0])
            part[1] = int(part[1])
            part[2] = int(part[2])
        except:
            myRaise(__file__)
            return None
        minMax = ((1300, 2100), (1, 12), (1, 31))
        formats=(
                [0, 1, 2],
                [1, 2, 0],
                [2, 1, 0],
        )
        for format in formats:
            for i in range(3):
                valid = True
                f = format[i]
                if not (minMax[f][0] <= part[i] <= minMax[f][1]):
                    valid = False
                    #print 'format %s was not valid, part[%s]=%s'%(format, i, part[i])
                    break
            if valid:
                year = part[format.index(0)] ## "format" must be list because of method "index"
                month = part[format.index(1)]
                day = part[format.index(2)]
                break
        if not valid:
            return None
    else:
        return None
    ##??????????? when drag from a persian GtkCalendar with format %y/%m/%d
    #if year < 100:
    #    year += 2000
    return (year, month, day)

def shownCalsStr():
    n = len(shownCals)
    st='('
    for i in range(n):
        d = shownCals[i].copy()
        st+='\n{'
        for k in d.keys():
            v = d[k]
            if type(k)==str:
                ks = '\'%s\''%k
            else:
                ks = str(k)
            if type(v)==str:
                vs = '\'%s\''%v
            else:
                vs = str(v)
            st += '%s:%s, '%(ks,vs)
        if i==n-1:
            st = st[:-2] + '})'
        else:
            st = st[:-2] + '},'
    return st

def saveLiveConf():
    text = ''
    for key in (
        'winX', 'winY', 'winWidth',
        'winKeepAbove', 'winSticky',
        'pluginsTextIsExpanded', 'bgColor',
        'eventManShowDescription',## FIXME
    ):
        text += '%s=%r\n'%(key, eval(key))
    open(confPathLive, 'w').write(text)

def saveLiveConfLoop():
    tm = time()
    if tm-lastLiveConfChangeTime > saveLiveConfDelay:
        saveLiveConf()
        return False ## Finish loop
    return True ## Continue loop

def checkNeedRestart():
    for key in needRestartPref.keys():
        if needRestartPref[key] != eval(key):
            print '"%s", "%s", "%s"'%(key, needRestartPref[key], eval(key))
            return True
    return False

getPywPath = lambda: join(rootDir, APP_NAME + ('-qt' if uiName=='qt' else '') + '.pyw')

def winMakeShortcut(srcPath, dstPath, iconPath=None):
    from win32com.client import Dispatch
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(dstPath)
    shortcut.Targetpath = srcPath
    #shortcut.WorkingDirectory = ...
    shortcut.save()



def addStartup():
    if osName=='win':
        makeDir(winStartupDir)
        #fname = APP_NAME + ('-qt' if uiName=='qt' else '') + '.pyw'
        fname = core.COMMAND + '.pyw'
        fpath = join(rootDir, fname)
        #open(winStartupFile, 'w').write('execfile(%r, {"__file__":%r})'%(fpath, fpath))
        try:
            winMakeShortcut(fpath, winStartupFile)
        except:
            return False
        else:
            return True
    elif isdir('%s/.config'%homeDir):## osName in ('linux', 'mac') ## maybe Gnome/KDE on Solaris, *BSD, ...
        text = '''[Desktop Entry]
Type=Application
Name=%s %s
Icon=%s
Exec=%s'''%(core.VERSION, core.APP_DESC, APP_NAME, core.COMMAND)## double quotes needed when the exec path has space
        makeDir(comDeskDir)
        try:
            fp = open(comDesk, 'w')
        except:
            core.myRaise(__file__)
            return False
        else:
            fp.write(text)
            return True
    elif osName=='mac':## FIXME
        pass
    return False

def removeStartup():
    if osName=='win':## FIXME
        if isfile(winStartupFile):
            os.remove(winStartupFile)
    elif isfile(comDesk):
        os.remove(comDesk)

def checkStartup():
    if osName=='win':
        return isfile(winStartupFile)
    elif isfile(comDesk):
        return True
    return False

def openUrl(url):
    if osName=='win':
        return Popen([url])
    if osName=='mac':
        return Popen(['open', url])
    try:
        Popen(['xdg-open', url])
    except:
        myRaise()
    else:
        return
    #if not url.startswith('http'):## FIXME
    #    return
    try:
        import webbrowser
        return webbrowser.open(url)
    except ImportError:
        pass
    try:
        import gnomevfs
        return gnomevfs.url_show(url)
    except ImportError:
        pass
    for command in ('gnome-www-browser', 'firefox', 'iceweasel', 'konqueror'):
        try:
            Popen([command, url])
        except:
            pass
        else:
            return

def dayOpenEvolution(arg=None):
    ##(y, m, d) = core.jd_to(cell.jd-1, core.DATE_GREG) ## in gnome-cal opens prev day! why??
    (y, m, d) = cell.dates[core.DATE_GREG]
    Popen('LANG=en_US.UTF-8 evolution calendar:///?startdate=%.4d%.2d%.2d'%(y, m, d), shell=True)## FIXME
    ## 'calendar:///?startdate=%.4d%.2d%.2dT120000Z'%(y, m, d)
    ## What "Time" pass to evolution? like gnome-clock: T193000Z (19:30:00) / Or ignore "Time"
    ## evolution calendar:///?startdate=$(date +"%Y%m%dT%H%M%SZ")

def dayOpenSunbird(arg=None):
    ## does not work on latest version of Sunbird ## FIXME
    ## and Sunbird seems to be a dead project
    ## Opens previous day in older version
    (y, m, d) = cell.dates[core.DATE_GREG]
    Popen('LANG=en_US.UTF-8 sunbird -showdate %.4d/%.2d/%.2d'%(y, m, d), shell=True)

## How do this with KOrginizer? FIXME

#######################################################################


class Cell:## status and information of a cell
    def __init__(self, jd):
        self.eventsData = []
        self.eventsDataIsSet = False
        self.pluginsText = ''
        ###
        self.jd = jd
        date = core.jd_to(jd, core.primaryMode)
        (self.year, self.month, self.day) = date
        self.weekDay = core.jwday(jd)
        self.holiday = (self.weekDay in core.holidayWeekDays)
        ###################
        self.dates = []
        for mode in xrange(core.modNum):
            if mode==core.primaryMode:
                self.dates.append((self.year, self.month, self.day))
            else:
                self.dates.append(core.jd_to(jd, mode))
        ###################
        for k in core.plugIndex:
            plug = core.allPlugList[k]
            if plug.enable:
                try:
                    plug.update_cell(self)
                except:
                    myRaiseTback()
    def format(self, binFmt, mode, tm=null):## FIXME
        (pyFmt, funcs) = binFmt
        return pyFmt%tuple(f(self, mode, tm) for f in funcs)
    def inSameMonth(self, other):
        return self.dates[core.primaryMode][:2] == other.dates[core.primaryMode][:2]

class CellCache:
    def __init__(self):
        self.jdCells = {} ## a mapping from julan_day to Cell instance
        self.plugins = {}
        self.weekEvents = {}
    def clear(self):
        global cell, todayCell
        self.jdCells = {}
        self.weekEvents = {}
        cell = self.getCell(cell.jd)
        todayCell = self.getCell(todayCell.jd)
    def registerPlugin(self, name, setParamsCallable, getCellGroupCallable):
        """
            setParamsCallable(cell): cell.attr1 = value1 ....
            getCellGroupCallable(cellCache, *args): return cell_group
                call cellCache.getCell(jd) inside getCellGroupFunc
        """
        self.plugins[name] = {
            'setParamsCallable': setParamsCallable,
            'getCellGroupCallable': getCellGroupCallable,
        }
        for local_cell in self.jdCells.values():
            setParamsCallable(local_cell)
    def getCell(self, jd):
        if self.jdCells.has_key(jd):
            return self.jdCells[jd]
        else:
            return self.buildCell(jd)
    def getTmpCell(self, jd):## don't keep, no eventsData, no plugin params
        if self.jdCells.has_key(jd):
            return self.jdCells[jd]
        else:
            return Cell(jd)
    getCellByDate = lambda self, year, month, day: self.getCell(core.to_jd(year, month, day, core.primaryMode))
    getTodayCell = lambda self: self.getCell(core.getCurrentJd())
    def getCellByDate(self, year, month, day):
        return self.getCell(core.to_jd(year, month, day, core.primaryMode))
    def buildCell(self, jd):
        local_cell = Cell(jd)
        for pluginData in self.plugins.values():
            pluginData['setParamsCallable'](local_cell)
        #local_cell.eventsData = event_man.getDayOccurrenceData(local_cell.jd, eventGroups)
        self.jdCells[jd] = local_cell
        cleanCacheDict(self.jdCells, maxDayCacheSize, jd)
        return local_cell
    def calcEventsData(self, cellList):
        changed = False
        for local_cell in cellList:
            if not local_cell.eventsDataIsSet:
                changed = True
                local_cell.eventsData = event_man.getDayOccurrenceData(local_cell.jd, eventGroups)
                local_cell.eventsDataIsSet = True
        if changed and mainWin:## prevent from infinit loop!
            mainWin.onDateChange()
    def getCellGroup(self, pluginName, *args):
        cellGroup = self.plugins[pluginName]['getCellGroupCallable'](self, *args)
        timeout_add_seconds(0, self.calcEventsData, cellGroup.allCells())
        return cellGroup
    def getWeekData(self, absWeekNumber):
        cells = self.getCellGroup('WeekCal', absWeekNumber)
        try:
            wEventData = self.weekEvents[absWeekNumber]
        except KeyError:
            wEventData = event_man.getWeekOccurrenceData(absWeekNumber, eventGroups)
            cleanCacheDict(self.weekEvents, maxWeekCacheSize, absWeekNumber)
            self.weekEvents[absWeekNumber] = wEventData
        return (cells, wEventData)
    #def getMonthData(self, year, month):## needed? FIXME


def changeDate(year, month, day, mode=None):
    global cell
    if mode is None:
        mode = core.primaryMode
    cell = cellCache.getCell(core.to_jd(year, month, day, mode))


def jdPlus(plus=1):
    global cell
    cell = cellCache.getCell(cell.jd + plus)

def monthPlus(plus=1):
    global cell
    if plus==1:
        (year, month) = getNextMonth(cell.year, cell.month)
    elif plus==-1:
        (year, month) = getPrevMonth(cell.year, cell.month)
    else:
        raise ValueError('monthPlus: bad argument %s'%plus)
    day = min(cell.day, getMonthLen(year, month, core.primaryMode))
    cell = cellCache.getCellByDate(year, month, day)

def yearPlus(plus=1):
    global cell
    year = cell.year + plus
    month = cell.month
    day = min(cell.day, getMonthLen(year, month, core.primaryMode))
    cell = cellCache.getCellByDate(year, month, day)

getFont = lambda: list(fontDefault if fontUseDefault else fontCustom)

def getHolidaysJdList(startJd, endJd):
    jdList = []
    for jd in range(startJd, endJd):
        tmpCell = cellCache.getTmpCell(jd)
        if tmpCell.holiday:
            jdList.append(jd)
    return jdList


######################################################################

def checkMainWinItems():
    global mainWinItems
    #print ui.mainWinItems
    ## cleaning and updating mainWinItems
    indexes = {}
    names = set()
    for (i, (name, enable)) in enumerate(mainWinItems):
        indexes[name] = i
        names.add(name)
    defaultNames = set([name for (name, i) in mainWinItemsDefault])
    #print sorted(list(names)), sorted(list(defaultNames))
    for name in names.difference(defaultNames):
        #print '----- removed', name, mainWinItems[indexes[name]]
        mainWinItems.pop(indexes[name])
    for name in defaultNames.difference(names):
        #print '------ new', name
        mainWinItems.append((name, False))## FIXME


def deleteEventGroup(group):
    eventGroups.moveToTrash(group, eventTrash, addToFirst=True)

def moveEventToTrash(group, event):
    group.remove(event)
    group.save()
    eventTrash.insert(0, event)## or append? FIXME
    eventTrash.save()

def moveEventToTrashFromOutside(group, event):
    global trashedEvents
    eventIndex = group.index(event.id)
    moveEventToTrash(group, event)
    trashedEvents.append((group.id, event.id, eventIndex))

getEvent = lambda groupId, eventId: eventGroups[groupId][eventId]

def duplicateGroupTitle(group):
    title = toStr(group.title)
    titleList = [toStr(g.title) for g in eventGroups]
    parts = title.split('#')
    try:
        index = int(parts[-1])
        title = '#'.join(parts[:-1])
    except:
        #myRaise()
        index = 1
    index += 1
    while True:
        newTitle = title + '#%d'%index
        if newTitle not in titleList:
            group.title = newTitle
            return
        index += 1

######################################################################
shownCals = [
    {'enable':True, 'mode':0, 'x':0,  'y':-2, 'font':None, 'color':(220, 220, 220)},
    {'enable':True, 'mode':1, 'x':18, 'y':5,  'font':None, 'color':(165, 255, 114)},
    {'enable':True, 'mode':2, 'x':-18,'y':4,  'font':None, 'color':(0, 200, 205)},
]
core.primaryMode = shownCals[0]['mode']
################################
tagsDir = join(pixDir, 'event')

class TagIconItem:
    def __init__(self, name, desc='', icon='', eventTypes=()):
        self.name = name
        if not desc:
            desc = name.capitalize()
        self.desc = _(desc)
        if icon:
            if not icon.startswith('/'):
                icon = join(tagsDir, icon)
        else:
            iconTmp = join(tagsDir, name)+'.png'
            if isfile(iconTmp):
                icon = iconTmp
        self.icon = icon
        self.eventTypes = eventTypes
        self.usage = 0
    __repr__ = lambda self: 'TagIconItem(%r, desc=%r, icon=%r, eventTypes=%r)'%(self.name, self.desc, self.icon, self.eventTypes)


eventTags = (
    TagIconItem('birthday', eventTypes=('yearly',)),
    TagIconItem('marriage', desc=_('Marriage'), eventTypes=('yearly',)),
    TagIconItem('obituary', eventTypes=('yearly',)),
    TagIconItem('note', eventTypes=('dailyNote',)),
    TagIconItem('task', eventTypes=('task',)),
    TagIconItem('alarm'),
    TagIconItem('business'),
    TagIconItem('personal'),
    TagIconItem('favorite'),
    TagIconItem('important'),
    TagIconItem('appointment', eventTypes=('task',)),
    TagIconItem('meeting', eventTypes=('task',)),
    TagIconItem('phone_call', desc='Phone Call', eventTypes=('task',)),
    TagIconItem('university', eventTypes=('task',)),## FIXME
    TagIconItem('education'),
    TagIconItem('holiday'),
    TagIconItem('travel'),
)

getEventTagsDict = lambda: dict([(tagObj.name, tagObj) for tagObj in eventTags])
eventTagsDesc = dict([(t.name, t.desc) for t in eventTags])

###################
for fname in os.listdir(join(srcDir, 'accounts')):
    name, ext = splitext(fname)
    if ext == '.py' and name != '__init__':
        try:
            __import__('scal2.accounts.%s'%name)
        except:
            core.myRaiseTback()
#print 'accounts', event_man.classes.account.names
###########
eventAccounts = event_man.EventAccountsHolder()
eventGroups = event_man.EventGroupsHolder()
eventTrash = event_man.EventTrash()
#### Load accounts, groups and trash? FIXME
eventAccounts.load()
eventGroups.load()
eventTrash.load()
####
event_man.saveLastIds()



try:
    event_man.checkAndStartDaemon()## FIXME here or in ui_*/event/main.py
except:
    print 'Error while starting daemon'
    myRaise()


newGroups = []## list of groupId's
changedGroups = []## list of groupId's
newEvents = []## a list of (groupId, eventId) 's
changedEvents = []## a list of (groupId, eventId) 's
trashedEvents = []## a list of (groupId, eventId) 's



#def updateEventTagsUsage():## FIXME where to use?
#    tagsDict = getEventTagsDict()
#    for tagObj in eventTags:
#        tagObj.usage = 0
#    for event in events:## FIXME
#        for tag in event.tags:
#            try:
#                tagsDict[tag].usage += 1
#            except KeyError:
#                pass


###################
core.loadAllPlugins()## FIXME
###################
## BUILD CACHE AFTER SETTING core.primaryMode
maxDayCacheSize = 100 ## maximum size of cellCache (days number)
maxWeekCacheSize = 12

cellCache = CellCache()
todayCell = cell = cellCache.getTodayCell() ## FIXME
###########################
autoLocale = True
logo = '%s/starcal2.png'%pixDir
comDeskDir = '%s/.config/autostart'%homeDir
comDesk = '%s/%s.desktop'%(comDeskDir, APP_NAME)
#kdeDesk='%s/.kde/Autostart/%s.desktop'%(homeDir, APP_NAME)
###########################
#themeDir = join(rootDir, 'themes')
#theme = None
########################### Options ###########################
keyDelay = 0 #0.07 ## delay between listening of key press in calendar
winWidth = 480
calHeight = 250
winTaskbar = False
#showDigClockTb = True ## On Toolbar ## FIXME
showDigClockTr = True ## On Tray
####
toolbarItems = []
toolbarIconSize = 'Large Toolbar'
toolbarIconSizePixel = 24 ## used in pyqt ui
toolbarStyle = 'Icon'
####
bgColor = (26, 0, 1, 255)## or None
bgUseDesk = False
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255) ## text of weekDays and weekNumbers
#menuBgColor = borderColor ##???????????????
menuTextColor = None##borderTextColor##???????????????
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor  = (0, 255, 0, 50)
cursorFixed = False
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
cursorD = 3.0
cursorR = 7.0 ## Rounded Rectangle
cursorCornerOval = False ## Apply in Pref? FIXME
cursorW = 57
cursorH = 24
calGrid = True
gridColor = (255, 252, 0, 82)
calLeftMargin = 30
calTopMargin = 30
boldYmLabel = True ##Apply in Pref FIXME
showYmArrows = True ##Apply in Pref FIXME
labelMenuDelay = 0.1 ## delay for shift up/down items of menu for right click on YearLabel
####################
trayImage = join(pixDir, 'tray-green.png')
trayImageHoli = join(pixDir, 'tray-red.png')
trayBgColor = (-1, -1, -1, 0) ## how to get bg color of gnome panel ????????????
trayTextColor = (0, 0, 0)
traySize = 22
trayFont = None
trayY0 = None

'''
trayImage = join(pixDir, 'tray-dark.png')
trayImageHoli = join(pixDir, 'tray-dark.png')
trayBgColor = (0, 0, 0, 0) ## how to get bg color of gnome panel ????????????
trayTextColor = (255, 255, 255)
traySize = 21
trayFont = None
trayY0 = 4
'''

####################
menuActiveLabelColor = "#ff0000"
pluginsTextTray = False
pluginsTextInsideExpander = True
pluginsTextIsExpanded = True ## affect only if pluginsTextInsideExpander
####################
dragGetMode = core.DATE_GREG  ##Apply in Pref - FIXME
#dragGetDateFormat = '%Y/%m/%d'
dragRecMode = core.DATE_GREG  ##Apply in Pref - FIXME
dragIconCell = False
####################
monthRMenuNum = True
#monthRMenu
prefPagesOrder = (0, 1, 2, 3)
showWinController = True
####################
winKeepAbove = True
winSticky = True
winX = 0
winY = 0
fontUseDefault = True
fontDefault = ('Sans', False, False, 12)
fontCustom = None
#####################
weekCalTextColor = (255, 255, 255)
#####################
showMain = True ## Show main window on start (or only goto tray)
#####################
mainWinItems = (
    ('toolbar', True),
    ('labelBox', True),
    ('monthCal', True),
    ('statusBar', True),
    ('pluginsText', True),
    ('eventDayView', True),
)

mainWinItemsDefault = mainWinItems[:]

ntpServers = (
    'pool.ntp.org',
    'asia.pool.ntp.org',
    'europe.pool.ntp.org',
    'north-america.pool.ntp.org',
    'oceania.pool.ntp.org',
    'south-america.pool.ntp.org',
    'ntp.ubuntu.com'
)


#####################
#dailyNoteChDateOnEdit = True ## change date of a dailyNoteEvent when editing it
eventManShowDescription = True
#####################
focusTime = 0
lastLiveConfChangeTime = 0


sysConfPath = join(sysConfDir, 'ui.conf') ## also includes LIVE config
if os.path.isfile(sysConfPath):
    try:
        exec(open(sysConfPath).read())
    except:
        myRaise(__file__)

confPath = join(confDir, 'ui.conf')
if os.path.isfile(confPath):
    try:
        exec(open(confPath).read())
    except:
        myRaise(__file__)

saveLiveConfDelay = 0.5 ## seconds
confPathLive = join(confDir, 'ui-live.conf')
if os.path.isfile(confPathLive):
    try:
        exec(open(confPathLive).read())
    except:
        myRaise(__file__)
################################

try:
    version
except NameError:
    prefVersion = ''
else:
    prefVersion = version
    del version

shownCalsNum = len(shownCals)

newPrimaryMode = shownCals[0]['mode']
if newPrimaryMode!= core.primaryMode:
    core.primaryMode = newPrimaryMode
    cellCache.clear()
del newPrimaryMode

## monthcal:


needRestartPref = {} ### Right place ????????
for key in ('scal2.locale_man.lang', 'winTaskbar', 'showYmArrows'): # What other????
    needRestartPref[key] = eval(key)

if menuTextColor is None:
    menuTextColor = borderTextColor

##################################

mainWin = None
prefDialog = None
eventManDialog = None
timeLineWin = None
weekCalWin = None







