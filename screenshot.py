import urllib.parse
import urllib.request


def download_file(url):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            return data
    except urllib.error.URLError as e:
        print(e)


# screenshotlayer用のURLを作成する
def screenshotlayer(access_key, url, args):
    #print("=====SSを撮りたいURLを、加工します======")
    query_string = urllib.parse.urlencode(args)
    url += "&" + query_string
    
    return f"https://api.screenshotlayer.com/api/capture?access_key={access_key}&url={url}"


# SSがほしいURLへアクセスした際のスクショをJPGで返す
def get_ss_from_url(want_ss_url):
    params = {
        'viewport': '800x600',
        'format': 'jpg',
    }
    access_key = os.environ["SCREENSHOTLAYER_ACCESS_KEY"]  # screenshotlayerのaccess_key
    want_ss_url = urllib.parse.quote(want_ss_url)
    
    access_link = screenshotlayer(access_key, want_ss_url, params)
    ss_data = download_file(access_link)
    
    return ss_data
