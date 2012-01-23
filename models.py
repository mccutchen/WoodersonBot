from google.appengine.ext import db


class Reply(db.Model):
    """A record of an exchange with a Twitter user. Each entity's key should
    be the same as its tweet_id.
    """
    tweet_id = db.IntegerProperty()
    tweet = db.StringProperty(multiline=True, indexed=False)
    user_id = db.IntegerProperty()
    reply = db.StringProperty(multiline=True, indexed=False)
    reply_id = db.IntegerProperty()

    def __repr__(self):
        return '<Reply %s>' % ' '.join(
            '%s=%r' % (key, getattr(self, key)) for key in self.properties())

    def __str__(self):
        return repr(self)
