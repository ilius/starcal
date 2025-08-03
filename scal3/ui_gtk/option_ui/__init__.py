#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger

log = logger.get()


from scal3.ui_gtk.option_ui.base import OptionUI

from .check import CheckOptionUI
from .check_mix import CheckColorOptionUI, CheckFontOptionUI
from .color import ColorOptionUI
from .combo import ComboEntryTextOptionUI, ComboTextOptionUI
from .direction import DirectionOptionUI
from .file import IconChooserOptionUI, ImageFileChooserOptionUI
from .font import FontFamilyOptionUI, FontOptionUI
from .geo import WidthHeightOptionUI
from .justification import JustificationOptionUI
from .spin import FloatSpinOptionUI, IntSpinOptionUI
from .text import TextOptionUI

__all__ = [
	"CheckColorOptionUI",
	"CheckFontOptionUI",
	"CheckOptionUI",
	"ColorOptionUI",
	"ComboEntryTextOptionUI",
	"ComboTextOptionUI",
	"DirectionOptionUI",
	"FloatSpinOptionUI",
	"FontFamilyOptionUI",
	"FontOptionUI",
	"IconChooserOptionUI",
	"ImageFileChooserOptionUI",
	"IntSpinOptionUI",
	"JustificationOptionUI",
	"OptionUI",
	"TextOptionUI",
	"WidthHeightOptionUI",
]


# All methods of Gtk.ColorButton are deprecated since version 3.4:
# Looks like ColorButton itself is deprecated, and should be replaced
# with something else!!
