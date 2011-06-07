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

sys.path.insert(0, dataDir) ## FIXME
sys.path.insert(0, rootDir) ## FIXME


from scal2.paths import *
from pray_times_backend import PrayTimes

## DO NOT IMPORT core IN PLUGINS
from scal2.locale_man import tr as _
from scal2.plugin_man import BasePlugin
from scal2.cal_modules.gregorian import to_jd as gregorian_to_jd

from pray_times_qt import *
'''
try:
    import gtk
except ImportError:
    from pray_times_qt import *
else:
    from pray_times_gtk import *
'''

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
    
def hms(x):
    (days, s) = divmod(int(x), 24*3600)
    (m, s) = divmod(s, 60)
    (h, m) = divmod(m, 60)
    return '%d:%.2d:%.2d'%(h, m, s)

def hm(x):
    (days, m) = divmod(int(x/60), 24*60)
    (h, m) = divmod(m, 60)
    return '%d:%.2d'%(m, s)



class TextPlug(BasePlugin, TextPlugUI):
    ## all options (except "enable" and "show_date") will be saved in file confPath
    def __init__(self, enable=True, show_date=False):
        BasePlugin.__init__(self, path=_mypath, mode='gregorian', desc=_('Islamic Pray Times'),
                            enable=enable, show_date=show_date, last_day_merge=False)
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
        ####
        if isfile(confPath):
            exec(open(confPath).read())
        #######
        self.locName = locName
        self.imsak = imsak
        self.ptObj = PrayTimes(lat, lng, methodName=method, imsak='%d min'%imsak)
        self.shownTimeNames = shownTimeNames
        ###
        self.makeWidget()
    def saveConfig(self):
        text = 'locName=%r\n'%self.locName
        text += 'lat=%r\n'%self.ptObj.lat
        text += 'lng=%r\n'%self.ptObj.lng
        text += 'method=%r\n'%self.ptObj.method.name
        text += 'shownTimeNames=%r\n'%self.shownTimeNames
        text += 'imsak=%r\n'%self.imsak
        open(confPath, 'w').write(text)
    #def date_change_after(self, widget, year, month, day):
    #    self.dialog.menuCell.add(self.menuitem)
    #    self.menu_unmap_id = self.dialog.menuCell.connect('unmap', self.menu_unmap)
    #def menu_unmap(self, menu):
    #    menu.remove(self.menuitem)
    #    menu.disconnect(self.menu_unmap_id)
    def get_text_jd(self, jd):
        times = self.ptObj.getTimesByJd(jd)
        return '\t'.join(['%s: %s'%(_(name.capitalize()), times[name]) for name in self.shownTimeNames])
    def get_text(self, year, month, day):## just for compatibity (usage by external programs)
        return self.get_text_jd(gregorian_to_jd(year, month, day))
    def update_cell(self, c):
        text = self.get_text_jd(c.jd)
        if text!='':
            if c.extraday!='':
                c.extraday += '\n'
            c.extraday += text    


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
    



