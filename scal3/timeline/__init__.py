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
from scal3.timeline.conf import confParams
from scal3.timeline.params import confParamsData
from scal3.ui import conf as uiconf

__all__ = ["confParamsData", "saveConf"]

sysConfPath = join(sysConfDir, "timeline.json")

confPath = join(confDir, "timeline.json")

# ---------------------------------------------


def loadConf() -> None:
	if os.getenv("STARCAL_NO_LOAD_CONFIG"):
		return
	loadSingleConfig(
		sysConfPath,
		confParams,
		# decoders=confDecoders,
	)
	loadSingleConfig(
		confPath,
		confParams,
		# decoders=confDecoders,
	)
	conf.bgColor.v = conf.bgColor.v or uiconf.bgColor.v
	conf.fgColor.v = conf.fgColor.v or uiconf.textColor.v


def saveConf() -> None:
	saveSingleConfig(
		confPath,
		confParams,
		# encoders=confEncoders,
	)


# ---------------------------------------------

loadConf()
