from __future__ import annotations

from scal3.font import Font
from scal3.ui import getFont

__all__ = ["getParamsFont"]


def getParamsFont(params: dict) -> Font | None:
	font = params.get("font")
	if not font:
		return None
	if not isinstance(font, Font):
		font = Font(*font)
	if font.family is None:
		font.family = getFont().family
	return font
