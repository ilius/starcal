# FIXME: what is the purpose of this?
# def convertAllPluginsToIcs(startYear: int, endYear: int) -> None:
# 	if GREGORIAN not in calTypes:
# 		raise RuntimeError(f"cal type {GREGORIAN=} not found")
# 	startJd = to_jd(startYear, 1, 1, GREGORIAN)
# 	endJd = to_jd(endYear + 1, 1, 1, GREGORIAN)
# 	namePostfix = f"-{startYear}-{endYear}"
# 	for plug in core.allPlugList:
# 		if isinstance(plug, HolidayPlugin):
# 			convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix)
# 		elif isinstance(plug, BuiltinTextPlugin):
# 			convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix)
# 		else:
# 			log.info(f"Ignoring unsupported plugin {plug.file}")
