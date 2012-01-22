import webapp2
import wooderson


class SocializeHandler(webapp2.RequestHandler):
    def get(self):
        wooderson.socialize()
        self.response.headers['Content-Type'] = 'text/plain'
        return self.response.out.write('OK')


class SoliloquizeHandler(webapp2.RequestHandler):
    def get(self):
        wooderson.soliloquize()
        self.response.headers['Content-Type'] = 'text/plain'
        return self.response.out.write('OK')


urls = [('/cron/socialize', SocializeHandler),
        ('/cron/soliloquize', SoliloquizeHandler)]
app = webapp2.WSGIApplication(urls, debug=True)
