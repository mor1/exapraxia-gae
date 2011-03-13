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

"""Entry points for Kukcity, George's Twitter experiment."""

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import kukcity.views as views

urls = map(
    lambda (p,c): (r'^/kukcity/%s' % p, c),
    [ (r'?$', views.Root),
      (r'cron/?$', views.Cron),
      (r'sync(?:/(?P<cmd>start|stop))?/?$', views.Sync),
      (r'tweets/?$', views.Tweets),

      ## (r'login/?$', views.Login),
      ## (r'verify/?$', views.Verify),
      
      ])
    
application = webapp.WSGIApplication(urls, debug=True)
def main(): run_wsgi_app(application) 
if __name__ == "__main__": main()
