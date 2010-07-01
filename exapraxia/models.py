## Copyright (C) 2010 Richard Mortier <mort@cantab.net>
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

'''Model schema for Exapraxia, the Unproxy.'''

import sys, logging, traceback, urllib, urlparse
log = logging.info
err = logging.exception

from google.appengine.ext import db
from google.appengine.api import datastore_errors, urlfetch

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
