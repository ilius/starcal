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

import requests
from datetime import datetime
from pprint import pprint

from scal3.utils import (
	myRaise,
)
from scal3.time_utils import (
	jsonTimeFromEpoch,
)
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3.event_lib import Account

from scal3.cal_types import (
	calTypes,
	jd_to,
	to_jd,
)

#def encodeDateTimeRuleValue(
#	return {
#		"date": dateEncode(self.date),
#		"time": timeEncode(self.time),
#	}


def formatJd(remoteEvent, attrName):
	jd = remoteEvent[attrName]
	year, month, day = calTypes[remoteEvent["calType"]].jd_to(jd)
	return "%.4d/%.2d/%.2d" % (year, month, day)


def allDayTaskDecoder(remoteEvent):
	rules = [
		[
			"start",
			{
				"date": formatJd(remoteEvent, "startJd"),
				"time": "00:00:00"
			}
		],
	]
	if remoteEvent["durationEnable"]:
		rules.append(
			[
				"duration",
				"%d day" % (remoteEvent["endJd"] - remoteEvent["startJd"])
			]
		)
	else:
		rules.append(
			[
				"end",
				{
					"date": formatJd(remoteEvent, "endJd"),
					"time": "00:00:00"
				}
			],
		)
	return {"rules": rules}


remoteEventTypeDecoders = {
	"allDayTask": allDayTaskDecoder,
	"custom": lambda ev: {
	},
	"dailyNote": lambda ev: {
	},
	"largeScale": lambda ev: {
	},
	"lifeTime": lambda ev: {
	},
	"monthly": lambda ev: {
	},
	"task": lambda ev: {
	},
	"universityClass": lambda ev: {
	},
	"universityExam": lambda ev: {
	},
	"weekly": lambda ev: {
	},
	"yearly": lambda ev: {
	},
}


def decodeRemoteEvent(remoteEventFull, accountId, group):
	"""
	remoteEventFull is dict

	return (event, error)
	where event is instance of event_lib.Event, or None
	and error is string or None
	"""
	try:
		eventType = remoteEventFull["eventType"]
	except KeyError:
		return None, "bad remoteEventFull: missing \"eventType\""
	try:
		remoteEvent = remoteEventFull["data"]
	except KeyError:
		return None, "bad remoteEventFull: missing \"data\""
	try:
		decoder = remoteEventTypeDecoders[eventType]
	except KeyError:
		return None, "bad remoteEventFull: unkown type \"%s\"" % eventType
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
		myRaise()
		return None, "bad remoteEvent: %s" % e
	eventData.update(eventTypeData)
	event = event_lib.classes.event.byName[eventType]()
	event.setData(eventData)
	event.remoteIds = (
		accountId,
		remoteEventFull["groupId"],  # remoteGroupId,
		remoteEventFull["eventId"],
		remoteEventFull["sha1"],
	)
	return event, None


@event_lib.classes.account.register
class StarCalendarAccount(Account):
	name = "starcal"
	desc = _("StarCalendar.net")
	params = Account.params + (
		"email",
		"password",
		"lastToken",
	)
	basicParams = Account.basicParams + (
		"password",
		"lastToken",
	)
	paramsOrder = Account.paramsOrder + (
		"email",
		"password",
		"lastToken",
	)

	serverUrl = "http://starcalendar.net:9001/"

	def callBase(self, method, path, **kwargs):
		return getattr(requests, method)(
			self.serverUrl + path,
			headers={"Authorization": "bearer " + self.lastToken},
			json=kwargs,
		)

	def call(self, method, path, **kwargs):
		"""
		return (data, None) if successful
		return (data, error) if failed
		where error is string and data is a dict
		"""
		error = None
		data = {}
		tokenIsOld = bool(self.lastToken)

		try:
			if not tokenIsOld:
				error = self.login()
				if error:
					return data, error
			res = self.callBase(method, path, **kwargs)
			if res.status_code == 401:
				if tokenIsOld:
					error = self.login()
					if error:
						return data, error
					res = self.callBase(method, path, **kwargs)
		except Exception as e:
			error = str(e)
			return data, error

		try:
			data = res.json()
		except:
			error = "non-json data: %s" % res.text
		else:
			try:
				error = data.pop("error")
			except KeyError:
				pass
		return data, error

	def __init__(self, aid=None):
		Account.__init__(self, aid)
		self.email = ""
		self.password = ""
		self.lastToken = ""

	def login(self):
		"""
		self.email and self.password must be set
		this methods logs in by the server, gets the token
		and sets self.lastToken

		return None if successful, or error string if failed
		"""
		print("login started")

		email = self.email
		password = self.password
		res = requests.post(
			self.serverUrl + "auth/login/",
			json={
				"email": email,
				"password": password,
			},
		)
		error = None
		token = ""
		try:
			data = res.json()
		except:
			error = "non-json data: %s" % res.text
		else:
			error = data.get("error", "")
			token = data.get("token", "")

		if not token:
			if not error:
				error = "login failed, unkown error"
			return error

		self.lastToken = token
		print("login successful")

	def fetchGroups(self):
		"""
		return None if successful, or error string if failed
		"""
		print("fetchGroups started")
		data, error = self.call("get", "event/groups/")
		if error:
			return error

		try:
			groups = data["groups"]
		except KeyError:
			return "bad data: missing \"groups\""

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
			return "bad data: %s" % e

		print("fetchGroups successful, %s groups" % len(self.remoteGroups))

	def addNewGroup(self, title):
		pass

	def deleteGroup(self, remoteGroupId):
		pass

	def sync(self, group, remoteGroupId):  # in progress TODO
		"""
		return None if successful, or error string if failed
		"""
		print("sync started")
		if not group.remoteIds:
			return "sync not enabled"
		if group.remoteIds[0] != self.id:
			return "mismatch account id"
		groupId = group.remoteIds[1]
		lastSyncTuple = group.getLastSync()
		if lastSyncTuple is None:
			lastSyncStartEpoch = group.getStartEpoch()
			lastSyncEndEpoch = None  # FIXME
		else:
			lastSyncStartEpoch, lastSyncEndEpoch = lastSyncTuple

		syncStart = datetime.now()

		path = "event/groups/%s/modified-events/%s/" % (
			groupId,
			jsonTimeFromEpoch(lastSyncStartEpoch),
		)
		data, error = self.call("get", path)
		if error:
			return error
		try:
			remoteModifiedEvents = data["modifiedEvents"]
		except KeyError:
			return "bad data: missing \"modifiedEvents\""
		try:
			group.setReadOnly(True)

			### Pull
			for remoteEvent in remoteModifiedEvents:
				# remoteEvent is a dict
				pprint(remoteEvent)
				event, error = decodeRemoteEvent(
					remoteEvent,
					self.id,
					group,
				)
				if error:
					print(error)
					continue
				# record = event.save() # record is (lastEpoch, lastHash, **args)
				# event.lastMergeSha1 = [
				# 	record[1], # local sha1
				# 	event.remoteIds[1], # remote sha1
				# ]
				# group.replaceEvent(event)

			### Push
			if lastSyncEndEpoch:
				pass

		except Exception as e:
			myRaise()
			return "sync failed: %s" % e
		else:
			group.afterSync(syncStart.timestamp())
		finally:
			group.setReadOnly(False)
			group.save()
