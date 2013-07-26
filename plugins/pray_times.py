# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux


import sys, os, time, gettext
from os.path import join, isfile, dirname
from math import pi, floor, ceil, sqrt, sin, cos, tan, asin, acos, atan, atan2

_mypath = __file__
if _mypath.endswith('.pyc'):
    _mypath = _mypath[:-1]
dataDir = dirname(_mypath) + '/pray_times_files/'
rootDir = '/usr/share/starcal2'

sys.path.insert(0, dataDir)## FIXME
sys.path.insert(0, rootDir)## FIXME

from scal2 import plugin_api as api

from scal2.path import *
from pray_times_backend import PrayTimes

## DO NOT IMPORT core IN PLUGINS
from scal2.time_utils import floatHourToTime
from scal2.locale_man import tr as _
from scal2.plugin_man import BasePlugin
from scal2.cal_types.gregorian import to_jd as gregorian_to_jd
from scal2.time_utils import getUtcOffsetByJd
#from scal2 import event_lib## needs core!! FIXME

#if 'gtk' in sys.modules:
from pray_times_gtk import *
#else:
#    from pray_times_qt import *

####################################################

confPath = join(plugConfDir, 'pray_times')
earthR = 6370

####################################################




####################### Methods and Classes ##################
sind = lambda x: sin(pi/180.0*x)
cosd = lambda x: cos(pi/180.0*x)
#tand = lambda x: tan(pi/180.0*x)
#asind = lambda x: asin(x)*180.0/pi
#acosd = lambda x: acos(x)*180.0/pi
#atand = lambda x: atan(x)*180.0/pi
#loc2hor = lambda z, delta, lat: acosd((cosd(z)-sind(delta)*sind(lat))/cosd(delta)/cosd(lat))/15.0

def earthDistance(lat1, lng1, lat2, lng2):
    #if lat1==lat2 and lng1==lng2:
    #    return 0
    dx = lng2 - lng1
    if dx<0:
        dx += 360
    if dx>180:
        dx = 360-dx
    ####
    dy = lat2 - lat1
    if dy<0:
        dy += 360
    if dy>180:
        dy = 360-dy
    ####
    deg = acos(cosd(dx)*cosd(dy))
    if deg>pi:
        deg = 2*pi-deg
    return deg*earthR
    #return ang*180/pi

'''
event_classes = api.get('event_lib', 'classes')
EventRule = api.get('event_lib', 'EventRule')

@event_classes.rule.register
class PrayTimeEventRule(EventRule):
    plug = None ## FIXME
    name = 'prayTime'
    desc = _('Pray Time')
    provide = ('time',)
    need = ()
    conflict = ('dayTimeRange', 'cycleLen',)
    def __init__(self, parent):
        EventRule.__init__(self, parent)
    def calcOccurrence(self, startEpoch, endEpoch, event):
        self.plug.get_times_jd(jd)
    getInfo = lambda self: self.desc
'''

class TextPlug(BasePlugin, TextPlugUI):
    ## all options (except for "enable" and "show_date") will be saved in file confPath
    def __init__(self, enable=True, show_date=False):
        #print '----------- praytime TextPlug.__init__'
        #print 'From plugin: core.VERSION=%s'%api.get('core', 'VERSION')
        #print 'From plugin: core.aaa=%s'%api.get('core', 'aaa')
        BasePlugin.__init__(
            self,
            path=_mypath,
            mode='gregorian',
            desc=_('Islamic Pray Times'),
            enable=enable,
            show_date=show_date,
            last_day_merge=False,
        )
        self.external = True
        self.name = _('Islamic Pray Times')
        self.about = _('Islamic Pray Times') ## FIXME
        self.has_config = True
        ##############
        ## here load config ## FIXME
        locName = 'Tehran'
        lat = 35.705
        lng = 51.4216
        method = 'Tehran'
        imsak = 10 ## minutes before Fajr (Morning Azan)
        #asrMode=ASR_STANDARD
        #highLats='NightMiddle'
        #timeFormat='24h'
        shownTimeNames = ('fajr', 'sunrise', 'dhuhr', 'maghrib', 'midnight')
        sep = '     '
        ####
        if isfile(confPath):
            exec(open(confPath).read())
        #######
        self.locName = locName
        self.imsak = imsak
        self.ptObj = PrayTimes(lat, lng, methodName=method, imsak='%d min'%imsak)
        self.shownTimeNames = shownTimeNames
        self.sep = sep
        #######
        #PrayTimeEventRule.plug = self
        #######
        self.makeWidget()## FIXME
    def saveConfig(self):
        text = 'locName=%r\n'%self.locName
        text += 'lat=%r\n'%self.ptObj.lat
        text += 'lng=%r\n'%self.ptObj.lng
        text += 'method=%r\n'%self.ptObj.method.name
        text += 'shownTimeNames=%r\n'%self.shownTimeNames
        text += 'imsak=%r\n'%self.imsak
        text += 'sep=%r\n'%self.sep
        open(confPath, 'w').write(text)
    #def date_change_after(self, widget, year, month, day):
    #    self.dialog.menuCell.add(self.menuitem)
    #    self.menu_unmap_id = self.dialog.menuCell.connect('unmap', self.menu_unmap)
    #def menu_unmap(self, menu):
    #    menu.remove(self.menuitem)
    #    menu.disconnect(self.menu_unmap_id)
    def get_times_jd(self, jd):
        times = self.ptObj.getTimesByJd(
            jd,
            getUtcOffsetByJd(jd)/3600.0,
        )
        return [(name, times[name]) for name in self.shownTimeNames]
    def getFormattedTime(self, tm):## tm is float hour
        try:
            h, m, s = floatHourToTime(float(tm))
        except ValueError:
            return tm
        else:
            return '%d:%.2d'%(h, m)
    def get_text_jd(self, jd):
        return self.sep.join([
            '%s: %s'%(_(name.capitalize()), self.getFormattedTime(tm))
            for name, tm in self.get_times_jd(jd)
        ])
    def get_text(self, year, month, day):## just for compatibity (usage by external programs)
        return self.get_text_jd(gregorian_to_jd(year, month, day))
    def update_cell(self, c):
        text = self.get_text_jd(c.jd)
        if text!='':
            if c.pluginsText!='':
                c.pluginsText += '\n'
            c.pluginsText += text


if __name__=='__main__':
    #sys.path.insert(0, '/usr/share/starcal2')
    #from scal2 import core
    #from scal2.locale_man import rtl
    #if rtl:
    #    gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
    dialog = LocationDialog()
    dialog.connect('delete-event', gtk.main_quit)
    #dialog.connect('response', gtk.main_quit)
    dialog.resize(600, 600)
    print dialog.run()
    #gtk.main()




