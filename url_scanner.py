# url_scaner.py
# MITLicenseのライブラリvirustotal_pythonを使用
# !pip install virustotal-python
from base64 import urlsafe_b64encode

from virustotal_python import Virustotal


# VT APIKeyの入力
vtotal = Virustotal(API_KEY="", API_VERSION="v3")


# VTでURLを診断し結果を返す
def vt_scan(tweet_url):
    try:
        # URLをbase64で暗号化
        url_id = urlsafe_b64encode(tweet_url.encode()).decode().strip("=")
        # URLをVTへリクエストとレスポンスの取得
        resp = vtotal.request(f"urls/{url_id}")
        result = resp.data
        return result

    except:
        print("URL分析時に問題が発生しました。")


# 診断結果（dict）をparse
def parse_response(result):
    # ツイートしたい結果を抽出
    result_harmless = f"良性判断サイト：{result['attributes']['last_analysis_stats']['harmless']}個"
    result_malicious = f"悪性判断サイト：{result['attributes']['last_analysis_stats']['malicious']}個"
    result_http_response_code = f"HTTPレスポンスコード：{result['attributes']['last_http_response_code']}"
    
    # ツイート文構築
    tweet_result = f'{result_harmless}\n{result_malicious}\n{result_http_response_code}'

    return tweet_result


def main():
    tweet_result = parse_response(vt_scan())
    print(tweet_result)


if __name__ == '__main__':
    main()
