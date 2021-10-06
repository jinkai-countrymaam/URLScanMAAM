# URLScanMAAM

Twitter上で、URLの安全性を検証し、スクリーンショットを取得する機能を持つTwitterBotです。

Twitterアカウント: https://twitter.com/URLScan_MaamBot

## 機能・使用方法

### <Botを呼び出す方法>

- 検査したいURLを含むツイートのリプライでBot宛の@メンションを含めた投稿をツイートする
- 検査したいURLとともに、Bot宛の@メンションを含めてツイートする
- Botアカウントのツイートに検査したいURLをリプライする

`hxxp://`や`exsample[.]com`などの記法でハイパーリンクが無効化されたURLにも対応しています。

### <検査結果の表示>

VirusTotalによるWebサイトのスキャン結果として、以下の3つを返します。
- VirusTotalで良性判定された個数
- VirusTotalで悪性判定された個数
- HTTPレスポンスコード

また、Webサイトにアクセスした際のスクリーンショットを取得し、画像で返します。URLは同時に最大4つまで検査可能です。

## 使用例のスクリーンショット

![example1](https://user-images.githubusercontent.com/52136734/136167873-b8fd26f0-e141-4d11-b622-8877a932a72c.png)
