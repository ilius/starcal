#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# FIXME
developerKey = (
	"AI39si4QJ0bmdZJd7nVz0j3zuo1JYS3WUJX8y0f2" +
	"mvGteDtiKY8TUSzTsY4oAcGlYAM0LmOxHmWWyFLU"
)

from scal3 import logger
log = logger.get()

import sys
from os.path import splitext
from time import time as now
import http.server

from pprint import pprint, pformat

try:
	from urllib.parse import parse_qsl
except ImportError:
	from cgi import parse_qsl

import httplib2
from httplib2 import *

from scal3.path import *

sys.path.append(join(sourceDir, "google-api-python-client"))  # FIXME
sys.path.append(join(sourceDir, "oauth2client"))  # FIXME

from scal3.utils import toBytes, toStr

from scal3.ics import *
from scal3.os_utils import openUrl
from scal3.cal_types import to_jd, jd_to, GREGORIAN
from scal3.locale_man import tr as _
from scal3 import core

from scal3 import event_lib
from scal3.event_lib import Account


auth_local_webserver = True
auth_host_name = "localhost"
auth_host_port = [8080, 8090]

syncResultPerPage = 1000

STATUS_UNCHANCHED, STATUS_ADDED, STATUS_DELETED, STATUS_MODIFIED = range(4)


def calcEtag(gevent):
	return core.compressLongInt(abs(hash(repr(gevent))))


def decodeIcsStartEnd(value):
	return {
		("dateTime" if "T" in value else "date"): value,
		"timeZone": "GMT",
	}


def encodeIcsStartEnd(value):
	timeZone = value.get("timeZone", "GMT")  # FIXME
	if "date" in value:
		icsValue = value["date"].replace("-", "")
	elif "dateTime" in value:
		icsValue = value["dateTime"].replace("-", "").replace(":", "")
	else:
		raise ValueError(f"bad gcal start/end value '{value}'")
	return icsValue


def exportEvent(event):
	if not event.changeCalType(GREGORIAN):
		return
	icsData = event.getIcsData(True)
	if not icsData:
		return
	gevent = {
		"kind": "calendar#event",
		"summary": toStr(event.summary),
		"description": toStr(event.description),
		"attendees": [],
		"status": "confirmed",
		"visibility": "default",
		"guestsCanModify": False,
		"reminders": {
			"overrides": {
				"minutes": event.getNotifyBeforeMin(),
				"method": "popup",  # FIXME
			},
		},
		"extendedProperties": {
			"shared": {
				"starcal_id": event.id,
				"starcal_type": event.name,
			},
		}
	}
	for key, value in icsData:
		key = key.upper()
		if key == "DTSTART":
			gevent["start"] = decodeIcsStartEnd(value)
		elif key == "DTEND":
			gevent["end"] = decodeIcsStartEnd(value)
		elif key in ("RRULE", "RDATE", "EXRULE", "EXDATE"):
			if "recurrence" not in gevent:
				gevent["recurrence"] = []
			gevent["recurrence"].append(key + ":" + value)
		elif key == "TRANSP":
			gevent["transparency"] = value.lower()
		# elif key=="CATEGORIES":
	return gevent

#def exportToEvent(event, group, gevent):  # FIXME


def importEvent(gevent, group):
	# open("/tmp/gevent.js", "a").write(pformat(gevent) + "\n\n")
	icsData = [
		("DTSTART", encodeIcsStartEnd(gevent["start"])),
		("DTEND", encodeIcsStartEnd(gevent["end"])),
	]

	recurring = False
	if "recurrence" in gevent:
		recurring = True
		for recStr in gevent["recurrence"]:
			key, value = recStr.upper().split(":")  # multi line? FIXME
			icsData.append((key, value))
	try:
		eventType = gevent["extendedProperties"]["shared"]["starcal_type"]
	except KeyError:
		if recurring:
			eventType = "custom"
		else:
			eventType = "task"

	event = group.create(eventType)
	event.calType = GREGORIAN  # FIXME
	if not event.setIcsData(dict(icsData)):
		return
	event.summary = toBytes(gevent["summary"])
	event.description = toBytes(gevent.get("description", ""))
	if "reminders" in gevent:
		try:
			minutes = gevent["reminders"]["overrides"]["minutes"]
		except KeyError:
			log.exception("")  # FIXME
		else:
			self.notifyBefore = (minutes, 60)
	return event


class ClientRedirectServer(http.server.HTTPServer):
	"""
	A server to handle OAuth 2.0 redirects back to localhost.

	Waits for a single request and parses the query parameters
	into query_params and then stops serving.
	"""
	query_params = {}


class ClientRedirectHandler(http.server.BaseHTTPRequestHandler):
	"""
	A handler for OAuth 2.0 redirects back to localhost.

	Waits for a single request and parses the query parameters
	into the servers query_params and then stops serving.
	"""

	def do_GET(s):
		"""
		Handle a GET request.

		Parses the query parameters and prints a message
		if the flow has completed. Note that we can't detect
		if an error occurred.
		"""
		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.end_headers()
		query = s.path.split("?", 1)[-1]
		query = dict(parse_qsl(query))
		s.server.query_params = query
		s.wfile.write(
			b"<html><head><title>Authentication Status</title></head>"
		)
		s.wfile.write(
			b"<body><p>The authentication flow has completed.</p>"
		)
		s.wfile.write(
			b"</body></html>"
		)

	def log_message(self, format, *args):
		"""
		Do not log messages to stdout while running as command line program.
		"""
		pass


def dumpRequest(request):
	open("/tmp/starcal-request", "a").write(
		f"uri={request.uri!r}\n" +
		f"method={request.method!r}\n" +
		f"headers={request.headers!r}\n" +
		f"body={request.body!r}\n\n\n"
	)


@event_lib.classes.account.register
class GoogleAccount(Account):
	name = "google"
	desc = _("Google")
	paramsOrder = Account.paramsOrder + ("email",)
	params = Account.params + ("email",)

	def __init__(self, aid=None, email=""):
		from oauth2client.client import OAuth2WebServerFlow
		Account.__init__(self, aid)
		self.authFile = splitext(self.file)[0] + ".oauth2"
		self.email = email
		self.flow = OAuth2WebServerFlow(
			client_id="536861675971.apps.googleusercontent.com",
			client_secret="BviBsCKTbXrzY0hZbioS6FAt",
			scope=[
				"https://www.googleapis.com/auth/calendar",
				"https://www.googleapis.com/auth/tasks",
			],
			user_agent=f"{core.APP_NAME}/{core.VERSION}",
		)

	def getData(self):
		data = Account.getData(self)
		data.update({
			"email": self.email,
		})
		return data

	def setData(self, data):
		Account.setData(self, data)
		for attr in ("email",):
			if attr not in data:
				continue
			setattr(self, attr, data[attr])

	def askVerificationCode(self):
		return input("Enter verification code: ").strip()

	def showError(self, error):
		sys.stderr.write(error + "\n")

	def showHttpException(self, e):
		self.showError(
			_("HTTP Error") + "\n" +
			_("Error Code") + ": " + _(e.resp.status) + "\n" +
			_("Error Message") + ": " + _(e._get_reason().strip())
		)

	def authenticate(self):
		global auth_local_webserver
		import socket
		from oauth2client.file import Storage
		storage = Storage(self.authFile)
		credentials = storage.get()
		if credentials and not credentials.invalid:
			return credentials

		if auth_local_webserver:
			success = False
			port_number = 0
			for port in auth_host_port:
				port_number = port
				try:
					httpd = ClientRedirectServer(
						(auth_host_name, port),
						ClientRedirectHandler,
					)
				except socket.error as e:
					log.info(
						f"-------- counld not use port {port} " +
						f"for local web server: {e}"
					)
					pass
				else:
					success = True
					break
			auth_local_webserver = success

		if auth_local_webserver:
			oauth_callback = f"http://{auth_host_name}:{port_number}/"
		else:
			oauth_callback = "oob"
		openUrl(self.flow.step1_get_authorize_url(oauth_callback))

		code = None
		if auth_local_webserver:
			httpd.handle_request()
			if "error" in httpd.query_params:
				self.showError(_("Authentication request was rejected."))
				return
			if "code" in httpd.query_params:
				code = httpd.query_params["code"]
			else:
				self.showError(_(
					"Failed to find \"code\" in the query parameters " +
					"of the redirect."
				))
				return
		else:
			code = self.askVerificationCode()
		try:
			credential = self.flow.step2_exchange(code)
		except Exception as e:
			self.showError(
				_("Authentication has failed") +
				f":\n{e}"
			)
			return
		storage.put(credential)
		credential.set_store(storage)
		return credentials

	def getHttp(self):
		credentials = self.authenticate()
		if not credentials:
			return False
		http = credentials.authorize(httplib2.Http())
		http.request = lambda uri, *args, **kwargs:\
			httplib2.Http.request(http, toStr(uri), *args, **kwargs)
		# http.request("google.com")
		return http

	def getCalendarService(self):
		from apiclient.discovery import build, HttpError
		try:
			return build(
				serviceName="calendar",
				version="v3",
				http=self.getHttp(),
				developerKey=developerKey,
			)
			# returns a Resource instance
		except HttpError as e:
			self.showHttpException(e)

	def getTasksService(self):
		from apiclient.discovery import build, HttpError
		try:
			return build(
				serviceName="tasks",
				version="v1",
				http=self.getHttp(),
				developerKey=developerKey,
			)
		except HttpError as e:
			self.showHttpException(e)

	def addNewGroup(self, title):
		service = self.getCalendarService()
		if not service:
			return
		service.calendars().insert(
			body={
				"kind": "calendar#calendar",
				"summary": title,
			}
		).execute()["id"]

	def deleteGroup(self, remoteGroupId):
		service = self.getCalendarService()
		if not service:
			return
		service.calendars().delete(calendarId=remoteGroupId).execute()

	def fetchGroups(self):
		"""
		return None if successful, or error string if failed
		"""
		service = self.getCalendarService()
		if not service:
			return "no service"  # fix msg FIXME
		groups = []
		for group in service.calendarList().list().execute()["items"]:
			# log.debug("group =", group)
			groups.append({
				"id": group["id"],
				"title": group["summary"],
			})
		self.remoteGroups = groups

	def fetchAllEventsInGroup(self, remoteGroupId):
		service = self.getCalendarService()
		if not service:
			return
		eventsRes = service.events().list(
			calendarId=remoteGroupId,
			orderBy="updated",
		).execute()
		return eventsRes.get("items", [])

	def sync(self, group, remoteGroupId):
		"""
		return None if successful, or error string if failed
		"""
		from apiclient.discovery import HttpError
		#if remoteGroupId=="tasks":  # FIXME
		#	service = self.getTasksService()
		service = self.getCalendarService()
		if not service:
			return "no service"  # fix msg FIXME
		lastSync = group.getLastSync()
		funcStartTime = now()
		# _________________ Pull _________________
		# log.debug("------------------- pulling...")
		kwargs = {
			"calendarId": remoteGroupId,
			"orderBy": "updated",
			"showDeleted": True,  # with event.status == "cancelled",
			"maxResults": syncResultPerPage,
			"timeZone": "GMT",
			"pageToken": 0,
		}
		if lastSync:
			kwargs["updatedMin"] = getIcsTimeByEpoch(lastSync, True)  # FIXME
			# int(lastSync)
		# log.debug(kwargs)
		request = service.events().list(**kwargs)
		# request is a HttpRequest instance
		#dumpRequest(request)
		try:
			geventsRes = request.execute()
		except HttpError as e:
			self.showHttpException(e)
			return str(e)
		#plog.info(geventsRes)
		gevents = geventsRes.get("items", [])
		#plog.info(gevents)
		diff = {}

		def addToDiff(key, here, status, *args):
			value = (status, here) + args
			toAppend = diff.get(key)
			if toAppend is None:
				diff[key] = [value]
			else:
				diff[key].append(value)

		for gevent in gevents:
			remoteIds = (self.id, remoteGroupId, gevent["id"])

			try:
				#eventId = group.eventIdByRemoteIds[remoteIds]
				eventId = gevent["extendedProperties"]["shared"]["starcal_id"]
			except KeyError:
				eventId = None

			bothId = (eventId, gevent["id"])
			if gevent["status"] == "cancelled":
				if eventId is not None:
					addToDiff(bothId, False, STATUS_DELETED)
					#group.remove(group[eventId])
					#group.save()  # FIXME
			if gevent["status"] != "confirmed":  # FIXME
				log.info(gevent["status"], gevent["summary"])
				continue
			event = importEvent(gevent, group)
			if not event:
				# log.debug(f"-------- event can not be pulled: {pformat(gevent)}")
				continue
			event.remoteIds = remoteIds
			if eventId is None:
				addToDiff(bothId, False, STATUS_ADDED, event)
				#event.afterModify()
				#group.append(event)
				#event.save()
				#group.save()
				# log.debug(f"---------- event {event} added in starcal")
			else:
				addToDiff(bothId, False, STATUS_MODIFIED, event)
				#local_event = group[eventId]
				#local_event.copyFrom(event)
				#local_event.save()
		#group.afterSync()  # FIXME
		#group.save()  # FIXME
		# _______________________ Push _______________________
		# log.debug("------------------- pushing...")
		#if remoteGroupId=="tasks":  # FIXME
		for eventId, eventRemoteAttrs in group.deletedRemoteEvents.items():
			(
				deletedEpoch,
				tmp_accountId,
				tmp_remoteGroupId,
				remoteEventId,
			) = eventRemoteAttrs
			if deletedEpoch > funcStartTime:
				continue
			if (tmp_accountId, tmp_remoteGroupId) != (self.id, remoteGroupId):
				del group.deletedRemoteEvents[eventId]
				continue
			bothId = (eventId, remoteEventId)
			addToDiff(bothId, True, STATUS_DELETED)
		for event in group:
			if event.modified > funcStartTime:
				continue
			# log.debug("---------- event {event}")
			remoteEventId = None
			if event.remoteIds:
				if event.remoteIds[:2] == (self.id, remoteGroupId):
					remoteEventId = event.remoteIds[2]
			# log.debug("---------- remoteEventId = {remoteEventId}")
			if remoteEventId and lastSync and event.modified < lastSync:
				log.info(
					f"---------- skipping event {event.summary}" +
					f"(modified = {event.modified} < {lastPush} = lastPush)"
				)
				continue
			bothId = (event.id, remoteEventId)
			addToDiff(bothId, True, STATUS_MODIFIED, event)
			"""
			gevent = exportEvent(event)
			if gevent is None:
				log.info(f"---------- event {event} can not be pushed")
				continue
			gevent["etag"] = calcEtag(gevent)
			# log.debug(f"etag = {gevent['etag']!r}")
			gevent.update({
				"calendarId": remoteGroupId,
				"sequence": group.index(event.id),
				"organizer": {
					"displayName": core.userDisplayName,  # FIXME
					"email": self.email,
				},
			})
			if remoteEventId:
				#gevent["id"] = remoteEventId
				#if not "recurrence" in gevent:
				#	gevent["recurrence"] = None  # or [] FIXME
				request = service.events().update(  # patch or update? FIXME
					eventId=remoteEventId,
					body=gevent,
					calendarId=remoteGroupId
				)
				try:
					request.execute()
				except HttpError as e:
					self.showHttpException(e)
					return str(e)  # FIXME
				else:
					log.info(f"------ event {event} updated on server")
			else:  # FIXME
				request = service.events().insert(
					body=gevent,
					calendarId=remoteGroupId,
					sendNotifications=False,
				)
				#dumpRequest(request)
				try:
					response = request.execute()
				except HttpError as e:
					self.showHttpException(e)
					return str(e)  # FIXME
				# log.debug("response = {pformat(response)}")
				remoteEventId = response["id"]
				log.info(f"----------- event {event} added on server")
			event.remoteIds = [self.id, remoteGroupId, remoteEventId]
			event.save()
			#group.eventIdByRemoteIds[tuple(event.remoteIds)] = event.id
			# use tuple() to avoid: TypeError: unhashable type: "list"
		"""
		group.afterSync()  # FIXME
		group.save()  # FIXME


def printAllEvent(account, remoteGroupId):
	for gevent in account.fetchAllEventsInGroup(remoteGroupId):
		log.info(gevent["summary"], gevent["updated"])


if __name__ == "__main__":
	from scal3 import ui
	account = GoogleAccount.load(1)
	log.info(account.fetchGroups())
	# remoteGroupId = "gi646vjovfrh2u2u2l9hnatvq0@group.calendar.google.com"
	# groupId = 102
	# ui.eventGroups = event_lib.EventGroupsHolder.load()
	# group = ui.eventGroups[groupId]
	# log.debug("group.remoteIds", group.remoteIds)
	# group.remoteIds = (account.id, remoteGroupId)
	# account.sync(group, remoteGroupId)  # 400 Bad Request
	# group.save()
