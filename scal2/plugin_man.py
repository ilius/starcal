# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import sys
from time import strftime
from os.path import isfile, dirname, join, split, splitext


from scal2.cal_modules import modules, moduleNames, modNum, jd_to, to_jd, convert
from scal2.locale_man import numLocale, getMonthName
from scal2.paths import *

try:
    import logging
    log = logging.getLogger('starcal2')
except:
    from scal2.utils import FallbackLogger
    log = FallbackLogger()

def myRaise(File=__file__):
    i = sys.exc_info()
    log.error('File "%s", line %s: %s: %s\n'%(File, i[2].tb_lineno, i[0].__name__, i[1]))

def pluginException(name):
    i = sys.exc_info()
    log.error('error in plugin %s, %s: %s\n'%(name, i[0].__name__, i[1]))


icsTmFormat = '%Y%m%dT%H%M%SZ'
icsHeader = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
'''



class BasePlugin:
    __repr__ = lambda self: 'loadPlugin(%r, enable=%r, show_date=%r)'%(self.path, self.enable, self.show_date)
    def __init__(self, path, mode=0, desc='', enable=True, show_date=False,
                 about=None, authors=[], has_config=False, has_image=False, last_day_merge=True):
        self.external = False
        self.path = path
        if mode==None or isinstance(mode, int):
            self.mode = mode
        else:
            try:
                self.mode = moduleNames.index(mode)
            except ValueError:
                log.error('Plugin "%s" needs calendar module "%s" that is not loaded!\n'%(path, mode))
                self.mode = None
        self.desc = desc
        self.enable = enable
        self.show_date = show_date
        self.about = about
        self.authors = authors
        self.has_config = has_config
        self.has_image = has_image
        self.last_day_merge = last_day_merge
        #########
        self.text = ''
        self.holiday = False
        self.load()
    def clear(self):
        pass
    def load(self):
        pass
    def get_text(self, year, month, day):
        return ''
    def update_cell(self, c):
        (y, m, d) = c.dates[self.mode]
        text = ''
        t = self.get_text(y, m, d)
        if t!='':
            text += t
        if self.last_day_merge and d>=modules[self.mode].minMonthLen:## and d<=modules[self.mode].maxMonthLen:
            (ny, nm, nd) = jd_to(c.jd+1, self.mode)
            if nm>m or ny>y:
                nt = self.get_text(y, m, d+1)
                if nt!='':
                    text += nt
        if text!='':
            if c.extraday!='':
                c.extraday += '\n'
            c.extraday += text    
    def exportToIcs(self, fileName, startJd, endJd):
        currentTimeStamp = strftime(icsTmFormat)
        self.load() ## FIXME
        mode = self.mode
        icsText = icsHeader
        for jd in range(startJd, endJd):
            (myear, mmonth, mday) = jd_to(jd, mode)
            dayText = self.get_text(myear, mmonth, mday)
            if dayText:
                (gyear, gmonth, gday) = jd_to(jd, DATE_GREG)
                (gyear_next, gmonth_next, gday_next) = jd_to(jd+1, DATE_GREG)
                #######
                icsText += 'BEGIN:VEVENT\n'
                icsText += 'CREATED:%s\n'%currentTimeStamp
                icsText += 'LAST-MODIFIED:%s\n'%currentTimeStamp
                icsText += 'DTSTART;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear, gmonth, gday)
                icsText += 'DTEND;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear_next, gmonth_next, gday_next)
                icsText += 'SUMMARY:%s\n'%dayText
                icsText += 'END:VEVENT\n'
        icsText += 'END:VCALENDAR\n'
        open(fileName, 'w').write(icsText)


def loadExternalPlugin(path, enable=True, show_date=True):
    if not isfile(path):
        log.error('plugin file "%s" not found! maybe removed?'%path)
        #try:
        #    plugIndex.remove(
        return None #?????????????????????????
        ##plug = BasePlugin(path, 0, 'Failed to load plugin', enable, show_date)
        ##plug.external = True
        ##return plug
    fname = split(path)[1]
    direc = dirname(path)
    name = splitext(fname)[0]
    sys.path.insert(0, direc)
    try:
        mod = __import__(name)
    except:
        pluginException(name)
        return None
    finally:
        sys.path.pop(0)
    ## mod.module_init(rootDir, ) ## FIXME
    try:
        return mod.TextPlug(enable=enable, show_date=show_date)
    except:
        pluginException(name)
        #print dir(mod)
        return None

class ExternalPlugin(BasePlugin):
    def __init__(self, path, enable=True, show_date=False, **params):
        BasePlugin.__init__(self, path, enable=enable, show_date=show_date)
        self.params = params
        self.external = True
        self.module = None
        self.extender = None
        self.isLoaded = False
    def lateLoad(self):
        if not isfile(self.path):
            return False
        fname = split(self.path)[1]
        direc = dirname(self.path)
        name = splitext(fname)[0]
        sys.path.insert(0, direc)
        self.module = __import__(name)
        sys.path.pop(0)
        ###
        params = self.params
        params['rootDir'] = rootDir
        self.module.module_init(self, params) ## FIXME
        self.isLoaded = True
        return True
    def open_configure(self):
        pass
    def open_about(self):
        pass

class HolidayPlugin(BasePlugin):
    def __init__(self, path, enable=None, show_date=None):
        default_enable = True
        default_show_date = False
        exec(open(path).read())
        #execfile(path)
        if enable==None:
            enable = default_enable
        if show_date==None:
            show_date = default_show_date
        BasePlugin.__init__(self, path, None, desc, enable, show_date,
            about, authors, has_config, False)
        self.holidays = {}
        for modeName in holidays.keys():## .keys() in not neccesery
            try:
                mode = moduleNames.index(modeName)
            except ValueError:
                continue
            self.holidays[mode] = holidays[modeName]
    def update_cell(self, c):
        if not c.holiday:
            for mode in self.holidays.keys():## .keys() in not neccesery
                (y, m, d) = c.dates[mode]
                for (hm, hd) in self.holidays[mode]:
                    if m==hm:
                        if d==hd:
                            c.holiday = True
                            break
                        elif d==hd-1 and hd>=modules[mode].minMonthLen:
                            (ny, nm, nd) = jd_to(c.jd+1, mode)
                            if nm>m or ny>y:
                                c.holiday = True
                                break
    def exportToIcs(self, fileName, startJd, endJd):
        currentTimeStamp = strftime(icsTmFormat)
        icsText = icsHeader
        for jd in range(startJd, endJd):
            isHoliday = False
            for mode in self.holidays.keys():
                (myear, mmonth, mday) = jd_to(jd, mode)
                if (mmonth, mday) in self.holidays[mode]:
                    isHoliday = True
                    break
            if isHoliday:
                (gyear, gmonth, gday) = jd_to(jd, DATE_GREG)
                (gyear_next, gmonth_next, gday_next) = jd_to(jd+1, DATE_GREG)
                #######
                icsText += 'BEGIN:VEVENT\n'
                icsText += 'CREATED:%s\n'%currentTimeStamp
                icsText += 'LAST-MODIFIED:%s\n'%currentTimeStamp
                icsText += 'DTSTART;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear, gmonth, gday)
                icsText += 'DTEND;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear_next, gmonth_next, gday_next)
                icsText += 'CATEGORIES:Holidays\n'
                icsText += 'TRANSP:TRANSPARENT\n'
                ## TRANSPARENT because being in holiday time, does not make you busy!
                ## see http://www.kanzaki.com/docs/ical/transp.html
                icsText += 'SUMMARY:%s\n'%_('Holiday')
                icsText += 'END:VEVENT\n'
        icsText += 'END:VCALENDAR\n'
        open(fileName, 'w').write(icsText)






class BuiltinTextPlugin(BasePlugin):
    def __init__(self, path, enable=None, show_date=None):
        default_enable = True
        default_show_date = False
        exec(open(path).read())
        #execfile(path)
        if enable==None:
            enable = default_enable
        if show_date==None:
            show_date = default_show_date
        self.db_path = dirname(path)+'/'+db_name
        BasePlugin.__init__(self, path, mode, desc, enable, show_date,
            about, authors, has_config, has_image)
    def clear(self):
        self.data = []
    def load(self):
        db = []
        for j in xrange(12):
                monthDb=[]
                for k in xrange(modules[self.mode].maxMonthLen):
                    monthDb.append('')
                db.append(monthDb)
        ## last item is a dict of dates (y, m, d) and the description of day:
        db.append({})
        ext = splitext(self.db_path)[1]
        if ext=='.xml':
                tmp = parse(self.db_path).documentElement
                db_xml=tmp.getElementsByTagName('day')
                for record in db_xml:
                    for element in record.childNodes:
                        if element.nodeType != element.TEXT_NODE:
                            if element.nodeType != element.TEXT_NODE:
                                name, data = _get_text(element)
                                if name=='num':
                                    sp=data.split('/')
                                    find = True
                                if name=='desc' and find:
                                    if len(sp)==2:
                                        try:
                                            m = int(sp[0])
                                            d = int(sp[1])
                                            db[m-1][d-1] = data
                                        except:
                                            myRaise()
                                    elif len(sp)==3:
                                        try:
                                            y = int(sp[0])
                                            m = int(sp[1])
                                            d = int(sp[2])
                                            db[12][(y,m,d)] = data
                                        except:
                                            myRaise()
                                    find = False
        elif ext=='.titled':## Titled text db (used for Owghat)
                sep = '\t'
                lines = open(self.db_path).read().split('\n')
                year = 0
                month = 1
                day = 1
                heads = lines[0].split('\t')
                n = len(heads)
                for line in lines[1:]:
                    if line=='':
                        continue
                    if line[0]=='#':
                        continue
                    parts = line.split('\t')
                    assert len(parts)==n
                    date = parts[0].split('/')
                    if len(date)==3:
                        year = int(date[0])
                        month = int(date[1])
                        day = int(date[2])
                    elif len(date)==2:
                        month = int(date[0])
                        day = int(date[1])
                    elif len(date)==1:
                        day = int(date[0])
                    else:
                        raise IOError, 'Bad line in database %s:\n%s'%(db_file, line)
                    tp = []
                    for j in xrange(1, n):#????????????????????
                        tp.append('%s: %s'%(heads[j], parts[j]))
                    db[12][(year, month, day)] = sep.join(tp)
        elif ext in ('.txt', '.db'):
                sep = '\t'
                lines = open(self.db_path).read().split('\n')
                for line in lines[1:]:
                    if line=='':
                        continue
                    if line[0]=='#':
                        continue
                    parts = line.split('\t')
                    if len(parts)<2:
                        continue
                    date = parts[0].split('/')
                    text = '\t'.join(parts[1:])
                    if len(date)==3:
                        y = int(date[0])
                        m = int(date[1])
                        d = int(date[2])
                        db[12][(y, m, d)] = text
                    elif len(date)==2:
                        m = int(date[0])
                        d = int(date[1])
                        db[m-1][d-1] = text
                    else:
                        raise IOError, 'Bad line in database %s:\n%s'%(self.db_path, line)
        self.data = db
    def get_text(self, year, month, day):
        db = self.data
        if db==None:
            return ''
        mode = self.mode
        text = ''
        #if mode!=primaryMode:
        #    (year, month, day) = convert(year, month, day, primaryMode, mode)
        try:
            text = db[month-1][day-1]
        except:## KeyError or IndexError
            pass
        else:
            if self.show_date and text!='':
                text = '%s %s: %s'%(numLocale(day), getMonthName(mode, month), text)
        try:
            text2 = db[12][(year, month, day)]
        except:## KeyError or IndexError
            pass
        else:
            if text!='':
                text += '\n'
            if self.show_date:
                text2 = '%s %s %s: %s'%(numLocale(day), getMonthName(mode, month, year), numLocale(year), text2)
                    
            text += text2
        return text
    #def pref_str(self):
        ## (self, path, mode, desc, show_date=False):
        #return '%s("%s", %s, "%s", enable=%s, show_date=%s)'\
        #    %(self.__class__.__name__, self.db_path.replace('"', '\\"'),
        #    self.mode, self.desc.replace('"', '\\"'), self.enable, self.show_date)


#class EveryDayTextPlugin(BasePlugin):


class IcsTextPlugin(BasePlugin):
    def __init__(self, path, enable=True, show_date=False, all_years=False):
        desc = split(path)[1][:-4]
        self.ymd = None
        self.md = None
        self.all_years = all_years
        BasePlugin.__init__(self, path, DATE_GREG, desc, enable, show_date)
        #self.load()
    def clear(self):
        self.ymd = None
        self.md = None
    def load(self):
        lines = open(self.path).read().replace('\r', '').split('\n')
        n = len(lines)
        i = 0
        while True:
            try:
                if lines[i]=='BEGIN:VEVENT':
                    break
            except IndexError:
                log.error('bad ics file "%s"'%self.path)
                return
            i += 1
        SUMMARY		= ''
        DESCRIPTION	= ''
        DTSTART		= None
        DTEND		= None
        if self.all_years:
            md = {}
            while True:
                i += 1
                try:
                    line = lines[i]
                except IndexError:
                    break
                if line=='END:VEVENT':
                    if SUMMARY!='' and DTSTART!=None and DTEND!=None:
                        text = SUMMARY
                        if DESCRIPTION!='':
                            text += '\n%s'%DESCRIPTION
                        for (y, m, d) in ymdRange(DTSTART, DTEND):
                            md[(m, d)] = text
                    else:
                        log.error('unsupported ics event, SUMMARY=%s, DTSTART=%s, DTEND=%s'%(SUMMARY, DTSTART,DTEND))
                    SUMMARY		= ''
                    DESCRIPTION	= ''
                    DTSTART		= None
                    DTEND			= None
                elif line.startswith('SUMMARY:'):
                    SUMMARY = line[8:].replace('\\,', ',').replace('\\n', '\n')
                elif line.startswith('DESCRIPTION:'):
                    DESCRIPTION = line[12:].replace('\\,', ',').replace('\\n', '\n')
                elif line.startswith('DTSTART;'):
                    #if not line.startswith('DTSTART;VALUE=DATE;'):
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    date = line.split(':')[-1]
                    #if len(date)!=8:
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    try:
                        DTSTART = (int(date[:4]), int(date[4:6]), int(date[6:8]))
                    except:
                        log.error('unsupported ics line: %s'%line)
                        myRaise()
                        continue
                elif line.startswith('DTEND;'):
                    #if not line.startswith('DTEND;VALUE=DATE;'):
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    date = line.split(':')[-1]
                    #if len(date)!=8:
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    try:
                        DTEND = (int(date[:4]), int(date[4:6]), int(date[6:8]))
                    except:
                        log.error('unsupported ics line: %s'%line)
                        myRaise()
                        continue
            self.ymd = None
            self.md = md
        else:## not self.all_years
            ymd = {}
            while True:
                i += 1
                try:
                    line = lines[i]
                except IndexError:
                    break
                if line=='END:VEVENT':
                    if SUMMARY!='' and DTSTART!=None and DTEND!=None:
                        text = SUMMARY
                        if DESCRIPTION!='':
                            text += '\n%s'%DESCRIPTION
                        for (y, m, d) in ymdRange(DTSTART, DTEND):
                            ymd[(y, m, d)] = text
                    SUMMARY		= ''
                    DESCRIPTION	= ''
                    DTSTART		= None
                    DTEND			= None
                elif line.startswith('SUMMARY:'):
                    SUMMARY = line[8:].replace('\\,', ',').replace('\\n', '\n')
                elif line.startswith('DESCRIPTION:'):
                    DESCRIPTION = line[12:].replace('\\,', ',').replace('\\n', '\n')
                elif line.startswith('DTSTART;'):
                    #if not line.startswith('DTSTART;VALUE=DATE;'):
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    date = line.split(':')[-1]
                    #if len(date)!=8:
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    try:
                        DTSTART = (int(date[:4]), int(date[4:6]), int(date[6:8]))
                    except:
                        log.error('unsupported ics line: %s'%line)
                        myRaise()
                        continue
                elif line.startswith('DTEND;'):
                    #if not line.startswith('DTEND;VALUE=DATE;'):
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    date = line.split(':')[-1]
                    #if len(date)!=8:
                    #    log.error('unsupported ics line: %s'%line)
                    #    continue
                    try:
                        DTEND = (int(date[:4]), int(date[4:6]), int(date[6:8]))
                    except:
                        log.error('unsupported ics line: %s'%line)
                        myRaise()
                        continue
            self.ymd = ymd
            self.md = None
    def get_text(self, y, m, d):
        if self.ymd!=None:
            if (y, m, d) in self.ymd:
                if self.show_date:
                    return '%s %s %s: %s'%(numLocale(d), getMonthName(self.mode, m),
                        numLocale(y), self.ymd[(y, m, d)])
                else:
                    return self.ymd[(y, m, d)]
        if self.md!=None:
            if (m, d) in self.md:
                if self.show_date:
                    return '%s %s %s: %s'%(numLocale(d), getMonthName(self.mode, m), numLocale(y), self.ymd[(y, m, d)])
                else:
                    return self.md[(m, d)]
        return ''
    def open_configure(self):
        pass
    def open_about(self):
        pass

## class RandomTextPlug: #??????????????



def loadPlugin(path, **kwargs):
    if not path.startswith('/'):
        path = join(plugDir, path)
    if not isfile(path):
        log.error('error while loading plugin "%s": no such file!\n'%path)
        return None
    ext = splitext(path)[1]
    #try:
    if ext=='.spg':
        return BuiltinTextPlugin(path, **kwargs)
    elif ext=='.hol':
        return HolidayPlugin(path, **kwargs)
    elif ext=='.ics':
        return IcsTextPlugin(path, **kwargs)
    elif ext=='.py' or ext=='.so':
        return loadExternalPlugin(path, **kwargs)
    else:
        return None
    #except ImportError:## FIXME
    #    i = sys.exc_info()
    #    log.error('error while loading plugin "%s": %s: %s\n'%(path, i[0].__name__, i[1]))
    #    ### How to get line number of error in plugin file ????????????????
    #    return None

