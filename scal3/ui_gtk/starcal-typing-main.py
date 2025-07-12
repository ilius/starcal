# mypy: ignore-errors

import sys
import typing
from os.path import dirname

typing.TYPE_CHECKING = True

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3.ui_gtk.starcal import main

main()
