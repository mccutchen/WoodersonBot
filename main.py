import webapp2
import wooderson


class IndexHandler(webapp2.RequestHandler):
  def get(self):
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write('Alright alright alright')


class SocializeHandler(webapp2.RequestHandler):
    def get(self):
        replies = wooderson.socialize()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('OK')


public_urls = [('/', IndexHandler)]
private_urls = [('/cron/socialize', SocializeHandler)]

public_app = webapp2.WSGIApplication(public_urls, debug=True)
private_app = webapp2.WSGIApplication(private_urls, debug=True)
