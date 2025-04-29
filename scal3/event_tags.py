from __future__ import annotations

from scal3 import logger

log = logger.get()

import os
import os.path
from os.path import isabs, isfile, join

from scal3.locale_man import tr as _
from scal3.path import svgDir

__all__ = ["eventTags"]


eventIconDir = join(svgDir, "event")


class TagIconItem:
	def __init__(self, name, desc="", icon="", eventTypes=()):
		self.name = name
		if not desc:
			desc = name.capitalize()
		self.desc = _(desc)
		if icon:
			if not isabs(icon):
				icon = join(eventIconDir, icon)
		else:
			iconTmp = join(eventIconDir, name) + ".svg"
			if isfile(iconTmp):
				icon = iconTmp
			else:
				log.debug(f"TagIconItem: file not found: {iconTmp}")
		self.icon = icon
		self.eventTypes = eventTypes
		self.usage = 0

	def getIconRel(self):
		icon = self.icon
		if icon.startswith(svgDir + os.sep):
			return icon[len(svgDir) + 1 :]
		return icon

	def __repr__(self):
		return (
			f"TagIconItem({self.name!r}, desc={self.desc!r}, "
			f"icon={self.icon!r}, eventTypes={self.eventTypes!r})"
		)


eventTags = (
	TagIconItem("alarm"),
	TagIconItem("birthday", eventTypes=("yearly",), desc="Birthday (Balloons)"),
	TagIconItem("birthday2", eventTypes=("yearly",), desc="Birthday (Cake)"),
	TagIconItem("business"),
	TagIconItem("education"),
	TagIconItem("favorite"),
	TagIconItem("green_clover", desc="Green Clover"),
	TagIconItem("holiday"),
	TagIconItem("important"),
	TagIconItem("marriage", eventTypes=("yearly",)),
	TagIconItem("note", eventTypes=("dailyNote",)),
	TagIconItem("phone_call", desc="Phone Call", eventTypes=("task",)),
	TagIconItem("task", eventTypes=("task",)),
	TagIconItem("university", eventTypes=("task",)),  # FIXME: eventTypes
	TagIconItem("shopping_cart", desc="Shopping Cart"),
	TagIconItem("personal"),  # TODO: icon
	TagIconItem("appointment", eventTypes=("task",)),  # TODO: icon
	TagIconItem("meeting", eventTypes=("task",)),  # TODO: icon
	TagIconItem("travel"),  # TODO: icon
)


def getEventTagsDict():
	return {tagObj.name: tagObj for tagObj in eventTags}


# def updateEventTagsUsage():  # FIXME where to use?
# 	tagsDict = getEventTagsDict()
# 	for tagObj in eventTags:
# 		tagObj.usage = 0
# 	for event in events:  # FIXME
# 		for tag in event.tags:
# 			td = tagsDict.get(tag)
# 			if td is not None:
# 				tagsDict[tag].usage += 1


eventTagsDesc = {t.name: t.desc for t in eventTags}
