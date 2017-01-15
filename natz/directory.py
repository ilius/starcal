import os
import os.path

infoDir = "/usr/share/zoneinfo"

if not os.path.isdir(infoDir):
	import pytz
	pytz_infoDir = os.path.join(os.path.dirname(pytz.__file__), "zoneinfo")
	if os.path.isdir(pytz_infoDir):
		infoDir = pytz_infoDir
	else:
		raise IOError(
			"zoneinfo directory not found" +
			", neither \"%s\" nor \"%s\"" % (infoDir, infoDir_pytz)
		)
