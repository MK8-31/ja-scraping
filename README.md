# ja-scraping

# 概要
お弁当の売上個数と気象情報（天気・気温・湿度）を取得し、スプレッドシートに自動で書き込む。

４品目それぞれに対して取得と記録を行う。

情報の取得は12時30分と16時30分の2回行う


![ja-scraping2 drawio (2)](https://user-images.githubusercontent.com/68171652/194685610-703a42b1-a779-4483-9a60-b5aa34d981ee.png)


# 目的
売上情報と気象情報を確認し、スプレッドシートに記入するのは大変なので自動化したい

# アーキテクチャ図
![ja-scraping drawio](https://user-images.githubusercontent.com/68171652/194684458-26b5d20b-e622-40c6-9a6f-d234f378869d.png)

# 補足
当初はRailsでスクレイピングアプリを作ろうとしたが、運用コストを考慮しGASを使って実装することにした。

しかし、スクレイピング対象のWebサイトで使われているAWSのALBのスティッキーセッション機能を使うためのCookieをGASでは上手く取得できなかった。

なので、Cloud functionsを使うことにした。
