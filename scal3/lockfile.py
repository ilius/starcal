import os
from os.path import isfile, exists
from time import time as now
from collections import OrderedDict
import atexit


import psutil

from scal3.utils import myRaise
from scal3.json_utils import jsonToData, dataToPrettyJson


def get_cmdline(proc):
	#print(psutil.version_info, proc.cmdline)
	if isinstance(proc.cmdline, list):## psutil < 2.0
		return proc.cmdline
	else:## psutil >= 2.0
		return proc.cmdline()


def checkAndSaveJsonLockFile(fpath):
	locked = False
	if isfile(fpath):
		try:
			text = open(fpath).read()
		except:
			myRaise()
			locked = True
		else:
			try:
				data = jsonToData(text)
			except:
				print('lock file %s is not valid'%fpath)
			else:
				try:
					pid = data['pid']
					cmd = data['cmd']
				except:
					print('lock file %s is not valid'%fpath)
				else:
					try:
						proc = psutil.Process(pid)
					except psutil.NoSuchProcess:
						print('lock file %s: pid %s does not exist'%(fpath, pid))
					else:
						if get_cmdline(proc) == cmd:
							locked = True
						else:
							print('lock file %s: cmd does match: %s != %s'%(fpath, get_cmdline(proc), cmd))
	elif exists(fpath):
		## what to do? FIXME
		pass
	######
	if not locked:
		my_pid = os.getpid()
		my_proc = psutil.Process(my_pid)
		my_cmd = get_cmdline(my_proc)
		my_text = dataToPrettyJson(OrderedDict([
			('pid', my_pid),
			('cmd', my_cmd),
			('time', now()),
		]))
		try:
			open(fpath, 'w').write(my_text)
		except Exception as e:
			print('failed to write lock file %s: %s'%(fpath, e))
		else:
			atexit.register(os.remove, fpath)
	######
	return locked










