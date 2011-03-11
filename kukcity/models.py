## Copyright (C) 2011 Richard Mortier <mort@cantab.net>
##
## This program is free software: you can redistribute it and/or
## modify it under the terms of the GNU Affero General Public License
## as published by the Free Software Foundation, either version 3 of
## the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public
## License along with this program.  If not, see
## <http://www.gnu.org/licenses/>.

"""Model schema for Kukcity, George's Twitter experiment."""

import sys, logging, traceback, urllib, urlparse
log = logging.info
err = logging.exception

from google.appengine.ext import db
from google.appengine.api import datastore_errors, urlfetch

class SVC_STATUS:
    needauth = 'NEEDAUTH'
    authorized = 'AUTHORIZED'

class SYNC_STATUS:
    unsynchronized = 'UNSYNCHRONIZED'
    inprogress = 'INPROGRESS'
    halting = 'HALTING'
    synchronized = 'SYNCHRONIZED'

class SyncService(db.Model):
    svcname = db.StringProperty()
    username = db.StringProperty()
    status = db.StringProperty(default=SVC_STATUS.needauth)
    
    def todict(self):
        return { 'svcname': self.svcname,
                 'username': self.username,
                 'status': self.status,
                 'threads': map(lambda x:x.todict(), self.threads),
                 }
    def tojson(self):
        return json.dumps(self.todict(), indent=2)

    @staticmethod
    def of_service(svcname):
        s = secret.OAuth.all().filter("service =", svcname).get()
        username = s.username if s else None
        status = SVC_STATUS.authorized if s else SVC_STATUS.needauth
        
        ss = db.GqlQuery("SELECT * FROM SyncService WHERE svcname=:s AND username=:u",
                         s=svcname, u=username).get()
        if not ss:
            ss = SyncService(svcname=svcname, username=username, status=status)
        ss.username = username
        ss.status = status
        ss.put()
        return ss
            




class User(db.Model):
    user = db.UserProperty(required=True, auto_current_user_add=True)
    auth = db.BooleanProperty(required=True, default=False)
    ctime = db.DateTimeProperty(auto_now_add=True)
    atime = db.DateTimeProperty(auto_now=True)

class Access(db.Model):
    user = db.ReferenceProperty(User, collection_name="accesses", required=True)
    uri = db.LinkProperty(required=True)
    ctime = db.DateTimeProperty(auto_now_add=True)
    atime = db.DateTimeProperty(auto_now=True)
