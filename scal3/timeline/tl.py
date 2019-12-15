#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from os.path import join

from scal3.path import *
from scal3 import ui
from scal3.json_utils import *


sysConfPath = join(sysConfDir, "timeline.json")

confPath = join(confDir, "timeline.json")

confParams = (
	"bgColor",
	"fgColor",
	"baseFontSize",
	"changeHolidayBg",
	"changeHolidayBgMinDays",
	"changeHolidayBgMaxDays",
	"holidayBgBolor",
	#####################
	"basicButtonsSize",
	"basicButtonsSpacing",
	"basicButtonsOpacity",
	"movementButtonsEnable",
	"movementButtonsSize",
	"movementButtonsOpacity",
	#####################
	"majorStepMin",
	"minorStepMin",
	"maxLabelWidth",
	"baseTickHeight",
	"baseTickWidth",
	"maxTickWidth",
	"maxTickHeightRatio",
	"labelYRatio",
	"yearPrettyPower",
	"truncateTickLabel",
	"currentTimeMarkerHeightRatio",
	"currentTimeMarkerWidth",
	"currentTimeMarkerColor",
	"showWeekStart",
	"showWeekStartMinDays",
	"showWeekStartMaxDays",
	"weekStartTickColor",
	#####################
	"boxLineWidth",
	"boxInnerAlpha",
	"boxEditBorderWidth",
	"boxEditInnerLineWidth",
	"boxEditHelperLineWidth",
	"boxReverseGravity",
	"boxSkipPixelLimit",
	"rotateBoxLabel",
	#####################
	"enableAnimation",
	"movingStaticStepKeyboard",
	"movingStaticStepMouse",
	"movingUpdateTime",
	"movingInitialVelocity",
	"movingHandForceMouse",
	"movingHandForceKeyboard",
	"movingHandForceKeyboardSmall",
	"movingHandForceButton",
	"movingFrictionForce",
	"movingMaxVelocity",
	"movingKeyTimeoutFirst",
	"movingKeyTimeout",
	#####################
	"scrollZoomStep",
	"keyboardZoomStep",
)

#############################################

def loadConf() -> None:
	loadModuleJsonConf(__name__)


def saveConf() -> None:
	saveModuleJsonConf(__name__)

#############################################

bgColor = ui.bgColor
fgColor = ui.textColor

baseFontSize = 8

changeHolidayBg = False
changeHolidayBgMinDays = 1  # day
changeHolidayBgMaxDays = 60  # day
holidayBgBolor = (60, 35, 35)

#############################################

basicButtonsSize = 22
basicButtonsSpacing = 3
basicButtonsOpacity = 1.0  # 0.0 <= value <= 1.0

movementButtonsEnable = True
movementButtonsSize = 22
movementButtonsOpacity = 1.0  # 0.0 <= value <= 1.0

#############################################

majorStepMin = 50  # with label
minorStepMin = 5  # with or without label
maxLabelWidth = 60  # or the same majorStepMin
baseTickHeight = 1.0  # pixel
baseTickWidth = 0.5  # pixel
maxTickWidth = 20.0  # pixel
maxTickHeightRatio = 0.3  # 0 < maxTickHeightRatio < 1
labelYRatio = 1.1
yearPrettyPower = True
truncateTickLabel = False

currentTimeMarkerHeightRatio = 0.3
currentTimeMarkerWidth = 2
currentTimeMarkerColor = (255, 100, 100)

# TODO: change timeline background according to daylight
# sunLightEnable = False
# sunLightH = 10

showWeekStart = True
showWeekStartMinDays = 1  # day
showWeekStartMaxDays = 60  # day
weekStartTickColor = (0, 200, 0)

#############################################

boxLineWidth = 2  # pixel
boxInnerAlpha = 0.1  # 0 <= boxInnerAlpha <= 1

# if boxLineWidth==0 inside the box will be solid (like boxInnerAlpha==0)

boxEditBorderWidth = 10  # pixel
boxEditInnerLineWidth = 0.5  # pixel
boxEditHelperLineWidth = 0.3  # pixel

boxReverseGravity = False

boxSkipPixelLimit = 0.1  # pixel

rotateBoxLabel = -1
# rotateBoxLabel: 0, 1 or -1
# 0: no rotation
# 1: 90 deg CCW (if needed)
# -1: 90 deg CW (if needed)

#############################################

enableAnimation = False

# movingStaticStep* is used only when enableAnimation==False
# number of pixels on each step (keyboard / mouse event)
movingStaticStepKeyboard = 20  # pixel
movingStaticStepMouse = 20  # pixel

movingUpdateTime = 10  # milisecons

# pixel/second, initial speed/velocity when moving time range
movingInitialVelocity = 0

# Force is the same as Acceleration, assuming Mass == 1


movingHandForceMouse = 1100  # pixel / (second^2)
movingHandForceKeyboard = 1100  # pixel / (second^2)
movingHandForceKeyboardSmall = 850  # pixel / (second^2)
# movingHandForceKeyboardSmall is when press Shift with Left/Right arrow
movingHandForceButton = 1100

movingFrictionForce = 600  # pixel / (second^2)
# movingHandForce > movingFrictionForce

movingMaxVelocity = 1200  # pixel / second
# movingMaxVelocity = movingAccel * 4 to reach maximum speed in 4 seconds

movingKeyTimeoutFirst = 0.5  # second

movingKeyTimeout = 0.1  # seconds
# ^ continuous onKeyPress delay is about 0.05 sec

#############################################

scrollZoomStep = 1.2  # > 1.0
keyboardZoomStep = 1.2  # > 1.0

#############################################

keys = {
	"space": "moveToNow",
	"home": "moveToNow",
	"right": "moveRight",
	"left": "moveLeft",
	"down": "moveStop",
	"q": "close",
	"escape": "close",
	"plus": "zoomIn",
	"equal": "zoomIn",
	"kp_add": "zoomIn",
	"minus": "zoomOut",
	"kp_subtract": "zoomOut",
}


#############################################

loadConf()
