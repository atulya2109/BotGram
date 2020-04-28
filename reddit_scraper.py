import praw
import json
import pickle 
import os
import logging 

logger = logging.getLogger(__name__)

def loginReddit():

    if not os.path.isfile(os.path.join(os.path.curdir,'reddit.pickle')):
        
        logger.info('Pickled File Not Found. Logging In Using Credentials')
        reddit = praw.Reddit(client_id = 'u71M0v8DK3lAdA',
                     client_secret = 'GgCpHfpJrNWPZywOrmW0uryOqNA',
                     username = 'atulya2109',
                     password = 'atulya.21',
                     user_agent = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19')

        with open(os.path.join(os.path.curdir,'reddit.pickle'), 'wb') as f:
            pickle.dump(reddit,f)
            logger.info('File Created: reddit.pickle')
    
    else:   
         with open(os.path.join(os.path.curdir,'reddit.pickle'), 'rb') as f:
            reddit = pickle.load(f)
            logger.info('Loaded Configuration From File: reddit.pickle')

    return reddit

def getSubreddit(reddit,name):

    subreddit = reddit.subreddit(name)
    return subreddit

def getSubredditPosts(subbreddit,sort_by = 'hot'):

    if sort_by == 'hot':
        return [submission for submission in subbreddit.hot() if not submission.is_self]

    elif sort_by == 'new':
        return [submission for submission in subbreddit.new() if not submission.is_self]

    elif sort_by == 'rising':
        return [submission for submission in subbreddit.rising() if not submission.is_self]

    elif sort_by == 'controversial':
        return [submission for submission in subbreddit.controversial() if not submission.is_self]

    elif sort_by == 'top':
        return [submission for submission in subbreddit.top() if not submission.is_self]
