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

from os.path import join
from typing import Any, Final

from scal3.config_utils import loadModuleConfig, saveSingleConfig
from scal3.option import Option
from scal3.path import confDir

# row ID in the tree for the "Archived Groups" holder node
# (the trash row uses -1)
archivedGroupsRowId = -2

confPath = join(confDir, "event", "manager.json")

eventManPos: Final[Option[tuple[int, int]]] = Option((0, 0))
eventManShowDescription: Final[Option[bool]] = Option(True)
confOptions: dict[str, Option[Any]] = {
	"eventManPos": eventManPos,
	"eventManShowDescription": eventManShowDescription,
}


def loadConf() -> None:
	loadModuleConfig(
		confPath=confPath,
		sysConfPath=None,
		options=confOptions,
		decoders={},
	)


def saveConf() -> None:
	saveSingleConfig(confPath, confOptions, {})
