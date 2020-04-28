from instagram_private_api import Client, ClientError, ClientLoginError, ClientCookieExpiredError, ClientLoginRequiredError
import instagram_web_api
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from base import Post, Base, User
import datetime
import codecs
import random
import argparse
# try:
from pbservice import sendImage, getLatestPushes,deletePush, sendMessage, removeNotif

import os
import time
from reddit_scraper import loginReddit,getSubreddit,getSubredditPosts
import requests
import threading 


lock = threading.Lock()
engine = create_engine('sqlite:///main.sqlite',connect_args = {'check_same_thread' : False})
Session = sessionmaker(bind = engine)

session = Session()
Base.metadata.create_all(engine)

tokens = ['#meme', '#memes', '#bestmemes', '#instamemes', '#funny', '#funnymemes', '#dankmemes', '#offensivememes', '#edgymemes', '#spicymemes', '#nichememes', '#memepage', '#funniestmemes', '#dank', '#memesdaily', '#jokes', '#memesrlife', '#memestar', '#memesquad', '#humor', '#lmao', '#igmemes', '#lol', '#memeaccount', '#memer', '#relatablememes', '#funnyposts', '#sillymemes', '#nichememe', '#memetime', '#memeimages', '#newestmemes', '#todaymemes', '#recentmemes', '#decentmemes', '#memearmy', '#memedose', '#memehumor', '#questionablememes', '#sickmeme', '#oldmeme', '#unusualmeme', '#memeculture', '#memehour', '#bizarrememe', '#scarymeme', '#sarcasm', '#goofymemes', '#entertaining', '#ironic', '#stupidmemes', '#crazymemes', '#lightmeme', '#annoyingthings', '#memehearted', '#wtfmeme', '#dogmemes', '#catmeme', '#fortnitememes', '#clevermemes', '#oddlymemes', '#dumbmemes', '#interestingmemes', '#likablememes', '#beameme', '#fulltimememer', '#cornymeme', '#surrealmeme', '#wowmemes', '#originalmemes', '#creepymemes', '#memefarm', '#mememaker', '#memebased', '#meming', '#memelord', '#latinmemes', '#schoolmemes', '#relevantmeme', '#bestjokes', '#memeboss', '#dadjokes', '#famousmemes', '#memeintelligence', '#memeuniversity', '#gamingmemes', '#rapmemes', '#coldmemes', '#memeit', '#prettyfunny', '#memevibes', '#boringmemes', '#geniusmemes', '#funnyvideos', '#bestmemevideos', '#funnythings', '#funnystories', '#memestory', '#memesgraciosos', '#laughs', '#cleverjokes', '#memeworld', '#memezar', '#amazingmemes', '#funnymemesdaily', '#memespam', '#moodmemes', '#dankspam', '#awfulmeme', '#quitefunny', '#trumpmemes', '#obamamemes', '#nbamemes', '#memestuff', '#unbelievable', '#savagememes', '#meaningful', '#comedy', '#dailycomedy', '#hahaha']

if not os.path.isdir('logs'):
    os.mkdir('logs')

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Instagram Bot That Posts Content From Reddit")
parser.add_argument('--settings','-s',dest = 'settings_file_path',type=str,required=True)
parser.add_argument('-u','--username','-u',dest = 'username',type = str,required=True)
parser.add_argument('-p', '--password', dest='password', type=str, required=True)
parser.add_argument('-d','--debug',action='store_true')

args = parser.parse_args()

error_handler = logging.FileHandler(os.path.join('logs',f'logfile.log'),mode='w')

error_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

if args.debug:
    logger.setLevel(logging.DEBUG)

def to_json(python_object):

    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):

    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object

def onlogin_callback(api,settings_file):
    
    cache_settings = api.settings

    with open(settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
    
    logging.info(f'New Settings File Created: {settings_file}')

def login():

    settings_file_path = args.settings_file_path
    device_id = None

    try:
        if not os.path.isfile(settings_file_path):
            
            logger.info(f'Unable To Find File: {settings_file_path}')

            api = Client(
                args.username, args.password,
                on_login = lambda x: onlogin_callback(x,settings_file_path))
        
        else:
            with open(settings_file_path,'r') as file_data:
                cached_settings = json.load(file_data,object_hook=from_json)
            
            logger.info(f'Loading Cached Settings From File: {settings_file_path}')

            device_id = cached_settings.get('device_id')

            api = Client(
                args.username,args.password,
                settings = cached_settings
            )

    
    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        
        logger.error(f'An Error Occured: {e}')

        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))
    
    except ClientLoginError as e:
        logger.error(f'ClientLoginError Occured: {e}')
        exit(9)
    
    except ClientError as e:
        logger.error(f'ClientError Occured {e.msg} ( Code: {e.code} Response: {e.error_response} )')
        exit(9)

    except Exception as e:
        logger.error(f'An Unknown Error Occured: {e}',exc_info=True)
        exit(99)

    cookie_expiry = datetime.datetime.fromtimestamp(api.cookie_jar.auth_expires).strftime('%d-%m-/%Y %H:%M:%S')
    logger.info(f'Cookie Expiry:  {cookie_expiry}')

    return api

def getFollowers(api):

    followers = api.user_followers(api.authenticated_user_id,api.generate_uuid())['users']
    followers = [follower['pk'] for follower in followers]

    return followers

def getFollowing(api):

    followings = api.user_following(api.authenticated_user_id,api.generate_uuid())['users']
    followings = [following['pk'] for following in followings]

    return followings

def maintainFollowers(api):

    followings = getFollowing(api)
    followers = getFollowers(api)

    for following in followings:

        # lock.acquire()
        # logger.info('Lock Acquired By maintainFollowers')
        with lock:
            user = session.query(User).filter_by(id = following).first()
        
        if following not in followers:

            destroy = False
            lock.acquire()
            if user:


                if not user.is_special:
                    
                    diff = datetime.datetime.now() - user.followed_on
                    
                    if diff.days >= 1:
                        destroy = True
                        user.is_followed = False
                        user.stale = True
                
                    else:
                        logger.info(f'User {following} Was Followed Less Than 24 Hours Ago. Skipping')

            else:
                destroy = True
                user = User(id = following,stale = True, followed_on = datetime.datetime.now(),is_special = False)
                session.add(user)
            
            session.commit()
            
            lock.release()
            # logger.info('Lock Released By maintainFollowers')

            if destroy:
                
                try:
                    api.friendships_destroy(following)
                    logger.info(f'Unfollowed User: {following}')
                    time.sleep(60)
                except Exception as e:
                    logger.info(e)
    
        else:

            lock.acquire()
            # logger.info('Lock Acquired By maintainFollowers')
            if user:
                user.follow_backs = True
            else:
                user = User(id = following, is_followed = True, follow_backs = True,followed_on = datetime.datetime.now(),is_special = False)
                session.add(user)
            
            session.commit()
            lock.release()
            # logger.info('Lock Released By maintainFollower')

def addPosts(reddit):

    subreddit = getSubreddit(reddit,'memes')
    
    posts = getSubredditPosts(subreddit)
    posts.extend(getSubredditPosts(subreddit,sort_by='rising'))
    posts.extend(getSubredditPosts(subreddit,sort_by='top'))

    logger.info(f'Fetched {len(posts)} From Reddit')

    c = 0

    for post in posts:

        db_post = session.query(Post).filter_by(id = post.id).first()

        if not db_post:
            db_post = Post(id = post.id,title = post.title,link = post.permalink,posted = False,added = datetime.datetime.fromtimestamp(post.created_utc),url= post.url)
            session.add(db_post)
            session.commit()
            logger.info(f'Added Post: {post.id}')
            c+=1
        
    logger.info(f'Added {c} New Posts To Database')

def sendPostEveryHour():

    while True:

        posts = session.query(Post).all()

        for post in posts:

            if not post.posted:
                sendImage(post.url,post.title,' '.join(random.sample(tokens,k = 15)))
                post.posted = True
                session.commit()
                logger.info(f'Sent Post: {post.id}')
                time.sleep(3600)

def addToFollow(api,link):

    success = False
    try:
        while not success:    
            mid = getMediaId(link)
            persons = api.media_likers(mid)['users']
            logger.info(f'Got Media Id: {mid}')
            success = True
    
    except ConnectionError:
        logger.error('Failed To Connect To IG. Retrying...')

    c = 0
    for person in persons:
        pk = person['pk']

        with lock:
            user = session.query(User).filter_by(id = pk).first()

            if not user:
                user = User(id = pk,is_special = False)
                session.add(user)
                session.commit()
                logger.info(f'Added Person To To-Be Followed List: {pk}')
                c+=1

    else:
        logger.info(f'Person {pk} Already In Queue')

    logger.info(f'Added {c} Persons To Follow List')

def getUserDetails(username):

    resp = requests.get(f'https://www.instagram.com/{username}/?__a=1').text
    return json.loads(resp)['graphql']['user']

def addToSpecial(uname):

    uid = getUserDetails(uname)['id']

    with lock:
        user = session.query(User).filter_by(id = uid).first()

        if user:
            user.is_special = True
            user.stale = False
            # session.commit()

        else:
            user = User(id = uid,is_followed = True,followed_on = datetime.datetime.now(), is_special = True)
            session.add(user)
        
        logger.info(f'Added {uid} To Special List')
        session.commit()

def listen(api):

    print('Listening...')
    while True:

        try:
            push = getLatestPushes()

            if push:
                content = push['body']

                if '!af' in content.split():

                    link = content[content.rfind(' ')+1:]
                    t = threading.Thread(target=addToFollow, args = (api,link),daemon=True)
                    t.start()
                    deletePush(push['iden'])

                if '!as' in content.split():

                    uname = content[content.rfind(' ')+1:]
                    t = threading.Thread(target=addToSpecial, args = (uname,),daemon=True)
                    t.start()
                    deletePush(push['iden'])

        except KeyError:
            pass

        except Exception as e:
            logger.error(f"Error Occured: {e}",exc_info=True)
            # exit(99)

        time.sleep(60)

def getMediaId(link):

    resp = requests.get(f'http://api.instagram.com/oembed?url={link}').text
    resp = json.loads(resp)
    return resp['media_id']

def follow(api,pk):
    
    try:
        api.friendships_create(pk)
    except Exception as e:
        logger.info(e)

def followEveryHour(api):

    following = getFollowing(api)
    # iden = None

    while True:

            # lock.acquire()
            # logger.info('Lock Acquired By followEveryHour')
        with lock:
            users = session.query(User).filter_by(is_followed = False,stale = False).all()

        for user in users:

            try:
            
                lock.acquire()
                if user.id not in following:
                    follow(api,user.id)
                    user.is_followed = True
                    user.followed_on = datetime.datetime.now()
                    logger.info(f'Followed User: {user.id}')

                else:
                    user.is_followed = True

                session.commit()

                lock.release()
                # logger.info('Lock Released By followEveryHour')

                time.sleep(60)
        
            except Exception as e:
                logger.info(e)
                
def main():

    # https://www.instagram.com/p/B_UXg90HA_D/?igshid=9zsov68gfo5v
    api = login()
    reddit = loginReddit()
    addPosts(reddit)

    t = threading.Thread(target = followEveryHour, args= (api,),daemon=True)
    t1 = threading.Thread(target= listen, args= (api,),daemon=True)
    t2 = threading.Thread(target= maintainFollowers, args = (api,),daemon=True)
    t3 = threading.Thread(target= sendPostEveryHour,args=(),daemon=True)

    t3.start()
    t2.start()
    t1.start()
    t.start()

    t1.join()
    t2.join()
    t.join()
    t3.join()

if __name__ == "__main__":
    main()