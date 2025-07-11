from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.font import Font
from scal3.ui import getFont

if TYPE_CHECKING:
	from scal3.ui.pytypes import DictWithFont

__all__ = ["getOptionsFont"]


def getOptionsFont(options: DictWithFont) -> Font | None:
	font = options.get("font")
	if not font:
		return None
	if not isinstance(font, Font):
		font = Font(*font)
	if font.family is None:
		font.family = getFont().family
	return font
