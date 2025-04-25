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
import os
from os.path import join

from scal3.config_utils import (
	loadSingleConfig,
	saveSingleConfig,
)
from scal3.path import confDir, sysConfDir
from scal3.timeline import conf
from scal3.timeline.params import confParamsData
from scal3.ui import conf as uiConf

__all__ = ["saveConf"]

sysConfPath = join(sysConfDir, "timeline.json")

confPath = join(confDir, "timeline.json")

confParams = [p.v3Name for p in confParamsData]

# ---------------------------------------------


def loadConf() -> None:
	if os.getenv("STARCAL_NO_LOAD_CONFIG"):
		return
	loadSingleConfig(
		conf,
		sysConfPath,
		# decoders=confDecoders,
	)
	loadSingleConfig(
		conf,
		confPath,
		# decoders=confDecoders,
	)
	conf.bgColor = conf.bgColor or uiConf.bgColor
	conf.fgColor = conf.fgColor or uiConf.textColor


def saveConf() -> None:
	saveSingleConfig(
		conf,
		confPath,
		confParams,
		# encoders=confEncoders,
	)


# ---------------------------------------------

loadConf()
