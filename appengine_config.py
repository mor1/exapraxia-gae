## from http://code.google.com/appengine/docs/python/tools/appstats.html#Installing_the_Event_Recorder

def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app
