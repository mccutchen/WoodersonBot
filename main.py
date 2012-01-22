import webapp2
import wooderson


class SocializeHandler(webapp2.RequestHandler):
    def get(self):
        wooderson.socialize()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('OK')


urls = [('/cron/socialize', SocializeHandler)]
app = webapp2.WSGIApplication(urls, debug=True)
