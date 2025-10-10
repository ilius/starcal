import abc
import os
from os.path import isabs, join, split
from typing import Any

from scal3.path import pixDir, svgDir

__all__ = ["WithIcon", "iconAbsToRelativelnData"]


class WithIcon(abc.ABC):
	icon: str | None

	def getIcon(self) -> str | None:
		return self.icon

	def getIconRel(self) -> str | None:
		icon = self.icon
		if not icon:
			return None
		for direc in (svgDir, pixDir):
			if icon.startswith(direc + os.sep):
				return icon[len(direc) + 1 :]
		return icon

	def iconRelativeToAbsInObj(self) -> None:
		icon = self.icon
		if icon and not isabs(icon):
			if "/" not in icon:
				icon = join("event", icon)
			if icon.endswith(".png"):
				icon = join(pixDir, icon)
			else:
				icon = join(svgDir, icon)
		self.icon = icon


def iconAbsToRelativelnData(data: dict[str, Any]) -> None:
	icon = data["icon"]
	if icon is None:
		return
	iconDir, iconName = split(icon)
	if iconName == "obituary.png":
		iconName = "green_clover.svg"
	elif iconDir in {
		"event",
		join(svgDir, "event"),
		join(pixDir, "event"),
	}:
		icon = iconName
	data["icon"] = icon
