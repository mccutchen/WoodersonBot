import logging
import random
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
     "High school girls, man. I get older, they stay the same age."),
    ]

soliloquies = [
    'Alright alright alright',

    ("You ought to ditch the two geeks you're in the car with now and get in "
     "with us. But that's all right, we'll worry about that later."),

    ("Let me tell you this, the older you get the more rules they're gonna "
     "try to get you to follow. You just gotta keep livin' man, L-I-V-I-N."),

    "Say, man, you got a joint?",

    "I love them redheads!",
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

def update_status(status, **kwargs):
    api = get_api()
    args = {
        'status': status,
        'lat': reply_lat,
        'lon': reply_lon,
        'place_id': reply_place_id,
        'display_coordinates': True,
        }
    args.update(kwargs)
    return api.update_status(**args)

def send_reply(user_id, tweet_id, tweet, reply):
    existing_reply = Reply.get_by_id(tweet_id)
    if existing_reply:
        logging.warn('Skipping existing reply: %r', existing_reply)
        return

    logging.info('Tweet: %s', tweet)
    logging.info('Reply: %s', reply)
    try:
        status = update_status(reply, in_reply_to_status_id=tweet_id)
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

def should_reply(user, tweet):
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
    if should_reply(user, tweet):
        return '@%s %s' % (user, base_reply)
    else:
        return None

def socialize():
    # We'll gather pending replies here so that we can shuffle them before
    # queuing them up for execution.
    reply_args = []

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
            api = get_api()
            results = api.search(**args)
        except Exception, e:
            logging.exception('Error searching with params %r: %s', args, e)
            continue
        else:
            if not results:
                logging.warn('No results for search %r', args)
                continue

            for result in results:
                reply = make_reply(result.from_user, result.text, response)
                if reply:
                    args = {
                        'user_id': result.from_user_id,
                        'tweet_id': result.id,
                        'tweet': result.text,
                        'reply': reply,
                        }
                    reply_args.append(args)
                else:
                    logging.warn('Not replying to: %s', result.text)

            logging.info('Recording last ID for %r: %r', query, results[0].id)
            memcache.set(query, results[0].id)

    random.shuffle(reply_args)
    for args in reply_args:
        deferred.defer(send_reply, **args)

def soliloquize():
    key = 'last_soliloquy'
    last_soliloquy = memcache.get(key)
    next_soliloquy = random.choice(soliloquies)
    while last_soliloquy and next_soliloquy == last_soliloquy:
        next_soliloquy = random.choice(soliloquies)
    logging.info('Soliloquizing: %s', next_soliloquy)
    try:
        status = update_status(next_soliloquy)
    except Exception, e:
        logging.exception('Error updating status: %s', e)
    else:
        logging.info('Updated status: %s (%s)', next_soliloquy, status.id)
        memcache.set(key, next_soliloquy)
