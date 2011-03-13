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

import sys, logging, datetime, time
log = logging.info
err = logging.exception

from django.utils import simplejson as json
from google.appengine.ext import db

def datetime_as_float(dt):
    '''Convert a datetime.datetime into a microsecond-precision float.'''
    return time.mktime(dt.timetuple())+(dt.microsecond/1e6)

class SYNC_STATUS:
    unsynchronized = 'UNSYNCHRONIZED'
    inprogress = 'INPROGRESS'
    synchronized = 'SYNCHRONIZED'

class SyncStatus(db.Model):
    status = db.StringProperty(default=SYNC_STATUS.unsynchronized, required=True)
    last_sync = db.DateTimeProperty()

    def todict(self):
        ## hack: mutual recursion ahoy.  bah.
        last_sync = datetime_as_float(self.last_sync) if self.last_sync else None
        return { 'status': self.status,
                 'last_sync': last_sync,
                 }
    def tojson(self):
        return json.dumps(self.todict(), indent=2)

    def put(self):
        if self.status == SYNC_STATUS.synchronized:
            self.last_sync = datetime.datetime.now()
        super(SyncStatus, self).put()

class Tweet(db.Model):
    raw = db.TextProperty(required=True)
    txt = db.StringProperty(required=True)
