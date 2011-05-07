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

import sys, os, os.path
from os import listdir
from os.path import dirname, join, isfile
from xml.dom.minidom import parse

from scal2.utils import NullObj
from scal2.paths import *

import scal2.locale_man
from scal2.locale_man import tr as _

from scal2 import core
from scal2.core import myRaise, getMonthLen, getNextMonth, getPrevMonth

#from scal2 import event_man

null = NullObj()

invertColor = lambda r, g, b: (255-r, 255-g, 255-b)
## htmlColorToGdk=lambda hc: gdk.Color(int(hc[1:3], 16)*256, int(hc[3:5], 16)*256, int(hc[5:7], 16)*256)
## htmlColorToGdk = lambda hc: gdk.color_parse(hc)

def getElementText(el):
    rc = u''
    name = el.nodeName
    for node in el.childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return (name, rc.strip())

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
            st=st[:-2]+'})'
        else:
            st=st[:-2]+'},'
    return st

def saveLiveConf():
    text = ''
    for key in ('winX', 'winY', 'winWidth', 'winKeepAbove', 'winSticky', 'extraTextIsExpanded', 'bgColor'):
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

#######################################################################


class Cell:## status and information of a cell
    def __init__(self, jd):
        self.customday = None
        self.extraday = ''
        ###
        self.jd = jd
        date = core.jd_to(jd, core.primaryMode)
        (self.year, self.month, self.day) = date
        self.weekDay = core.jwday(jd)
        self.holiday = (self.weekDay in core.holidayWeekDays)
        self.holidayExtra = self.holiday
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
                plug.update_cell(self)
    def format(self, binFmt, mode, tm=null):## FIXME
        (pyFmt, funcs) = binFmt
        return pyFmt%tuple(f(self, mode, tm) for f in funcs)


class CellCache:
    def __init__(self):
        self.jdCells = {} ## a mapping from julan_day to Cell instance
        self.plugins = {}
    def clear(self):
        global cell, todayCell
        self.jdCells = {}
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
            'getCellGroupCallable': getCellGroupCallable
        }
        for local_cell in self.jdCells.values():
            setParamsCallable(local_cell)
    def getCell(self, jd):
        if self.jdCells.has_key(jd):
            return self.jdCells[jd]
        else:
            return self.buildCell(jd)
    getCellByDate = lambda self, year, month, day: self.getCell(core.to_jd(year, month, day, core.primaryMode))
    getTodayCell = lambda self: self.getCell(core.getCurrentJd())
    def getCellByDate(self, year, month, day):
        return self.getCell(core.to_jd(year, month, day, core.primaryMode))
    def buildCell(self, jd):
        local_cell = Cell(jd)
        for pluginData in self.plugins.values():
            pluginData['setParamsCallable'](local_cell)
        self.jdCells[jd] = local_cell
        #########
        ## too bad performance! and replace with events ## FIXME
        if customDB:
            for item in customDB:## month, day, type, desc
                if item['month'] == local_cell.month and item['day'] == local_cell.day:
                    local_cell.customday = {'type': item['type'], 'desc': item['desc']}
        #########
        ## Clean Cache
        n = len(self.jdCells)
        if n >= maxCache > 2:
            keys = sorted(self.jdCells.keys())
            if keys[n//2] < jd:
                rm = keys[0]
            else:
                rm = keys[-1]
            self.jdCells.pop(rm)
        #########
        return local_cell
    def getCellGroup(self, pluginName, *args):
        return self.plugins[pluginName]['getCellGroupCallable'](self, *args)

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

######################################################################

def loadCustomDB():
    global customDB
    if not isfile(customFile):
        customDB = None
        return
    db = parse(customFile).documentElement.getElementsByTagName('day')
    customDB = []
    for record in db:
        item = {}
        for element in record.childNodes:
            if element.nodeType != element.TEXT_NODE:
                if element.nodeType != element.TEXT_NODE:
                    name, data = getElementText(element)
                    if name=='num':
                        sp = data.split('/')
                        item['month'] = int(sp[0])
                        item['day'] = int(sp[1])
                    elif name=='kind':
                        item['type'] = int(data)
                    elif name=='desc':
                        item['desc'] = data
        customDB.append(item)


def loadEvents():
    from scal2 import event_man
    global events
    events = event_man.loadEvents()


######################################################################
shownCals = [
    {'enable':True, 'mode':0, 'x':0,  'y':-2, 'font':None, 'color':(220, 220, 220)}, 
    {'enable':True, 'mode':1, 'x':18, 'y':5,  'font':None, 'color':(165, 255, 114)}, 
    {'enable':True, 'mode':2, 'x':-18,'y':4,  'font':None, 'color':(0, 200, 205)}
]
core.primaryMode = shownCals[0]['mode']
################################
customFile = join(confDir, 'customday.xml') ## FIXME
customdayModes=(
    (_('Birthday'),         'tags/birthday.png'),
    (_('Marriage Jubilee'), 'tags/marriage.png'),
    (_('Obituary'),         'tags/obituary.png'),
    (_('Note'),             'tags/note.png'),
    (_('Task'),             'tags/task.png'),
    (_('Alarm'),            'tags/alarm.png')
)
customdayShowIcon = True ## FIXME
###################
tagsDir = join(pixDir, 'tags')

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
    TagIconItem('marriage', desc=_('Marriage Jubilee'), eventTypes=('yearly',)),
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
    TagIconItem('school'),
    TagIconItem('education'),
    TagIconItem('holiday'),
    TagIconItem('travel'),
)

getEventTagsDict = lambda: dict([(tagObj.name, tagObj) for tagObj in eventTags])
eventTagsDesc = dict([(t.name, t.desc) for t in eventTags])

###################
customDB = []
loadCustomDB()
events = []

def updateEventTagsUsage():
    tagsDict = getEventTagsDict()
    for tagObj in eventTags:
        tagObj.usage = 0
    for event in events:
        for tag in event.tags:
            try:
                tagsDict[tag].usage += 1
            except KeyError:
                pass


###################
## BUILD CACHE AFTER SETTING core.primaryMode
maxCache = 100 ## maximum size of cellCache (days number, not months number)
cellCache = CellCache()
todayCell = cell = cellCache.getTodayCell() ## FIXME
###########################
autoLocale = True
logo = '%s/starcal2.png'%pixDir
comDesk='%s/.config/autostart/starcal2.desktop'%homeDir
#kdeDesk='%s/.kde/Autostart/starcal2.desktop'%homeDir
###########################
#themeDir = join(rootDir, 'themes')
#theme = None
########################### Options ###########################
keyDelay 	= 0 #0.07 ## delay between listening of key press in calendar
winWidth	= 480
calHeight   = 250
winTaskbar	= False
#showDigClockTb	= True ## On Toolbar ## FIXME
showDigClockTr	= True ## On Tray
####
toolbarItems = []
toolbarIconSize = 'Large Toolbar'
toolbarIconSizePixel = 24 ## used in pyqt ui
toolbarStyle = 'Icon'
####
bgColor		= (26, 0, 1, 255)## or None
bgUseDesk 	= False
borderColor	= (123, 40, 0, 255)
borderTextColor	= (255, 255, 255, 255) ## text of weekDays and weekNumbers
#menuBgColor	= borderColor ##???????????????
menuTextColor	= None##borderTextColor##???????????????
holidayColor	= (255, 160, 0, 255)
inactiveColor	= (255, 255, 255, 115)
cursorFixed = False
cursorOutColor	= (213, 207, 0, 255)
cursorBgColor	= (41, 41, 41, 255)
cursorD 	= 3.0
cursorR		= 7.0 ## Rounded Rectangle
cursorCornerOval = False ## Apply in Pref? FIXME
cursorW 	= 57
cursorH		= 24
calGrid 	= True
gridColor 	= (255, 252, 0, 82)
calLeftMargin 	= 30
calTopMargin 	= 30
boldYmLabel	= True	##Apply in Pref FIXME
showYmArrows	= True	##Apply in Pref FIXME
labelMenuDelay = 0.1 ## delay for shift up/down items of menu for right click on YearLabel
trayImage	= join(pixDir, 'tray-green.png')
trayImageHoli	= join(pixDir, 'tray-red.png')
trayBgColor	= (-1, -1, -1, 0) ## how to get bg color of gnome panel ????????????
trayTextColor	= (0, 0, 0)
traySize	= 22
trayFont	= None
trayY0		= None
menuActiveLabelColor = "#ff0000"
extradayTray = False
extraTextInsideExpander = True
extraTextIsExpanded = True ## affect only if extraTextInsideExpander
####################
dragGetMode	= core.DATE_GREG  ##Apply in Pref - FIXME
#dragGetDateFormat = '%Y/%m/%d'
dragRecMode	= core.DATE_GREG  ##Apply in Pref - FIXME
dragIconCell	= False
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
    ('extraText', True),
    ('customDayText', True)
)

#####################
dailyNoteChDateOnEdit = True ## change date of a dailyNoteEvent when editing it
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

needRestartPref = {} ### Right place ????????
for key in ('scal2.locale_man.lang', 'winTaskbar', 'showYmArrows'): # What other???? 
    needRestartPref[key] = eval(key)

if menuTextColor is None:
    menuTextColor = borderTextColor

