import urllib.parse
import urllib.request
def download_file(url):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            return data
    except urllib.error.URLError as e:
        print(e)

    """
    screenshotlayer用のURLを作成する
    """
def screenshotlayer(access_key, url, args):
    #print("=====SSを撮りたいURLを、加工します======")
    query_string = urllib.parse.urlencode(args)
    url += "&" + query_string
    return "https://api.screenshotlayer.com/api/capture?access_key=%s&url=%s" % (access_key, url)

# SSがほしいURLへアクセスした際のスクショをJPGで返す
def get_ss_from_url(want_ss_url):
    params = {
        'viewport': '800x600',
        'format': 'jpg',
    };
    access_key = "a39aecb96f931ad30c08d912ef054816" #screenshotlayerのaccess_key
    want_ss_url = urllib.parse.quote(want_ss_url)
    #print(want_ss_url)
    access_link = screenshotlayer (access_key, want_ss_url, params)

    #print(access_link)
    ss_data = download_file(access_link)
    return ss_data