#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
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
import os
from os.path import join, split, dirname, isfile, isdir
from time import time as now
import json

from collections import OrderedDict

import shutil
import re

from scal3.path import confDir as newConfDir
from scal3.os_utils import makeDir
from scal3.json_utils import dataToPrettyJson
from scal3.s_object import saveBsonObject

oldConfDir = newConfDir.replace('starcal3', 'starcal2')


def loadConf(confPath):
    if not isfile(confPath):
        return
    try:
        text = open(confPath).read()
    except Exception as e:
        print('failed to read file %r: %s'%(confPath, e))
        return
    #####
    data = OrderedDict()
    exec(text, {}, data)
    return data

def loadCoreConf():
    confPath = join(oldConfDir, 'core.conf')
    #####
    def loadPlugin(fname, **data):
        data['_file'] = fname
        return data
    try:
        text = open(confPath).read()
    except Exception as e:
        print('failed to read file %r: %s'%(confPath, e))
        return
    ######
    text = text.replace('calTypes.activeNames', 'activeCalTypes')
    text = text.replace('calTypes.inactiveNames', 'inactiveCalTypes')
    ######
    data = OrderedDict()
    exec(text, {
        'loadPlugin': loadPlugin
    }, data)
    return data

def loadUiCustomizeConf():
    confPath = join(oldConfDir, 'ui-customize.conf')
    #####
    if not isfile(confPath):
        return
    #####
    try:
        text = open(confPath).read()
    except Exception as e:
        print('failed to read file %r: %s'%(confPath, e))
        return
    #####
    text = re.sub('^ui\.', '', text, flags=re.M)
    text = re.sub('^ud\.', 'ud__', text, flags=re.M)
    ######
    data = OrderedDict()
    exec(text, {}, data)
    data['wcal_toolbar_mainMenu_icon'] = 'starcal-24.png'
    return data


def writeJsonConf(name, data):
    if data is None:
        return
    fname = name + '.json'
    jsonPath = join(newConfDir, fname)
    text = dataToPrettyJson(data)
    try:
        open(jsonPath, 'w').write(text)
    except Exception as e:
        print('failed to write file %r: %s'%(jsonPath, e))


def migrateEventsToBson():
    eventsDir = join(newConfDir, 'event', 'events')
    for dname in os.listdir(eventsDir):
        try:
            eid = int(dname)
        except ValueError:
            continue
        dpath = join(eventsDir, dname)
        if not isdir(dpath):
            print('"%s" must be a directory'%dpath)
            continue
        jsonPath = join(dpath, 'event.json')
        if not isfile(jsonPath):
            print('"%s": not such file'%jsonPath)
            continue
        try:
            data = json.loads(open(jsonPath).read())
        except Exception as e:
            print('error while loading json file "%s"'%jsonPath)
            continue
        try:
            tm = data.pop('modified')
        except KeyError:
            tm = now()
        ###
        basicData = {}
        basicData['modified'] = tm
        ###
        ## remove extra params from data and add to basicData
        for param in (
            'remoteIds',
            'notifiers',## FIXME
        ):
            try:
                basicData[param] = data.pop(param)
            except KeyError:
                pass
        ###
        _hash = saveBsonObject(data)
        basicData['history'] = [
            (tm, _hash)
        ]
        open(dpath + '.json', 'w').write(dataToPrettyJson(basicData))
        shutil.rmtree(dpath)



def importConfigFrom24():
    makeDir(newConfDir)
    ####
    coreData = loadCoreConf()
    coreData['version'] = '3.0.0' ## FIXME
    writeJsonConf('core', coreData)
    ####
    writeJsonConf('ui-customize', loadUiCustomizeConf())
    ## remove adjustTimeCmd from ui-gtk.conf
    for name in (
        'hijri',
        'jalali',
        'locale',
        'ui',
        'ui-gtk',
        'ui-live',
    ):
        confPath = join(oldConfDir, name + '.conf')
        writeJsonConf(name, loadConf(confPath))
    ######
    oldPlugConfDir = join(oldConfDir, 'plugins.conf')
    ###
    if isdir(oldPlugConfDir):
        for plugName in os.listdir(oldPlugConfDir):
            writeJsonConf(
                plugName,## move it out of plugins.conf FIXME
                loadConf(
                    join(oldPlugConfDir, plugName)
                ),
            )
    #########
    oldEventDir = join(oldConfDir, 'event')
    newEventDir = join(newConfDir, 'event')
    if isdir(oldEventDir) and not isdir(newEventDir):
        shutil.copytree(oldEventDir, newEventDir)
    #########
    migrateEventsToBson()




def getOldVersion():## return version of starcal 2.*
    data = loadCoreConf()
    try:
        return data['version']
    except:
        return ''

    
##################################

if __name__=='__main__':
    importConfigFrom24()
    #migrateEventsToBson()# FIXME



