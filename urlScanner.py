#urlScaner.py
#MITLicenseのライブラリvirustotal_pythonを使用
#!pip install virustotal-python
from virustotal_python import Virustotal
from pprint import pprint
from base64 import urlsafe_b64encode

import json

#VT APIKeyの入力
vtotal = Virustotal(API_KEY="", API_VERSION="v3")

#スキャンするURLの入力
tweet_url = "https://developers.virustotal.com/reference"

#VTでURLを診断し結果を返す
def vt_scan():
    try:
        # URLをbase64で暗号化
        url_id = urlsafe_b64encode(tweet_url.encode()).decode().strip("=")
        # URLをVTへリクエストとレスポンスの取得
        resp = vtotal.request(f"urls/{url_id}")
        result = resp.data
        return result

    except:
        print("URL分析時に問題が発生しました。")

#診断結果（dict）をparse
def parse_response(result):
    #ツイートしたい結果を抽出
    result_harmless = '良性判断サイト：{}個'.format(result['attributes']['last_analysis_stats']['harmless'])
    result_malicious = '悪性判断サイト：{}個'.format(result['attributes']['last_analysis_stats']['malicious'])
    result_http_response_code = 'HTTPレスポンスコード：{}'.format(result['attributes']['last_http_response_code'])
    
    #ツイート文構築
    tweet_result = f'{result_harmless}\n{result_malicious}\n{result_http_response_code}'

    return tweet_result

def main():
    tweet_result = parse_response(vt_scan())
    #print(tweet_result)

if __name__ == '__main__':
    main()