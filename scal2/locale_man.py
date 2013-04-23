# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import os, string
from os.path import join, isfile, isdir, isabs
import locale, gettext
from path import *
from scal2.utils import StrOrderedDict, toStr, toUnicode
from scal2.cal_types import calTypes


APP_NAME = 'starcal2'
langDir = join(rootDir, 'conf', 'lang')
localeDir = '/usr/share/locale'

## point FIXME
digits = {
    'en':(u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9'),
    'ar':(u'٠', u'١', u'٢', u'٣', u'٤', u'٥', u'٦', u'٧', u'٨', u'٩'),
    'fa':(u'۰', u'۱', u'۲', u'۳', u'۴', u'۵', u'۶', u'۷', u'۸', u'۹'),
    'ur':(u'۔', u'١', u'٢', u'٣', u'۴', u'۵', u'٦', u'٧', u'٨', u'٩'),
    'hi':(u'०', u'१', u'२', u'३', u'४', u'५', u'६', u'७', u'८', u'९'),
    'th':(u'๐', u'๑', u'๒', u'๓', u'๔', u'๕', u'๖', u'๗', u'๘', u'๙'),
}

def getLangDigits(langSh0):
    try:
        return digits[langSh0]
    except KeyError:
        return digits['en']

## ar: Aarbic   ar_*    Arabic-indic                       Arabic Contries
## fa: Persian  fa_IR   Eastern (Extended) Arabic-indic    Iran & Afghanintan
## ur: Urdu     ur_PK   (Eastern) Arabic-indic             Pakistan (& Afghanintan??)
## hi: Hindi    hi_IN   Devenagari                         India
## th: Thai     th_TH   ----------                         Thailand

## Urdu digits is a combination of Arabic and Persian digits, except for Zero that is
## named ARABIC-INDIC DIGIT ZERO in unicode database

LRM = '\xe2\x80\x8e'
RLM = '\xe2\x80\x8f' ## u'\u200f' ## right to left mark
ZWNJ = '\xe2\x80\x8c'
ZWJ = '\xe2\x80\x8d'

sysLangDefault = os.environ.get('LANG', '')

langDefault = ''
lang = ''
langActive = ''
## langActive==lang except when lang=='' (that langActive will taken from system)
## langActive will not changed via program (because need for restart program to apply new language)
langSh = '' ## short language name, for example 'en', 'fa', 'fr', ...
rtl = False ## right to left

enableNumLocale = True


localeConfPath = join(confDir, 'locale.conf')
if isfile(localeConfPath):
    try:
        exec(open(localeConfPath).read())
    except:
        myRaise(__file__)

## translator
tr = lambda s, *a, **ka: numEncode(s, *a, **ka) if isinstance(s, (int, long)) else str(s)

class LangData:
    def __init__(self, code, name, nativeName, fileName, flag, rtl):
        self.code = code
        self.name = name
        self.nativeName = nativeName
        ###
        #self.fileName = fileName## FIXME
        transPath = ''
        path = join(rootDir, 'locale.d', fileName+'.mo')
        #print 'path=%s'%path
        if isfile(path):
            transPath = path
        else:
            #print '-------- File %r does not exists'%path
            for prefix in ('/usr', '/usr/local'):
                path = join(prefix, 'share', 'locale', fileName, 'LC_MESSAGES', '%s.mo'%APP_NAME)
                if isfile(path):
                    transPath = path
                    break
        #print code, transPath
        self.transPath = transPath
        ###
        if not isabs(flag):
            flag = join(pixDir, 'flags', flag)
        self.flag = flag
        self.rtl = rtl



langDict = StrOrderedDict()
for fname in os.listdir(langDir):
    text = open(join(langDir, fname)).read().strip()
    if fname=='default':
        langDefault = text
        continue
    lines = text.split('\n')
    if len(lines)!=5:
        log.error('bad language file %s: not exactly 5 lines'%fname)
    #assert len(lines)==5
    if lines[4]=='rtl':
        rtl_tmp = True
    elif lines[4]=='ltr':
        rtl_tmp = False
    else:
        raise RuntimeError('bad direction "%s" for language "%s"'%(rtl_tmp, fname))
    langDict[fname] = LangData(fname, lines[0], lines[1], lines[2], lines[3], rtl_tmp)
langDict.sort('name') ## OR 'code' or 'nativeName' ????????????


def prepareLanguage():
    global lang, langActive, langSh, rtl
    if lang=='':
        #langActive = locale.setlocale(locale.LC_ALL, '')
        langActive = sysLangDefault
        if not langActive in langDict.keyList:
            langActive = langDefault
        #os.environ['LANG'] = langActive
    elif lang in langDict.keyList:
        #try:
        #    lang = locale.setlocale(locale.LC_ALL, locale.normalize(lang))
        #except locale.Error:
        #lang = lang.lower()
        #lines = popen_output('locale -a').split('\n') ## FIXME
        #for line in lines:
        #    if line.lower().starts(lang)
        #locale.setlocale(locale.LC_ALL, lang) ## lang = locale.setlocale(...
        langActive = lang
        os.environ['LANG'] = lang
    else:## not lang in langDict.keyList
        #locale.setlocale(locale.LC_ALL, langDefault) ## lang = locale.setlocale(...
        lang               = langDefault
        langActive         = langDefault
        os.environ['LANG'] = langDefault
    langSh = langActive.split('_')[0]
    #sysRtl = (popen_output(['locale', 'cal_direction'])=='3\n')## FIXME
    rtl = langDict[langActive].rtl
    return langSh


def loadTranslator(ui_is_qt=False):
    global tr
    ## FIXME: How to say to gettext that itself detects coding(charset) from locale name and return a unicode object instead of str?
    #if isdir(localeDir):
    #    transObj = gettext.translation(APP_NAME, localeDir, languages=[langActive, langDefault], fallback=True)
    #else:## for example on windows (what about mac?)
    try:
        fd = open(langDict[langActive].transPath, 'rb')
    except:
        transObj = None
    else:
        transObj = gettext.GNUTranslations(fd)
    if transObj:
        def tr(s, *a, **ka):
            if isinstance(s, (int, long)):
                s = numEncode(s, *a, **ka)
            else:
                s = transObj.gettext(toStr(s)).decode('utf-8')
                if ui_is_qt:
                    s = s.replace(u'_', u'&')
                if a:
                    s = s % a
                if ka:
                    s = s % ka
            return s
        '''
        if ui_is_qt:## qt takes "&" instead of "_" as trigger
            tr = lambda s, *a, **ka: numEncode(s, *a, **ka) \
                if isinstance(s, int) \
                else transObj.gettext(toStr(s)).replace('_', '&').decode('utf-8')
        else:
            tr = lambda s, *a, **ka: numEncode(s, *a, **ka) \
                if isinstance(s, int) \
                else transObj.gettext(toStr(s)).decode('utf-8')
        '''
    return tr

rtlSgn = lambda: 1 if rtl else -1

getMonthName = lambda mode, month, year=None: tr(calTypes[mode].getMonthName(month, year))

getNumSep = lambda: tr(u'.') if enableNumLocale else u'.'

def getDigits():
    if enableNumLocale:
        try:
            return digits[langSh]
        except KeyError:
            pass
    return digits['en']

def getAvailableDigitKeys():
    keys = set(digits['en'])
    if langSh != 'en':
        try:
            locDigits = digits[langSh]
        except KeyError:
            pass
        else:
            keys.update(locDigits)
    return keys

def numEncode(num, mode=None, fillZero=0, negEnd=False):
    if not enableNumLocale:
        mode = 'en'
    if mode==None:
        mode = langSh
    elif isinstance(mode, int):
        if langSh != 'en':
            try:
                mode = calTypes[mode].origLang
            except AttributeError:
                mode = langSh
    if mode=='en' or not mode in digits.keys():
        if fillZero:
            return u'%.*d'%(fillZero, num)
        else:
            return u'%d'%num
    neg = (num<0)
    dig = getLangDigits(mode)
    res = u''
    for c in unicode(abs(num)):
        if c==u'.':
            res += dig[10]
        else:
            res += dig[int(c)]
    if fillZero>0:
        res = res.rjust(fillZero, dig[0])
    if neg:
        if negEnd:
            res = res + u'-'
        else:
            res = u'-' + res
    return res

def textNumEncode(st, mode=None, changeSpecialChars=True, changeDot=False):
    if not enableNumLocale:
        mode = 'en'
    if mode==None:
        mode = langSh
    elif isinstance(mode, int):
        if langSh != 'en':
            try:
                mode = calTypes[mode].origLang
            except AttributeError:
                mode = langSh
    dig = getLangDigits(mode)
    res = u''
    for c in toUnicode(st):
        try:
            i = int(c)
        except:
            if c in (',', '_'):## FIXME
                if changeSpecialChars:
                    c = tr(c)
            elif c=='.':## FIXME
                if changeDot:
                    c = tr(c)
            res += c
        else:
            res += dig[i]
    return res ## .encode('utf8')

def numDecode(numSt):
    numSt = numSt.strip()
    try:
        return int(numSt)
    except ValueError:
        pass
    numSt = toUnicode(numSt)
    tryLangs = digits.keys()
    if langSh in digits:
        tryLangs.remove(langSh)
        tryLangs.insert(0, langSh)
    for tryLang in tryLangs:
        tryLangDigits = digits[tryLang]
        numEn = ''
        for dig in numSt:
            if dig=='-':
                numEn += dig
            else:
                try:
                    numEn += str(tryLangDigits.index(dig))
                except ValueError, e:
                    print 'error in decoding num char %s'%dig
                    #raise e
                    break
        else:
            return int(numEn)
    raise ValueError('invalid locale number %s'%numSt)

def textNumDecode(text):## converts '۱۲:۰۰, ۱۳' to '12:00, 13'
    text = toUnicode(text)
    textEn = u''
    langDigits = getLangDigits(langSh)
    for ch in text:
        try:
            textEn += unicode(langDigits.index(ch))
        except ValueError:
            for sch in (u',', u'_', u'.'):
                if ch == tr(sch):
                    ch = sch
                    break
            textEn += ch
    return textEn

dateLocale = lambda year, month, day:\
    numEncode(year, fillZero=4) + '/' + \
    numEncode(month, fillZero=2) + '/' + \
    numEncode(day, fillZero=2)

def cutText(text, n):
    newText = text[:n]
    if len(text) > n:
        if text[n] not in list(string.printable)+[ZWNJ]:
            newText += ZWJ
    return newText

##############################################

prepareLanguage()
loadTranslator()


