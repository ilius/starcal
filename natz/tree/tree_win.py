#!/usr/bin/env python3
import os
import os.path
from collections import OrderedDict

from dateutil.tz.win import tzwin
from datetime import datetime


def getZoneInfoTree():
	zoneTree = OrderedDict()
	dt = datetime.now()
	for name in tzwin.list():
		zoneTree[name] = ""
	# FIXME: this is long list, find a way to group them
	# even group by the first word if you have to
	return zoneTree
