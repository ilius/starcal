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

from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, Any

from scal3.cal_types import calTypes
from scal3.event_lib import Account, classes
from scal3.event_lib.errors import AccountError
from scal3.locale_man import tr as _
from scal3.time_utils import jsonTimeFromEpoch

if TYPE_CHECKING:
	import requests

	from scal3.event_lib.pytypes import EventGroupType, EventType


__all__ = ["StarCalendarAccount"]
# def encodeDateTimeRuleValue(
# 	return {
# 		"date": dateEncode(self.date),
# 		"time": timeEncode(self.time),
# 	}


def formatJd(remoteEvent: dict[str, Any], attrName: str) -> str:
	jd = remoteEvent[attrName]
	mod = calTypes[remoteEvent["calType"]]
	if mod is None:
		raise ValueError(f"bad calType in {remoteEvent=}")
	y, m, d = mod.jd_to(jd)
	return f"{y:04}/{m:02}/{d:02}"


def allDayTaskDecoder(remoteEvent: dict[str, Any]) -> dict[str, Any]:
	rules = [
		[
			"start",
			{
				"date": formatJd(remoteEvent, "startJd"),
				"time": "00:00:00",
			},
		],
	]
	if remoteEvent["durationEnable"]:
		rules.append(
			[
				"duration",
				str(remoteEvent["endJd"] - remoteEvent["startJd"]) + " day",
			],
		)
	else:
		rules.append(
			[
				"end",
				{
					"date": formatJd(remoteEvent, "endJd"),
					"time": "00:00:00",
				},
			],
		)
	return {"rules": rules}


def _emptyDecoder(_ev: dict[str, Any]) -> dict[str, Any]:
	return {}


remoteEventTypeDecoders = {
	"allDayTask": allDayTaskDecoder,
	"custom": _emptyDecoder,
	"dailyNote": _emptyDecoder,
	"largeScale": _emptyDecoder,
	"lifetime": _emptyDecoder,
	"monthly": _emptyDecoder,
	"task": _emptyDecoder,
	"universityClass": _emptyDecoder,
	"universityExam": _emptyDecoder,
	"weekly": _emptyDecoder,
	"yearly": _emptyDecoder,
}


def decodeRemoteEvent(
	remoteEventFull: dict[str, Any],
	accountId: int,
	_group: EventGroupType,
) -> tuple[EventType | None, str | None]:
	"""
	Return (event, error)
	where event is instance of event_lib.Event, or None
	and error is string or None.
	"""
	try:
		eventType = remoteEventFull["eventType"]
	except KeyError:
		return None, 'bad remoteEventFull: missing "eventType"'
	try:
		remoteEvent = remoteEventFull["data"]
	except KeyError:
		return None, 'bad remoteEventFull: missing "data"'
	try:
		decoder = remoteEventTypeDecoders[eventType]
	except KeyError:
		return None, f'bad remoteEventFull: unkown type "{eventType}"'
	eventData = {
		"summary": remoteEvent["summary"],
		"description": remoteEvent["description"],
		"calType": remoteEvent["calType"],
		"icon": remoteEvent["icon"],
		"timeZone": remoteEvent["timeZone"],
		"timeZoneEnable": remoteEvent["timeZoneEnable"],
	}
	try:
		eventTypeData = decoder(remoteEvent)
	except Exception as e:
		log.exception("")
		return None, f"bad remoteEvent: {e}"
	eventData.update(eventTypeData)
	event = classes.event.byName[eventType]()
	event.setDict(eventData)
	remoteGroupId = remoteEventFull["groupId"]
	remoteEvendId = remoteEventFull["eventId"]
	remoteSha1 = remoteEventFull["sha1"]
	assert isinstance(remoteGroupId, str), f"{remoteGroupId=}"
	assert isinstance(remoteEvendId, str), f"{remoteEvendId=}"
	assert isinstance(remoteSha1, str), f"{remoteSha1=}"
	event.remoteIds = (
		accountId,
		remoteGroupId,
		remoteEvendId,
		remoteSha1,
	)
	return event, None


@classes.account.register
class StarCalendarAccount(Account):
	name = "starcal"
	desc = _("StarCalendar.net")
	params = Account.params + [
		"email",
		"password",
		"lastToken",
	]
	basicOptions: list[str] = Account.basicOptions + [
		"password",
		"lastToken",
	]
	paramsOrder = Account.paramsOrder + [
		"email",
		"password",
		"lastToken",
	]

	serverUrl = "http://127.0.0.1:9001/"

	def callBase(
		self,
		method: str,
		path: str,
		reqData: dict[str, Any] | None = None,
	) -> requests.Response:
		import requests

		return requests.request(
			method,
			self.serverUrl + path,
			headers={"Authorization": "bearer " + self.lastToken},
			json=reqData,
		)

	def call(
		self,
		method: str,
		path: str,
		reqData: dict[str, Any] | None = None,
	) -> tuple[dict[str, Any], str | None]:
		"""
		Return (data, None) if successful
		return (data, error) if failed
		where error is string and data is a dict.
		"""
		error = None
		data: dict[str, Any] = {}
		tokenIsOld = bool(self.lastToken)

		try:
			if not tokenIsOld:
				error = self.login()
				if error:
					return data, error
			res = self.callBase(method, path, reqData)
			if res.status_code == 401 and tokenIsOld:
				error = self.login()
				if error:
					return data, error
				res = self.callBase(method, path, reqData)
		except Exception as e:
			error = str(e)
			return data, error

		try:
			data = res.json()
		except Exception:
			# simplejson.errors.JSONDecodeError
			error = "non-json data: " + res.text
		else:
			with suppress(KeyError):
				error = data.pop("error")
		return data, error

	def __init__(self, ident: int | None = None) -> None:
		Account.__init__(self, ident)
		self.email = ""
		self.password = ""
		self.lastToken = ""

	def login(self) -> str | None:
		"""
		self.email and self.password must be set
		this methods logs in by the server, gets the token
		and sets self.lastToken.

		return None if successful, or error string if failed
		"""
		import requests

		log.info("login started")

		email = self.email
		password = self.password
		res = requests.post(
			self.serverUrl + "auth/login/",
			json={
				"email": email,
				"password": password,
			},
			timeout=10,  # FIXME: config
		)
		error = None
		token = ""
		try:
			data = res.json()
		except Exception:
			# simplejson.errors.JSONDecodeError
			error = "non-json data: " + res.text
		else:
			error = data.get("error", "")
			token = data.get("token", "")

		if not token:
			if not error:
				error = "login failed, unkown error"
			return error

		self.lastToken = token
		log.info("login successful")
		return None

	def fetchGroups(self) -> None:
		log.info("fetchGroups started")
		data, error = self.call("get", "event/groups/")
		if error:
			raise AccountError(error)

		try:
			groups = data["groups"]
		except KeyError:
			raise AccountError('bad data: missing "groups"') from None

		try:
			self.remoteGroups = [
				{
					"id": g["groupId"],
					"title": g["title"],
				}
				for g in groups
				if g["ownerEmail"] == self.email
			]
		except Exception as e:
			raise AccountError(f"bad data: {e}") from None

		log.info(f"fetchGroups successful, {len(self.remoteGroups)} groups")

	def addNewGroup(self, title: str) -> None:
		pass

	def deleteGroup(self, remoteGroupId: str) -> None:
		pass

	def sync(
		self,
		group: EventGroupType,
		remoteGroupId: str,  # noqa: ARG002
	) -> None:
		# in progress TODO
		"""Return None if successful, or error string if failed."""
		log.info("sync started")
		if not group.remoteIds:
			raise AccountError("sync not enabled")
		if group.remoteIds[0] != self.id:
			raise AccountError("mismatch account id")
		groupId = group.remoteIds[1]
		lastSyncTuple = group.getLastSync()
		lastSyncStartEpoch: float
		lastSyncEndEpoch: float | None
		if lastSyncTuple is None:
			lastSyncStartEpoch = group.getStartEpoch()
			lastSyncEndEpoch = None  # FIXME
		else:
			lastSyncStartEpoch, lastSyncEndEpoch = lastSyncTuple

		syncStart = datetime.now()

		path = (
			f"event/groups/{groupId}/modified-events/"
			f"{jsonTimeFromEpoch(lastSyncStartEpoch)}/"
		)
		data, error = self.call("get", path)
		if error:
			raise AccountError(error)
		try:
			remoteModifiedEvents = data["modifiedEvents"]
		except KeyError:
			raise AccountError('bad data: missing "modifiedEvents"') from None
		try:
			group.setReadOnly(True)

			# Pull
			for remoteEvent in remoteModifiedEvents:
				# remoteEvent is a dict
				log.info(remoteEvent)
				_event, error = decodeRemoteEvent(
					remoteEvent,
					self.id,
					group,
				)
				if error:
					log.error(error)
					continue
				# record = event.save() # record is (lastEpoch, lastHash, **args)
				# event.lastMergeSha1 = [
				# 	record[1], # local sha1
				# 	event.remoteIds[1], # remote sha1
				# ]
				# group.replaceEvent(event)

			# Push
			if lastSyncEndEpoch:
				pass

		except Exception as e:
			log.exception("")
			raise AccountError(f"sync failed: {e}") from None
		else:
			group.afterSync(syncStart.timestamp())
		finally:
			group.setReadOnly(False)
			group.save()
