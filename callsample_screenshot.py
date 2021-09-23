import screenshot

url = "https://github.com/nibosea"
photo = screenshot.get_ss_from_url(url)

# photoを保存する
with open("./picture/yobidasitest.jpg", mode ='wb') as local_file:
    local_file.write(photo)