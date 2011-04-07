# -*- coding: utf-8 -*-

import os
from os.path import isfile, join
import locale, gettext
from paths import *
from scal2.utils import StrOrderedDict, toStr
from scal2.cal_modules import modules


APP_NAME = 'starcal2'
langDir = join(rootDir, 'lang')
localeDir = '/usr/share/locale'

digits = {
    'en':(u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9', u'.'),
    'ar':(u'٠', u'١', u'٢', u'٣', u'٤', u'٥', u'٦', u'٧', u'٨', u'٩', u'٫'),
    'fa':(u'۰', u'۱', u'۲', u'۳', u'۴', u'۵', u'۶', u'۷', u'۸', u'۹', u'٫'),
    'ur':(u'۔', u'١', u'٢', u'٣', u'۴', u'۵', u'٦', u'٧', u'٨', u'٩', u'٫'),
    'hi':(u'०', u'१', u'२', u'३', u'४', u'५', u'६', u'७', u'८', u'९', u'.'),## point FIXME
    'th':(u'๐', u'๑', u'๒', u'๓', u'๔', u'๕', u'๖', u'๗', u'๘', u'๙', u'.'),## point FIXME
}

## ar: Aarbic   ar_*    Arabic-indic                       Arabic Contries
## fa: Persian  fa_IR   Eastern (Extended) Arabic-indic    Iran & Afghanintan
## ur: Urdu     ur_PK   (Eastern) Arabic-indic             Pakistan (& Afghanintan??)
## hi: Hindi    hi_IN   Devenagari                         India
## th: Thai     th_TH   ----------                         Thailand

## Urdu digits is a combination of Arabic and Persian digits, except for Zero that is
## named ARABIC-INDIC DIGIT ZERO in unicode database



langDefault = ''
lang = ''
langActive = ''
## langActive==lang except when lang=='' (that langActive will taken from system)
## langActive will not changed via program (because need for restart program to apply new language)
langSh = '' ## short language name, for example 'en', 'fa', 'fr', ...
rtl = False ## right to left
tr = str ## translator

class LangData:
    def __init__(self, code, name, nativeName, fileName, flag, rtl):
        self.code = code
        self.name = name
        self.nativeName = nativeName
        ###
        #self.fileName = fileName## FIXME
        transPath = ''
        for prefix in ('/usr', '/usr/local'):
            path = join(prefix, 'share', 'locale', fileName, 'LC_MESSAGES', '%s.mo'%APP_NAME)
            if isfile(path):
                transPath = path
                break
        self.transPath = transPath
        ###
        if not flag.startswith('/'):
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


def prepareLanguage(lang1):
    global lang, langActive, langSh, rtl
    lang = lang1
    if lang=='':
        #langActive = locale.setlocale(locale.LC_ALL, '')
        langActive = os.environ['LANG']
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
    transObj = gettext.translation(APP_NAME, localeDir, languages=[langActive, langDefault], fallback=True)
    if ui_is_qt:
        tr = lambda s: transObj.gettext(toStr(s)).replace('_', '&').decode('utf-8')## qt takes "&" instead of "_" as trigger
    else:
        tr = lambda s: transObj.gettext(toStr(s)).decode('utf-8')
    return tr

def rtlSgn():
    if rtl:
        return 1
    else:
        return -1

getMonthName = lambda mode, month, year=None: tr(modules[mode].getMonthName(month, year))

def numLocale(num, mode=None, fillZero=0):
    if mode==None:
        mode = langSh
    elif isinstance(mode, int):
        if langSh != 'en':
            try:
                mode = modules[mode].origLang
            except AttributeError:
                mode = langSh
    if mode=='en' or not mode in digits.keys():
        if fillZero:
            return u'%.*d'%(fillZero, num)
        else:
            return u'%d'%num
    neg = (num<0)
    dig = digits[mode]
    res = u''
    for c in unicode(abs(num)):
        if c==u'.':
            res += dig[10]
        else:
            res += dig[int(c)]
    if fillZero>0:
        res = res.rjust(fillZero, dig[0])
    if neg:
        res = '-'+res
    return res



