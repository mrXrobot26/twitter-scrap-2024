import asyncio
from twikit import Client, TooManyRequests
import csv
from datetime import datetime
from configparser import ConfigParser
from random import randint
from pathlib import Path

MINIMUM_TWEETS = 19900
QUERY = '(from:mrxrobot) lang:ar until:2024-01-01 since:2021-01-01'
OUTPUT_FILE = Path(__file__).parent / "tweets.csv"


async def get_tweets(client, tweets):
    if tweets is None:
        print(f'{datetime.now()} - Getting tweets...')
        tweets = await client.search_tweet(QUERY, product='Top')
    else:
        wait_time = randint(5, 10)
        print(f'{datetime.now()} - Getting next tweets after {wait_time} seconds ...')
        await asyncio.sleep(wait_time)
        tweets = await tweets.next()

    if not tweets:
        print(f'{datetime.now()} - No more tweets available for the query. Check the query parameters or network connectivity.')

    return tweets


async def main():
    config = ConfigParser()
    config.read('config.ini')
    username = config['X']['username']
    email = config['X']['email']
    password = config['X']['password']

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Tweet_count', 'Username', 'Text', 'Created At', 'Retweets', 'Likes'])

    client = Client(language='en-US')
    # await client.login(auth_info_1=username, auth_info_2=email, password=password)
    # client.save_cookies('cookies.json')
    client.load_cookies('cookies.json')

    tweet_count = 0
    tweets = None

    while tweet_count < MINIMUM_TWEETS:
        try:
            tweets = await get_tweets(client, tweets)
        except TooManyRequests as e:
            rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
            print(f'{datetime.now()} - Rate limit reached. Waiting until {rate_limit_reset}')
            wait_time = (rate_limit_reset - datetime.now()).total_seconds()
            await asyncio.sleep(wait_time)
            continue

        if not tweets:
            print(f'{datetime.now()} - No more tweets found')
            break

        for tweet in tweets:
            tweet_count += 1
            tweet_data = [
                tweet_count,
                tweet.user.name,
                tweet.text.encode('utf-8').decode('utf-8'),  
                tweet.created_at,
                tweet.retweet_count,
                tweet.favorite_count
            ]

            try:
                with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(tweet_data)
            except Exception as e:
                print(f'{datetime.now()} - Error writing to CSV: {e}')

        print(f'{datetime.now()} - Got {tweet_count} tweets')

    if tweet_count < MINIMUM_TWEETS:
        print(f'{datetime.now()} - Fetched {tweet_count} tweets, but could not reach the target of {MINIMUM_TWEETS}.')
    print(f'{datetime.now()} - Done! Got {tweet_count} tweets')


asyncio.run(main())
