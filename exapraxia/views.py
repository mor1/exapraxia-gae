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

'''View handlers for Exapraxia, the Unproxy.'''

import sys, logging, traceback, urllib, urlparse, re
log = logging.info
err = logging.exception

from google.appengine.api import users, urlfetch, memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.runtime import apiproxy_errors

import models

EXAPRAXIA_URL = "https://1-test.latest.exapraxia.appspot.com"
## EXAPRAXIA_URL = "http://localhost:8080" ## for debug

MAX_CONTENT_SIZE = 10**6
MAX_URL_DISPLAY_LENGTH = 50

def fmtexc(e, with_tb=False, clear=True):
    tb = traceback.extract_tb(sys.exc_info()[2])
    s = '%s: %s' % (e.__class__.__name__, str(e))
    if with_tb:
        s += '\n%s' % ('\n'.join([ '#   %s@%s:%s' % (filename, lineno, func)
                                   for (filename,lineno,func,_) in tb ]),)
    if clear: sys.exc_clear()
    return s


REWRITE_TYPES = frozenset([
    "text/html",
    "text/css",
    "text/javascript",
    ])

QUO_RES = r'(?P<quote>["\']?)'
URL_RES = r'(?P<url>[^\'" \t\)]*)'
TAG_RES = r'(?P<tag>src|href|action|url|background)[\t ]*=[\t ]*'+QUO_RES

BASE_REL_URL_RES = r'(?!http(s?))/(?!(/)|(http(s?)://)|(url\())'+URL_RES
BASE_REL_URL_RE = re.compile(TAG_RES+BASE_REL_URL_RES, re.I)

ABS_URL_RES = r'(http(s?)://)'+URL_RES
ABS_URL_RE = re.compile(TAG_RES+ABS_URL_RES, re.I)
                             
BACKGROUND_RES = r'(?P<tag>url[ \t]*\()'+QUO_RES
BACKGROUND_ABS_RE = re.compile(BACKGROUND_RES+ABS_URL_RES, re.I)
BACKGROUND_REL_RE = re.compile(BACKGROUND_RES+BASE_REL_URL_RES, re.I)

CSS_IMPORT_RES = r'@import[ \t]*'+QUO_RES
CSS_IMPORT_RE = re.compile(CSS_IMPORT_RES+ABS_URL_RES, re.I)

SCRIPT_RES = r'script:[ \t]*'+QUO_RES
SCRIPT_ABS_RE = re.compile(SCRIPT_RES+ABS_URL_RES, re.I)
SCRIPT_REL_RE = re.compile(SCRIPT_RES+BASE_REL_URL_RES, re.I)

MAP_RES = r'map:[ \t]*'+QUO_RES
MAP_RE = re.compile(MAP_RES+ABS_URL_RES, re.I)

FOOT_RES = r'foot:[ \t]*[[][ \t]*'+QUO_RES
FOOT_RE = re.compile(FOOT_RES+BASE_REL_URL_RES, re.I)

def rewrite(url, content):

    url = urlparse.urlsplit(url)

    newurl = "%s/%s" % (EXAPRAXIA_URL, url.netloc)

    content = re.sub(ABS_URL_RE,        "\g<tag>=\g<quote>%s/\g<url>" % (EXAPRAXIA_URL,), content)
    content = re.sub(BASE_REL_URL_RE,   "\g<tag>=\g<quote>%s/\g<url>" % (newurl,), content)

    content = re.sub(BACKGROUND_ABS_RE, "\g<tag>\g<quote>%s/\g<url>" % (EXAPRAXIA_URL,), content)
    content = re.sub(BACKGROUND_REL_RE, "\g<tag>\g<quote>%s/\g<url>" % (newurl,), content)

    content = re.sub(SCRIPT_ABS_RE,     "script: \g<quote>%s/\g<url>" % (EXAPRAXIA_URL,), content)
    content = re.sub(SCRIPT_REL_RE,     "script: \g<quote>%s/\g<url>" % (newurl,), content)

    content = re.sub(CSS_IMPORT_RE,     "@import \g<quote>%s/\g<url>" % (EXAPRAXIA_URL,), content)
    content = re.sub(MAP_RE,            "map: \g<quote>%s/\g<url>" % (EXAPRAXIA_URL,), content)
    content = re.sub(FOOT_RE,           "foot:[ \g<quote>%s/\g<url>" % (newurl,), content)
    
##     log(content)
    return content.decode("latin1").encode("utf8")

def http404(resp):
    resp.set_status(404)

def get_user():
    user = users.get_current_user()
    if not user: return 
    uid = user.user_id()

    u = db.get(db.Key.from_path('User', uid))
    if not u: u = models.User(key_name=uid)
    u.put()
    
    return u
    
class Exapraxia(webapp.RequestHandler):
    def options(self):
        log("req: %s" % (self.request,))

    def get(self):
        log("req: '%s'" % (self.request.path[1:],))

        ## check authorised user
        u = get_user()
        if not u: return http404(self.response)
        if not u.auth: return http404(self.response)
        
        ## canonicalise requested URL
        url = urllib.unquote(self.request.path[1:]) ## remove leading /
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://%s" % (url,)
        log("url: '%s'" % (url,))
        
        ## fetch URL
        try:
            headers = dict(self.request.headers.items())
##             log("req hdrs:%s" % (headers,))
            response = urlfetch.fetch(url, headers)
        except urlfetch.Error, exc:
            err("EXC: urlfetch(%s): %s" % (url, fmtexc(exc),))
            self.response.set_status(404)
            return
        
        except apiproxy_errors.Error, exc:
            err("EXC: urlfetch(%s): %s" % (url, fmtexc(exc, with_tb=True, clear=False),))
            raise

##         log("resp hdrs:%s" % (response.headers,))

        ## rewrite embedded urls
        ct = [ v for (k,v) in response.headers.iteritems() if k.lower() == "content-type" ]
        content = response.content
        if len(ct) > 0:
            for rt in REWRITE_TYPES:
                if ct[-1].startswith(rt):
                    content = rewrite(url, content)[:MAX_CONTENT_SIZE]

        ## done!
        for (k,v) in response.headers.items(): self.response.headers.add_header(k, v)
        self.response.out.write(content)
