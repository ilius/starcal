import sys
from os.path import join
import logging

from scal2.cal_modules import gregorian
from scal_mod_paths import *

DATE_GREG = 0 ## Gregorian (common calendar)
moduleNames = ['gregorian']
modules = [gregorian]

def myRaise():
    i = sys.exc_info()
    sys.stdout.write('File "%s", line %s: %s: %s\n'%(__file__, i[2].tb_lineno, i[0].__name__, i[1]))


for name in open(join(modDir, 'modules.list')).read().split('\n'):
    name = name.strip()
    if name=='':
        continue
    if name.startswith('#'):
        continue
    try:
        mod = __import__('scal2.cal_modules.%s'%name, fromlist=[name])
        #mod = __import__(name) ## Need to "sys.path.insert(0, modDir)" before
    except:
        myRaise()
        sys.stdout.write('Could not load calendar modules "%s"\n%s\n'%(name,sys.exc_info()[1]))
        continue
    for attr in ('name','desc','origLang','monthName','getMonthName',
                 'minMonthLen','maxMonthLen','getMonthLen','to_jd','jd_to','options','save'):
        if not hasattr(mod, attr):
            sys.stdout.write('Invalid calendar module: module "%s" has no attribute "%s"\n'%(name, attr))
    moduleNames.append(name)
    modules.append(mod)

modNum = len(modules)
## calOrigLang = [m.origLang for m in modules]

jd_to = lambda jd, target: modules[target].jd_to(jd)
to_jd = lambda y, m, d, source: modules[source].to_jd(y, m, d)

def convert(y, m, d, source, target):
    return (y, m, d) if source==target else jd_to(to_jd(y, m, d, source), target)

