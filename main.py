# main.py
import os
import base64
import hashlib
import hmac
import json
from typing import List

import tweepy
from flask import Flask, request, abort, render_template


# 環境変数から各種API認証情報を取得
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Flask
app = Flask(__name__)


# Account Activity APIのChallenge-Response Check (CRC)
@app.route("/webhooks/twitter", methods=["GET"])
def webhook_challenge():
    sha256_hash_digest = hmac.new(CONSUMER_SECRET, msg=request.args.get("crc_token"), digestmod=hashlib.sha256).digest()
    response = {
        "response_token": "sha256=" + base64.b64encode(sha256_hash_digest)
    }

    return json.dumps(response)


# Twitterイベント
@app.route("/webhooks/twitter", methods=["POST"])
def get_reply_and_response():
    request_json = request.get_json()
    
    BOT_SCREEN_NAME = "CheckURL_bot"
    bot = api.get_user(screen_name=BOT_SCREEN_NAME)
    BOT_ID = bot.id

    send_text = "[bot] "

    # tweet_create_events: 通常のTweet Object生成イベント
    if "tweet_create_events" in request_json.keys():
        status = request_json["tweet_create_events"][0]

        TWEET_ID = status["id"]

        TWEET_USER_ID = status["user"]["id"]
        TWEET_USER_SCREEN_NAME = status["user"]["screen_name"]
        TWEET_USER_NAME = status["user"]["name"]

        # Bot宛のメンションを含むかをチェック
        mention_to_bot_flag = False
        for user in status["entities"]["user_mentions"]:
            if user.id == BOT_ID:
                mention_to_bot_flag = True
                break

        # Bot宛のリプライであるかをチェック
        reply_to_bot_flag = status["in_reply_to_user_id_str"] == BOT_ID

        # Bot自身のツイート、もしくはBot宛のメンションかリプライをどちらも含まない場合、以降の処理を行わない
        if TWEET_USER_ID == BOT_ID or not (mention_to_bot_flag or reply_to_bot_flag):
            return "OK"

        tweet_text = status["text"]

        # 長文の場合一部省略されるため、全文を取得
        if "extended_tweet" in status:
            tweet_text = status["extended_tweet"]["full_text"]
            print("LongText")

        rcv_text = tweet_text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

        if "ping" in rcv_text:
            send_text += "pong"
            reply(send_text, TWEET_ID)

        return "OK"


# 文章からURLを抽出してリストで返す
def extract_url(text: str) -> List[str]:
    pass


# リプライ
def reply(reply_text: str, reply_tweet_id: int):
    api.update_status(status=reply_text, in_reply_to_status_id=reply_tweet_id)


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
