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
from twitter_text import parse_tweet

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
    #print("webhook", request_json)

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
            # Twitterの短縮URLを排除
            url_list = list(filter(lambda x: not x.startswith("https://t.co"), url_list))
            # 重複を排除
            url_list = sorted(set(url_list), key=url_list.index)
            print("URL list", url_list)
            # URLを4つまでに制限(Twitterの投稿可能な画像の数が4枚であるため)
            url_list = url_list[:4]

            # ツイート文中にURLが見つからなかった場合
            if not url_list:
                print("URL not included")
                reply("URLが見つかりませんでした。", TWEET_ID)
                return "OK"

            # 投稿用画像IDリスト
            media_ids= []
            # URLスキャンとSSの結果テキストリスト
            url_result_text_list = []

            # URLをループ
            for i, url in enumerate(url_list):
                # スクリーンショット
                try:
                    ss_image = screenshot.get_ss_from_url(url)
                    # スクリーンショットを保存
                    image_filepath = "./screenshot{i}.jpg"
                    with open(image_filepath, mode ='wb') as local_file:
                        local_file.write(ss_image)
                    img = api.media_upload(image_filepath)
                    media_ids.append(img.media_id_string)
                except Exception as e:
                    print("SS取得失敗", e)
                    ss_image = None

                # URLスキャン
                try:
                    scan_result_text = url_scanner.parse_response(url_scanner.vt_scan(url))
                except Exception as e:
                    print(e)
                    scan_result_text = "URLスキャンに失敗しました"

                url_result_text = f"{url}"

                # URLスキャンの結果を投稿ツイート文に追加
                url_result_text += "\n" + scan_result_text
                
                # スクリーンショットの取得に失敗
                if not ss_image:
                    url_result_text += "\nスクリーンショットの取得に失敗しました"

                url_result_text_list.append(url_result_text)

            # ツイート文
            post_text = "\n\n".join(url_result_text_list)
            # 1つ以上画像が取得できている場合
            if media_ids:
                reply(post_text, TWEET_ID, media_ids=media_ids)
            else:
                reply(post_text, TWEET_ID)


    return "OK"


# 文章からURLを抽出してリストで返す
def extract_url(text):
    return list(iocextract.extract_urls(text, refang=True))


# リプライ
def reply(reply_text, reply_tweet_id, media_ids=None):
    parse_result = parse_tweet(reply_text)
    print("reply_text", parse_result.weightedLength, reply_text)

    # 文字数制限にかかる場合
    if parse_result.weightedLength >= 280:
        print("文字数制限", parse_tweet(reply_text).weightedLength)
        # 制限範囲内の文字数をツイート
        valid_range_end = parse_result.validRangeEnd - 2
        reply_text_cutout = reply_text[:valid_range_end] + "..."
        if media_ids:
            first_tweet = api.update_status(media_ids=media_ids, status=reply_text_cutout, in_reply_to_status_id=reply_tweet_id, auto_populate_reply_metadata=True)
            print("画像付きreply", reply_text_cutout)
        else:
            first_tweet = api.update_status(status=reply_text_cutout, in_reply_to_status_id=reply_tweet_id, auto_populate_reply_metadata=True)
            print("画像なしreply", reply_text_cutout)
        
        # 137文字以降をリプライにつなげる
        reply(status="..." + reply_text[valid_range_end:], in_reply_to_status_id=first_tweet.id, auto_populate_reply_metadata=True)

    if media_ids:
        api.update_status(media_ids=media_ids, status=reply_text, in_reply_to_status_id=reply_tweet_id, auto_populate_reply_metadata=True)
        print("画像付きreply", reply_text)
    else:
        api.update_status(status=reply_text, in_reply_to_status_id=reply_tweet_id, auto_populate_reply_metadata=True)
        print("画像なしreply", reply_text)


if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
