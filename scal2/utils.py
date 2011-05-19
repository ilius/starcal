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

toStr = lambda s: s.encode('utf8') if isinstance(s, unicode) else str(s)
toUnicode = lambda s: s if isinstance(s, unicode) else str(s).decode('utf8')



def cmpVersion(v0, v1):
    assert type(v0)==type(v1)==str
    if v0=='':
        if v1=='':
            return 0
        else:
            return -1
    elif v1=='':
        return 1
    return cmp([ int(p) for p in v0.split('.') ], [ int(p) for p in v1.split('.') ])

class FallbackLogger:
    def __init__(self):
        pass
    def error(self, text):
        sys.stderr.write('ERROR: %s\n'%text)
    def warning(self, text):
        print 'WARNING: %s'%text
    def debug(self, text):
        print text

def myRaise(File=None):
    i = sys.exc_info()
    if File==None:
        sys.stderr.write('line %s: %s: %s\n'%(i[2].tb_lineno, i[0].__name__, i[1]))
    else:
        sys.stderr.write('File "%s", line %s: %s: %s\n'%(File, i[2].tb_lineno, i[0].__name__, i[1]))

class StrOrderedDict(dict):
    ## A dict from strings to objects, with ordered keys
    ## and some looks like a list
    def __init__(self, arg=[], reorderOnModify=True):
        self.reorderOnModify = reorderOnModify
        if isinstance(arg, (list, tuple)):
            self.keyList = [item[0] for item in arg]
        elif isinstance(arg, dict):
            self.keyList = sorted(arg.keys)
        else:
            raise TypeError('StrOrderedDict: bad type for first argument: %s'%type(arg))
        dict.__init__(self, arg)
    keys = lambda self: self.keyList
    values = lambda self: [dict.__getitem__(self, key) for key in self.keyList]
    items = lambda self: [(key, dict.__getitem__(self, key)) for key in self.keyList]
    def __getitem__(self, arg):
        if isinstance(arg, int):
            return dict.__getitem__(self, self.keyList[arg])
        elif isinstance(arg, basestring):
            return dict.__getitem__(self, arg)
        elif isinstance(arg, slice):## ???????????? is not tested
            return StrOrderedDict([(key, dict.__getitem__(self, key))
                                                         for key in self.keyList.__getitem__(arg)])
        else:
            raise ValueError('Bad type argument given to StrOrderedDict.__getitem__: %s'
                %type(arg))
    def __setitem__(self, arg, value):
        if isinstance(arg, int):
            dict.__setitem__(self, self.keyList[arg], value)
        elif isinstance(arg, basestring):
            if arg in self.keyList:## Modifying value for an existing key
                if reorderOnModify:
                    self.keyList.remove(arg)
                    self.keyList.append(arg)
            #elif isinstance(arg, slice):## ???????????? is not tested
            #    #assert isinstance(value, StrOrderedDict)
            #    if isinstance(value, StrOrderedDict):
            #        for key in self.keyList.__getitem__(arg):
            else:
                self.keyList.append(arg)
            dict.__setitem__(self, arg, value)
        else:
            raise ValueError('Bad type argument given to StrOrderedDict.__setitem__: %s'
                %type(item))
    def __delitem__(self, arg):
        if isinstance(arg, int):
            self.keyList.__delitem__(arg)
            dict.__delitem__(self, self.keyList[arg])
        elif isinstance(arg, basestring):
            self.keyList.remove(arg)
            dict.__delitem__(self, arg)
        elif isinstance(arg, slice):## ???????????? is not tested
            for key in self.keyList.__getitem__(arg):
                dict.__delitem__(self, key)
            self.keyList.__delitem__(arg)
        else:
            raise ValueError('Bad type argument given to StrOrderedDict.__delitem__: %s'
                %type(arg))
    pop = lambda self, key: self.__delitem__(key)
    def clear(self):
        self.keyList = []
        dict.clear(self)
    def append(self, key, value):
        assert isinstance(key, basestring) and not key in self.keyList
        self.keyList.append(key)
        dict.__setitem__(self, key, value)
    def insert(self, index, key, value):
        assert isinstance(key, basestring) and not key in self.keyList
        self.keyList.insert(index, key)
        dict.__setitem__(self, key, value)
    #def __cmp__(self, other):#?????
    def sort(self, attr=None):
        if attr==None:
            self.keyList.sort()
        else:
            myCmp = lambda k1, k2: cmp(
                getattr(dict.__getitem__(self, k1), attr),
                getattr(dict.__getitem__(self, k2), attr)
            )
            self.keyList.sort(myCmp)
    __iter__ = lambda self: self.keyList.__iter__()
    def iteritems(self):## OR lambda self: self.items().__iter__()
        for key in self.keyList:## OR self.keyList.__iter__()
            yield (key, dict.__getitem__(self, key))
    def __str__(self):
        #return 'StrOrderedDict{' + ', '.join([repr(k)+':'+repr(self[k]) for k in self.keyList]) + '}'
        return 'StrOrderedDict(%r)'%self.items()
    def __repr__(self):
        return 'StrOrderedDict(%r)'%self.items()


class NullObj:## a fully transparent object
    def __setattr__(self, attr, value):
        pass
    __getattr__ = lambda self, attr: self
    __call__ = lambda self, *args, **kwargs: self
    __str__ = lambda self: ''
    __repr__ = lambda self: ''
    __int__ = lambda self: 0


