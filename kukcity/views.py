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

import logging
log = logging.info

from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from django.utils import simplejson as json

import support.oauth as oauth
import support.secret as secret
import models

import twapp
app_key = twapp.app_key"loP38tlepqhkek5dHZl3w"
app_secret = twapp.app_secret"28Ze4D7OPlrhfg71E0HPGevnyI58IQe6GIhyhlxciI"

def base_url(req):
    bu = "%s://%s:%s/kukcity" % (
        req.scheme, req.environ['SERVER_NAME'], req.environ['SERVER_PORT'])
    return bu

def login_url(req): return "%s/login" % base_url(req)
def callback_url(req): return "%s/verify" % base_url(req)
 
class Login(webapp.RequestHandler):
    def get(self):
        client = oauth.TwitterClient(
            app_key, app_secret, callback_url(self.request))
        self.redirect(client.get_authorization_url())

class Verify(webapp.RequestHandler):
    def get(self):
        client = oauth.TwitterClient(app_key, app_secret, callback_url)
        auth_token = self.request.GET.get("oauth_token")
        auth_verifier = self.request.GET.get("oauth_verifier")
        user_info = client.get_user_info(auth_token, auth_verifier=auth_verifier)
        user_secret = user_info['secret']
        username = user_info['username']
        s = secret.OAuth(service="twitter", token=user_info['token'],
                         secret=user_secret, username=username)
        s.put()
        self.redirect("/")

class Cron(webapp.RequestHandler):
    def get(self):
        taskqueue.add(url="/kukcity/sync/start", method="POST")

class Sync(webapp.RequestHandler):
    def get(self, cmd):
        ss = models.SyncService.of_service("twitter")
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(ss.tojson())

    def post(self, cmd):
        ss = models.SyncService.of_service("twitter")
        if not ss or ss.status == models.SVC_STATUS.needauth:
            self.response.set_status(400)
            return
        
        u = "/kukcity/tweets/?sync=1"
        if cmd == "start":
            s = models.SyncStatus.all().filter(
                "service =", ss).filter("thread =", u).get()
            if not s: s = models.SyncStatus(service=ss, thread=u)

            if s.status != models.SYNC_STATUS.inprogress:
                taskqueue.add(url=u, method="GET")
                s.status = models.SYNC_STATUS.inprogress
                
            s.put()

        elif cmd == "stop":
            s = models.SyncStatus.all().filter(
                "service =", ss).filter("thread =", u).get()
            if not s: continue

            if s.status == models.SYNC_STATUS.inprogress:
                s.status = models.SYNC_STATUS.unsynchronized
                s.put()

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(ss.tojson())
