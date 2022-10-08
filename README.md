# ja-scraping

# 概要
お弁当の売上個数を取得し、スプレッドシートに自動で書き込む。

情報の取得は日中、１時間ごとに行う


![ja-scraping2 drawio](https://user-images.githubusercontent.com/68171652/194684461-d9083cf9-9143-4ca5-87f5-1b0e57edfce0.png)


# 目的
１時間ごとにWebサイトを見に行き、スプレッドシートに記入するのは大変なので自動化したい

# アーキテクチャ図
![ja-scraping drawio](https://user-images.githubusercontent.com/68171652/194684458-26b5d20b-e622-40c6-9a6f-d234f378869d.png)

# 補足
当初はRailsでスクレイピングアプリを作ろうとしたが、運用コストを考慮しGASを使って実装することにした。

しかし、スクレイピング対象のWebサイトで使われているAWSのALBのスティッキーセッション機能を使うためのCookieをGASでは上手く取得できなかった。

なので、Cloud functionsを使うことにした。
