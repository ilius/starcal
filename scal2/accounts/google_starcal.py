# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

developerKey = 'AI39si4QJ0bmdZJd7nVz0j3zuo1JYS3WUJX8y0f2mvGteDtiKY8TUSzTsY4oAcGlYAM0LmOxHmWWyFLU'## FIXME

import sys
from os.path import splitext
import socket
import BaseHTTPServer

from pprint import pprint, pformat

try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl

import httplib2
from httplib2 import *

from scal2.path import *

sys.path.append(join(rootDir, 'google_api_client'))## FIXME


from apiclient.discovery import build
from apiclient.http import HttpRequest

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow


from scal2.utils import toUnicode, toStr
from scal2.ics import *
from scal2.locale_man import tr as _
from scal2 import core
from scal2.core import to_jd, jd_to, DATE_GREG, compressLongInt

from scal2 import event_lib
from scal2.event_lib import Account


auth_local_webserver = True
auth_host_name = 'localhost'
auth_host_port = [8080, 8090]


decodeIcsStartEnd = lambda value: {
    ('dateTime' if 'T' in value else 'date'): value,
    'timeZone': 'GMT',
}

def encodeIcsStartEnd(value):
    timeZone = value.get('timeZone', 'GMT')## FIXME
    if 'date' in value:
        icsValue = value['date'].replace('-', '')
    elif 'dateTime' in value:
        icsValue = value['dateTime'].replace('-', '').replace(':', '')
    else:
        raise ValueError('bad gcal start/end value %r'%value)
    return icsValue


def exportEvent(event):
    if not event.changeMode(DATE_GREG):
        return
    icsData = event.getIcsData(True)
    if not icsData:
        return
    gevent = {
        'kind': 'calendar#event',
        'summary': toUnicode(event.summary),
        'description': toUnicode(event.description),
        'attendees': [],
        'status': 'confirmed',
        'visibility': 'default',
        'guestsCanModify': False,
        'reminders': {
            'overrides': {
                'minutes': event.getNotifyBeforeMin(),
                'method': 'popup',## FIXME
            },
        },
        'extendedProperties':{
            'shared': {
                'starcal_type': event.name,
            },
        }
    }
    for key, value in icsData:
        key = key.upper()
        if key=='DTSTART':
            gevent['start'] = decodeIcsStartEnd(value)
        elif key=='DTEND':
            gevent['end'] = decodeIcsStartEnd(value)
        elif key in ('RRULE', 'RDATE', 'EXRULE', 'EXDATE'):
            if not 'recurrence' in gevent:
                gevent['recurrence'] = []
            gevent['recurrence'].append(key + ':' + value)
        elif key=='TRANSP':
            gevent['transparency'] = value.lower()
        #elif key=='CATEGORIES':
    return gevent

#def exportToEvent(event, group, gevent):## FIXME


def importEvent(gevent, group):
    if gevent['status'] != 'confirmed':## FIXME
        return
    open('/tmp/gevent.js', 'a').write('%s\n\n'%pformat(gevent))
    icsData = [
        ('DTSTART', encodeIcsStartEnd(gevent['start'])),
        ('DTEND', encodeIcsStartEnd(gevent['end'])),
    ]
    ##
    recurring = False
    if 'recurrence' in gevent:
        key, value = gevent['recurrence'].upper().split(':')## multi line? FIXME
        icsData.append((key, value))
        recurring = True
    try:
        eventType = gevent['extendedProperties']['shared']['starcal_type']
    except KeyError:
        if recurring:
            eventType = 'custom'
        else:
            eventType = 'task'
    ##
    event = group.createEvent(eventType)
    event.mode = DATE_GREG ## FIXME
    if not event.setIcsDict(dict(icsData)):
        return
    event.summary = toStr(gevent['summary'])
    event.description = toStr(gevent.get('description', ''))
    if 'reminders' in gevent:
        try:
            minutes = gevent['reminders']['overrides']['minutes']
        except:
            pass## FIXME
        else:
            self.notifyBefore = (minutes, 60)
    return event


def setEtag(gevent):
    gevent['etag'] = compressLongInt(abs(hash(repr(gevent))))

class ClientRedirectServer(BaseHTTPServer.HTTPServer):
  """A server to handle OAuth 2.0 redirects back to localhost.

  Waits for a single request and parses the query parameters
  into query_params and then stops serving.
  """
  query_params = {}


class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """A handler for OAuth 2.0 redirects back to localhost.

  Waits for a single request and parses the query parameters
  into the servers query_params and then stops serving.
  """

  def do_GET(s):
    """Handle a GET request.

    Parses the query parameters and prints a message
    if the flow has completed. Note that we can't detect
    if an error occurred.
    """
    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    query = s.path.split('?', 1)[-1]
    query = dict(parse_qsl(query))
    s.server.query_params = query
    s.wfile.write("<html><head><title>Authentication Status</title></head>")
    s.wfile.write("<body><p>The authentication flow has completed.</p>")
    s.wfile.write("</body></html>")

  def log_message(self, format, *args):
    """Do not log messages to stdout while running as command line program."""
    pass


def dumpRequest(request):
    open('/tmp/starcal-request', 'a').write('uri=%r\nmethod=%r\nheaders=%r\nbody=%r\n\n\n'%(
        request.uri,
        request.method,
        request.headers,
        request.body,
    ))


@event_lib.classes.account.register
class GoogleAccount(Account):
    name = 'google'
    desc = _('Google')
    jsonParams = Account.jsonParams + ('email',)
    params = Account.params + ('email',)
    def __init__(self, aid=None, email=''):
        Account.__init__(self, aid)
        self.authFile = splitext(self.file)[0] + '.oauth2'
        self.email = email
        self.flow = OAuth2WebServerFlow(
            client_id='536861675971.apps.googleusercontent.com',
            client_secret='BviBsCKTbXrzY0hZbioS6FAt',
            scope=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/tasks',
            ],
            user_agent='%s/%s'%(core.APP_NAME, core.VERSION),
        )
    def getData(self):
        data = Account.getData(self)
        data.update({
            'email': self.email,
        })
        return data
    def setData(self, data):
        Account.setData(self, data)
        for attr in ('email',):
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
    askVerificationCode = lambda self: raw_input('Enter verification code: ').strip()
    def showError(self, error):
        sys.stderr.write(error+'\n')
    def authenticate(self):
        global auth_local_webserver
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
                    pass
                else:
                    success = True
                    break
            auth_local_webserver = success

        if auth_local_webserver:
            oauth_callback = 'http://%s:%s/' % (auth_host_name, port_number)
        else:
            oauth_callback = 'oob'
        core.openUrl(self.flow.step1_get_authorize_url(oauth_callback))

        code = None
        if auth_local_webserver:
            httpd.handle_request()
            if 'error' in httpd.query_params:
                self.showError('Authentication request was rejected.')
                return
            if 'code' in httpd.query_params:
                code = httpd.query_params['code']
            else:
                self.showError('Failed to find "code" in the query parameters of the redirect.')
                return
        else:
            code = self.askVerificationCode()
        try:
            credential = self.flow.step2_exchange(code)
        except Exception as e:
            self.showError('Authentication has failed: %s'%e)
            return
        storage.put(credential)
        credential.set_store(storage)
        return credentials
    def getHttp(self):
        credentials = self.authenticate()
        if not credentials:
            return False
        return credentials.authorize(httplib2.Http())
    getCalendarService = lambda self: build(
        serviceName='calendar',
        version='v3',
        http=self.getHttp(),
        developerKey=developerKey,
    )
    getTasksService = lambda self: build(
        serviceName='tasks',
        version='v1',
        http=self.getHttp(),
        developerKey=developerKey,
    )
    addNewGroup = lambda self, title: self.getCalendarService().calendars().insert(
        body={
            'kind': 'calendar#calendar',
            'summary': title,
        }
    ).execute()['id']
    def deleteGroup(self, remoteGroupId):
        self.getCalendarService().calendars().delete(calendarId=remoteGroupId).execute()
    def fetchGroups(self):
        service = self.getCalendarService()
        groups = []
        for group in service.calendarList().list().execute()['items']:
            #print('group =', group)
            groups.append({
                'id': group['id'],
                'title': group['summary'],
            })
        self.remoteGroups = groups
        return True
    def fetchAllEventsInGroup(self, remoteGroupId):
        eventsRes = self.getCalendarService().events().list(
            calendarId=remoteGroupId,
            orderBy='updated',
        ).execute()
        return eventsRes.get('items', [])
    def sync(self, group, remoteGroupId, resPerPage=50):
        service = self.getCalendarService()
        ## if remoteGroupId=='tasks':## FIXME
        lastSync = group.getLastSync()
        ########################### Pull
        kwargs = dict(
            calendarId=remoteGroupId,
            orderBy='updated',
            showDeleted=True,## with event.status == 'cancelled',
            maxResults=resPerPage,
            #timeZone="GMT",
            #pageToken=0,
        )
        if lastSync:
            kwargs['updatedMin'] = getIcsTimeByEpoch(lastSync, True) ## FIXME
            ## int(lastSync)
        request = service.events().list(**kwargs)
        dumpRequest(request)
        geventsRes = request.execute()
        #pprint(geventsRes)
        try:
            gevents = geventsRes['items']
        except KeyError:
            gevents = []
        for gevent in gevents:
            event = importEvent(gevent, group)
            if not event:
                print('---------- event %s can not be pulled'%event)
                continue
            remoteIds = (self.id, remoteGroupId, gevent['id'])
            eventId = group.eventIdByRemoteIds.get(remoteIds, None)
            if eventId is None:
                event.afterModify()
                group.append(event)
                event.save()
                group.save()
                print('---------- event %s added in starcal'%event.summary)
            else:
                try:
                    event = group[eventId]
                except Exception as e:
                    pass
        ########################### Push
        ## if remoteGroupId=='tasks':## FIXME
        for event in group:
            #print('---------- event %s'%event.summary)
            remoteEventId = None
            if event.remoteIds:
                if event.remoteIds[0]==self.id and event.remoteIds[1]==remoteGroupId:
                    remoteEventId = event.remoteIds[2]
            #print('---------- remoteEventId = %s'%remoteEventId)
            if remoteEventId and lastSync and event.modified < lastSync:
                #print('---------- skipping event %s (modified = %s < %s = lastPush)'%(event.summary, event.modified, lastPush))
                continue
            gevent = exportEvent(event)
            if gevent is None:
                print('---------- event %s can not be pushed'%event.summary)
                continue
            setEtag(gevent)
            #print('etag = %r'%gevent['etag'])
            gevent.update({
                'calendarId': remoteGroupId,
                'sequence': group.index(event.id),
                'organizer': {
                    'displayName': core.userDisplayName,## FIXME
                    'email': self.email,
                },
            })
            if remoteEventId:
                #gevent['id'] = remoteEventId
                #if not 'recurrence' in gevent:
                #    gevent['recurrence'] = None ## or [] FIXME
                service.events().update(## patch or update? FIXME
                    eventId=remoteEventId,
                    body=gevent,
                    calendarId=remoteGroupId
                ).execute()
                print('---------- event %s updated on server'%event.summary)
            else:## FIXME
                request = service.events().insert(
                    body=gevent,
                    calendarId=remoteGroupId,
                    sendNotifications=False,
                )
                #dumpRequest(request)
                response = request.execute()
                #print('response = %s'%pformat(response))
                remoteEventId = response['id']
                print('----------- event %s added on server'%event.summary)
            event.remoteIds = [self.id, remoteGroupId, remoteEventId]
            event.save()
            group.eventIdByRemoteIds[tuple(event.remoteIds)] = event.id## TypeError: unhashable type: 'list'
        group.afterSync()## FIXME
        group.save()## FIXME
        return True


def printAllEvent(account, remoteGroupId):
    for gevent in account.fetchAllEventsInGroup(remoteGroupId):
        print(gevent['summary'], gevent['updated'])


if __name__=='__main__':
    from scal2 import ui
    account = GoogleAccount(aid=1)
    account.load()
    remoteGroupId = 'gi646vjovfrh2u2u2l9hnatvq0@group.calendar.google.com'
    groupId = 66
    ui.eventGroups.load()
    group = ui.eventGroups[groupId]
    #print('group.remoteIds', group.remoteIds)
    group.remoteIds = (account.id, remoteGroupId)
    account.sync(group, remoteGroupId)
    group.save()






