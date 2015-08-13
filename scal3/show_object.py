#!/usr/bin/env python3

import sys
from pprint import pprint
from scal3.s_object import loadBsonObject

if __name__=='__main__':
    for arg in sys.argv[1:]:
        pprint(loadBsonObject(arg))
        print('-------------------')


