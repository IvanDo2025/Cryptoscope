import time
import requests
import datetime
from collections import deque
import praw
import tweepy
import os

# Настройки API (нужно вставить свои ключи)
TWITTER_BEARER_TOKEN = "YOUR_TWITTER_BEARER_TOKEN"
REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"
REDDIT_SECRET = "YOUR_REDDIT_SECRET"
REDDIT_USER_AGENT = "cryptoscope"

# Отслеживаемые монеты
TRACKED_COINS = ["bitcoin", "ethereum", "solana"]

# Порог резкого изменения цены (%)
PRICE_CHANGE_THRESHOLD = 3.0
MENTION_THRESHOLD = 2.0  # x раз всплеск активности

# Храним последние значения
price_history = {coin: deque(maxlen=5) for coin in TRACKED_COINS}
mention_history = {coin: deque(maxlen=5) for coin in TRACKED_COINS}

# Подключение к Reddit
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Twitter search client
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

def get_price(coin_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    response = requests.get(url).json()
    return response[coin_id]["usd"]

def get_mentions_twitter(coin):
    query = f"{coin} lang:en"
    tweets = twitter_client.search_recent_tweets(query=query, max_results=100)
    return len(tweets.data) if tweets.data else 0

def get_mentions_reddit(coin):
    count = 0
    for submission in reddit.subreddit("all").search(coin, time_filter="hour", limit=100):
        count += 1
    return count

def analyze_coin(coin):
    price = get_price(coin)
    price_history[coin].append(price)
    mentions = get_mentions_twitter(coin) + get_mentions_reddit(coin)
    mention_history[coin].append(mentions)

    if len(price_history[coin]) >= 2:
        price_change = ((price - price_history[coin][-2]) / price_history[coin][-2]) * 100
        avg_mentions = sum(mention_history[coin][:-1]) / max(len(mention_history[coin]) - 1, 1)
        if abs(price_change) >= PRICE_CHANGE_THRESHOLD and mentions > avg_mentions * MENTION_THRESHOLD:
            print(f"[{datetime.datetime.now()}] 🚨 ALERT: {coin.upper()} shows abnormal behavior!")
            print(f"    ↳ Price change: {price_change:.2f}%")
            print(f"    ↳ Mentions spike: {mentions} (avg: {avg_mentions:.1f})\n")

def main():
    print("🔍 Cryptoscope is now watching the market...")
    while True:
        for coin in TRACKED_COINS:
            try:
                analyze_coin(coin)
            except Exception as e:
                print(f"Error analyzing {coin}: {e}")
        time.sleep(300)  # каждые 5 минут

if __name__ == "__main__":
    main()
