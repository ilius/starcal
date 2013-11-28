import sys
from subprocess import Popen

import gio
import gtk


def getDefaultAppCommand(fpath):
    mime_type = gio.content_type_guess(fpath)
    try:
        app = gio.app_info_get_all_for_type(mime_type)[0]
    except IndexError:
        return
    return app.get_executable()


def popenFile(fpath):
    command = getDefaultAppCommand(fpath)
    if not command:
        return
    return Popen([
        command,
        fpath,
    ])




if __name__=='__main__':
    getAppListForFile(sys.argv[1])


