import sys

from scal3.locale_man import popenDefaultLang


from scal3.ui_gtk import *


def getDefaultAppCommand(fpath):
	from gi.repository import Gio as gio
	mime_type = gio.content_type_guess(fpath)[0]
	try:
		app = gio.app_info_get_all_for_type(mime_type)[0]
	except IndexError:
		return
	return app.get_executable()


def popenFile(fpath):
	command = getDefaultAppCommand(fpath)
	if not command:
		return
	return popenDefaultLang([
		command,
		fpath,
	])


if __name__ == '__main__':
	print(getDefaultAppCommand(sys.argv[1]))
