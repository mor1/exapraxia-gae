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

"""View handlers for Kukcity, George's Twitter experiment."""

import logging, urllib
log = logging.info

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from google.appengine.api import users
from django.utils import simplejson as json

import kukcity.models as models

COUNT = 80
HASHTAG = '#kukcity'

class Root(webapp.RequestHandler):
    def get(self):
        tweets = [ json.loads(t.raw) for t in models.Tweet.all().order('__key__') ]

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(tweets))

class Cron(webapp.RequestHandler):
    def get(self):
        taskqueue.add(url="/kukcity/sync/start", method="POST")

class Sync(webapp.RequestHandler):
    def get(self, cmd):
        ss = models.SyncStatus.get_by_key_name("twitter-status")
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(ss.tojson())

    def post(self, cmd):
        if cmd == "start":
            s = models.SyncStatus.get_or_insert("twitter-status")
            if s.status != models.SYNC_STATUS.inprogress:
                taskqueue.add(url="/kukcity/tweets/", method="GET")
                s.status = models.SYNC_STATUS.inprogress
                
            s.put()

        elif cmd == "stop":
            s = models.SyncStatus.get()
            if s.status == models.SYNC_STATUS.inprogress:
                s.status = models.SYNC_STATUS.unsynchronized
                s.put()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(s.tojson())

class Tweets(webapp.RequestHandler):
    def get(self):
        ps = { 'q': HASHTAG, 'rpp': COUNT, }
        max_id = self.request.GET.get("max_id")
        if max_id: ps['max_id'] = max_id

        page = self.request.GET.get("page")
        if page: ps['page'] = page
        
        url = "http://search.twitter.com/search.json?%s" % (urllib.urlencode(ps),)
        log("url:%s" % url)
        res = urlfetch.fetch(url)
        log("res:%s\nhdr:%s" % (res.content, res.headers))
        js = json.loads(res.content)

        if 'error' in js: ## retry after specified time
            retry = int(res.headers.get('retry-after', '300'))
            taskqueue.add(url=self.request.url, countdown=retry+2, method="GET")

        else:
            if 'results' in js:
                for tw in js['results']:
                    t = models.Tweet.get_or_insert(
                        tw['id_str'], raw=json.dumps(tw), txt=tw['text'])
                    t.put()

            if 'next_page' in js:
                ## page=2&max_id=46480544355192832&rpp=2&q=%23kukcity
                next_page = "%s%s" % (self.request.path_url, js['next_page'],)
                taskqueue.add(url=next_page, method="GET")

            else:
                s = models.SyncStatus.get_by_key_name("twitter-status")
                s.status = models.SYNC_STATUS.synchronized
                s.put()
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(js, indent=2))
