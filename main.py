# main.py
import os
import base64
import hashlib
import hmac
import json
from typing import List

import tweepy
from flask import Flask, request, abort, render_template
import iocextract

import screenshot
import url_scanner


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


# test
@app.route("/", methods=["GET"])
def test():
    return "OK"


# Account Activity APIのChallenge-Response Check (CRC)
@app.route("/webhooks/twitter", methods=["GET"])
def webhook_challenge():
    sha256_hash_digest = hmac.new(CONSUMER_SECRET.encode(), msg=request.args.get("crc_token").encode(), digestmod=hashlib.sha256).digest()
    response = {
        "response_token": "sha256=" + base64.b64encode(sha256_hash_digest).decode()
    }

    return json.dumps(response)


# Twitterイベント
@app.route("/webhooks/twitter", methods=["POST"])
def get_reply_and_response():
    request_json = json.loads(request.get_data().decode())
    print("webhook", request_json)

    BOT_SCREEN_NAME = "CheckURL_bot"
    bot = api.get_user(screen_name=BOT_SCREEN_NAME)
    BOT_ID = bot.id

    send_text = "[bot] "

    # tweet_create_events: 通常のTweet Object生成イベント
    if "tweet_create_events" in request_json.keys():
        print("tweet_create_events")
        status = request_json["tweet_create_events"][0]

        TWEET_ID = status["id"]

        TWEET_USER_ID = status["user"]["id"]
        TWEET_USER_SCREEN_NAME = status["user"]["screen_name"]
        TWEET_USER_NAME = status["user"]["name"]

        # Bot宛のメンションを含むかをチェック
        mention_to_bot_flag = False
        for user in status["entities"]["user_mentions"]:
            print("user id, bot id", user["id"], BOT_ID)
            if user["id"] == BOT_ID:
                mention_to_bot_flag = True
                break

        # Bot宛のリプライであるかをチェック
        reply_to_bot_flag = status["in_reply_to_user_id_str"] == BOT_ID

        # Bot自身のツイート、もしくはBot宛のメンションかリプライをどちらも含まない場合、以降の処理を行わない
        if TWEET_USER_ID == BOT_ID or not (mention_to_bot_flag or reply_to_bot_flag):
            print("ignore")
            return "OK"

        tweet_text = status["text"]

        # 長文の場合一部省略されるため、全文を取得
        if "extended_tweet" in status:
            tweet_text = status["extended_tweet"]["full_text"]
            print("LongText")

        rcv_text = tweet_text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        print(rcv_text)

        if "ping" in rcv_text:
            print("ping")
            send_text += "pong"
            reply(send_text, TWEET_ID)
        else:
            # TweetObjectからURLを取得
            url_list = [u["expanded_url"] for u in status["entities"]["urls"]]
            url_list += extract_url(rcv_text)
            # 重複を排除
            url_list = list(set(url_list))

            # ツイート文中にURLが見つからなかった場合
            if not url_list:
                print("URL not included")
                reply("URLが見つかりませんでした。", TWEET_ID)
                return "OK"

            print("URL list", url_list)
            # テスト用: 見つかったURLのうち、最初のもののみを処理
            url = url_list[0]

            try:
                ss_image = screenshot.get_ss_from_url(url)
                # スクリーンショットを保存
                image_filepath = "./screenshot.jpg"
                with open(image_filepath, mode ='wb') as local_file:
                    local_file.write(ss_image)
            except Exception as e:
                print(e)
                ss_image = None
            
            try:
                scan_result_text = url_scanner.parse_response(url_scanner.vt_scan(url))
            except Exception as e:
                print(e)
                scan_result_text = None

            # URLスキャンとスクリーンショットの取得の両方に成功
            if ss_image and scan_result_text:
                reply(scan_result_text, TWEET_ID, image_filepath=image_filepath)
            # URLスキャンに失敗
            elif ss_image and not scan_result_text:
                reply("URLのスキャンに失敗しました。", TWEET_ID, image_filepath=image_filepath)
            # スクリーンショットの取得に失敗
            elif not ss_image and scan_result_text:
                reply(scan_result_text + "\n\nスクリーンショットの取得に失敗しました。", TWEET_ID)
            # 両方に失敗
            else:
                reply("URLのスキャンとスクリーンショットの取得に失敗しました。", TWEET_ID)

    return "OK"


# 文章からURLを抽出してリストで返す
def extract_url(text):
    return list(iocextract.extract_urls(text, refang=True))


# リプライ
def reply(reply_text, reply_tweet_id, image_filepath=None):
    if image_filepath:
        api.update_with_media(image_filepath, status=reply_text, in_reply_to_status_id=reply_tweet_id, auto_populate_reply_metadata=True)
        print("画像付きreply")
    else:
        api.update_status(status=reply_text, in_reply_to_status_id=reply_tweet_id, auto_populate_reply_metadata=True)
        print("画像なしreply")


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
