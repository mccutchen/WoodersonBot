import logging
import re

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import deferred
from ext import tweepy

from models import Reply
import secrets


queries = [
    ('"I didn\'t" OR "I don\'t"',
     "It'd be a lot cooler if you did"),

    ('"high school girls"',
     ("That's what I love about these high school girls, man. I get older, "
      "they stay the same age.")),
    ]

# Where is Wooderson tweeting from? This is the latitude/longitude for the
# shopping center where they filmed the Emporium scenes:
# http://www.flickr.com/photos/jhwells/4008519023/
reply_lat = 30.334455
reply_lon = -97.721737
reply_place_id = 'c3f37afa9efcf94b'

def get_api():
    auth = tweepy.OAuthHandler(secrets.consumer_key, secrets.consumer_secret)
    auth.set_access_token(secrets.access_token, secrets.access_token_secret)
    return tweepy.API(auth)

def send_reply(user_id, tweet_id, tweet, reply):
    existing_reply = Reply.get_by_id(tweet_id)
    if existing_reply:
        logging.warn('Skipping existing reply: %r', existing_reply)
        return

    logging.info('Tweet: %s', tweet)
    logging.info('Reply: %s', reply)
    try:
        api = get_api()
        status = api.update_status(
            status=reply, in_reply_to_status_id=tweet_id,
            lat=reply_lat, lon=reply_lon, place_id=reply_place_id,
            display_coordinates=True)
    except Exception, e:
        logging.exception('Error updating status: %s', e)
    else:
        key = db.Key.from_path('Reply', status.id)
        Reply(
            key=key,
            tweet_id=tweet_id,
            tweet=tweet,
            user_id=user_id,
            reply=reply,
            reply_id=status.id).put()

def should_reply(tweet):
    """Determines whether Wooderson should reply to the given tweet. For now,
    he just ignores old-style RTs.
    """
    return re.search(r'\bRT\b', tweet) is None

def make_reply(user, tweet, base_reply):
    """Builds Wooderson's reply to the given tweet by the given user, based on
    the given "base" reply text. Right now, just prepend the user's Twitter
    handle to the base reply. Potential improvements: Reply-all if the tweet
    is itself a reply.
    """
    return '@%s %s' % (user, base_reply)

def socialize():
    api = get_api()
    for query, response in queries:
        last_id = memcache.get(query)
        logging.info('Searching for %r since %r', query, last_id)
        args = {
            'q': query,
            'result_type': 'mixed',
            'include_entities': False,
            }
        if last_id is not None:
            args['since_id'] = last_id

        try:
            results = api.search(**args)
        except Exception, e:
            logging.exception('Error searching with params %r: %s', args, e)
            continue
        else:
            if not results:
                logging.warn('No results for search %r', args)
                continue

            for result in results:
                if should_reply(result.text):
                    reply = make_reply(
                        result.from_user, result.text, response)
                    deferred.defer(
                        send_reply,
                        user_id=result.from_user_id,
                        tweet_id=result.id,
                        tweet=result.text,
                        reply=reply)
                else:
                    logging.warn('Not replying to: %s', result.text)

            logging.info('Recording last ID for %r: %r', query, results[0].id)
            memcache.set(query, results[0].id)
