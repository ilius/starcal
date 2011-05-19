#!/usr/bin/env python2
# -*- coding: utf-8 -*-
uiName = 'gtk'

import sys, os
from os.path import dirname, join, isdir

if sys.version_info[0] != 2:
    print 'Run this script with Python 2.x'
    sys.exit(1)

sys.path.append(dirname(__file__))
from scal2.paths import *
from scal2.utils import myRaise

if not isdir(confDir):
    try:
        __import__('scal2.ui_%s.config_importer'%uiName)
    except:
        myRaise()

main = __import__('scal2.ui_%s.starcal_%s'%(uiName, uiName), fromlist=['main']).main
sys.exit(main())

