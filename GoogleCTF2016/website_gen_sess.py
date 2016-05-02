import json
import logging
import os
import jinja2
import webapp2

from webapp2_extras import sessions


import util

class RequestHandler(webapp2.RequestHandler):
    """Base request handler for Mannequin Moments."""
    jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates')
            )

    def dispatch(self):
        self._session_store = sessions.get_store(request=self.request)

        try:
            #super(RequestHandler, self).dispatch()
            pass
        finally:
            self._session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self._session_store.get_session()

    def render(self, tpl_name, **args):
        tmpl = self.jinja_env.get_template(tpl_name)
        args['logged_in'] = True if self.session.get('user') else False
        self.response.out.write(tmpl.render(**args))



class HomeHandler(RequestHandler):
    def get(self):
        self.render('index.tpl')


class LoginHandler(RequestHandler):
    def get(self):
        self.render('login.tpl')

    def post(self):
        user = None
        username = 'admin'
        #password = self.request.get('password') or None
	# Change #1281 - emergency maintenance due to security issues
	# user = redo auth.
        self.session['user'] = username
        #return webapp2.redirect('/', response=self.response)




config = {
        'webapp2_extras.sessions': {
            'secret_key': 'a793134b-c2c5-4cbf-973b-64ff7eea863a',
            'name': 'mannequin-moments',
        }
}

app = webapp2.WSGIApplication([
    webapp2.Route('/', HomeHandler),
    webapp2.Route('/login', LoginHandler)
], config=config)

p=os.environ.__dict__

request = webapp2.Request(p)
response=webapp2.Response()
request.app = app
a=LoginHandler(request,response)
a.dispatch()
a.post()
a.dispatch()
#a.session.set('user','admin')
print a.response
