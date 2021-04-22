import os
from os import environ
import time
import schedule
import tweepy
import json

from sonar import run_and_save_sonar
from get_data import save_dataframe

CONSUMER_KEY = environ['CONSUMER_KEY']
CONSUMER_SECRET = environ['CONSUMER_SECRET']
ACCESS_KEY = environ['ACCESS_KEY']
ACCESS_SECRET =  environ['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

api = tweepy.API(auth, wait_on_rate_limit=True)
FILE_NAME = "last_replied_tweet_id.txt"


def retrieve_last_seen_id(file_name):

    with open(file_name, 'r') as f:
        last_seen_id = f.read().strip()
    
    return last_seen_id

def store_last_seen_id(last_seen_id, file_name):

    with open(file_name, 'w') as f:
        f.write(str(last_seen_id))

def process_request():
    print("Running...")
    success = False
    last_seen_id = retrieve_last_seen_id(FILE_NAME)
    mentions = api.mentions_timeline(last_seen_id, tweet_mode='extended')

    for mention in reversed(mentions):

        if not mention:
            return

        else:
            last_replied_tweet_id = mention.id
            store_last_seen_id(last_replied_tweet_id, FILE_NAME)
            print(f"Found #sonarrequest: {mention.id} - {mention.full_text}", flush=True)
            print("Replying...", flush=True)

            if "#sonarrequest" in mention.full_text.lower():
                query = mention.full_text.split("#sonarrequest")[-1]
                if "," in query:
                    player_name, position = query.split(",")[:2]
                    player_name=player_name.strip(); position= position.strip()
                    if position in ['FW', 'DM/CM', 'CAM/WF', 'CB', 'FB']:
                        success, matched_name = run_and_save_sonar(player_name, position) 
                    else: 
                        success, matched_name = run_and_save_sonar(player_name)                     
                else:
                    player_name = query.strip()
                    success, matched_name = run_and_save_sonar(player_name)

        if success:
            with open("weekly_tweets.json", "r") as f:
                tweets_dict = json.load(f)

            if matched_name in tweets_dict:
                api.update_status(f"@{mention.user.screen_name} https://twitter.com/wosonars/status/{tweets_dict[matched_name]}")

            else:             
                sonar_filename = f"../output/{matched_name}.png"
                message = f"@{mention.user.screen_name} {matched_name}"
                tweet = api.update_with_media(sonar_filename, status=message)
                
                tweets_dict[matched_name] = tweet.id
                with open("weekly_tweets.json", "w") as f:
                    json.dump(tweets_dict, f)


def weekly_reset():
    
    """Do tasks weekly 
    a) clear the output directory 
    b) collect data and 
    c) reset the update time in the txt file
    d) reset the weekly_tweets.json file
    """ 

    ##clear directory
    out_dir = "../output/"

    for f in os.listdir(out_dir):
        os.remove(os.path.join(dir, f)) 
    
    ##save update time
    with open("logger.txt", "w") as f:
        f.write(datetime.strftime(datetime.now(), format="%Y-%d-%m %H:%M:%S"))

    ##collect data
    save_dataframe()
    
    ##reset tweets to empty
    with open("weekly_tweets.json" "w") as f:
        json.dump(dict(), f)


schedule.every().monday.do(weekly_reset)
schedule.every(20).seconds.do(process_request)

while True:
    try:
        schedule.run_pending()
    except Exception as e:
        print("Ran into error while processing request", e)

