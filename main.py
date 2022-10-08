import functions_framework
import requests
from bs4 import BeautifulSoup
import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@functions_framework.http
def ja_scraping(request):
    # メールアドレスとパスワードの指定
    USERID = os.environ.get('USERID')
    PASS = os.environ.get('PASS')
    SHOP = os.environ.get('SHOP')
    LOGIN_URL = os.environ.get('LOGIN_URL')
    SALES_BULLETIN_URL = os.environ.get('SALES_BULLETIN_URL')

    print(SHOP)

    # セッションを開始
    session = requests.session()

    login_info = {
        "shop":SHOP,
        "userid":USERID,
        "pass":PASS,
    }

    res = session.post(LOGIN_URL, data=login_info, allow_redirects=False)

    res.raise_for_status() # エラーならここで例外を発生させる

    # print(res.text)
    # print(res.cookies)

    JSESSIONID = res.cookies.get('JSESSIONID')
    # AWSALB = res.cookies.get('AWSALB')
    # AWSALBCORS = res.cookies.get('AWSALBCORS')

    # print(JSESSIONID)
    # print(AWSALB)
    # print(AWSALBCORS)

    # cookieの取得
    response_cookie = res.cookies
    sales_bulletin_url = SALES_BULLETIN_URL + JSESSIONID

    sales_bulletin = session.get(sales_bulletin_url, cookies=response_cookie)


    # ログイン後のソースを取得
    print(sales_bulletin.text)

    soup = BeautifulSoup(sales_bulletin.content, "html.parser")

    elems = soup.select("pre")

    # 売れた個数を計算
    tori_num = int(elems[1].contents[2].split("　")[1])
    men_num = int(elems[2].contents[2].split("　")[1])
    total = tori_num + men_num

    # 天気の情報を取得
    weather, temp, humidity = getWeatherInfo()

    # 時間関係
    today, w, h = getTimeInfo()

    # use creds to create a client to interact with the Google Drive API
    scope =['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("JA弁当売上").worksheet("時間別売上")

    # スプレッドシートからデータを取得
    # list_of_hashes = sheet.get_all_records()
    # print(list_of_hashes)

    row = [today, w, h, weather,temp, humidity, total]

    # 最終行に追加
    sheet.append_row(row)

    return "success"

# 販売情報を取得した時の日付と曜日と時間帯
def getTimeInfo():
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    # 西暦を2桁に ex: 22/10/8
    today = now.strftime('%y/%m/%d')

    d_week = {'Sun': '日', 'Mon': '月', 'Tue': '火', 'Wed': '水',
          'Thu': '木', 'Fri': '金', 'Sat': '土'}
    key = now.strftime('%a')

    # 何曜日か ex: 木
    w = d_week[key]
    # 時間帯 ex: 12
    h = now.strftime('%H')

    return (today, w, h)

# 販売情報を取得した時の天気を取得
def getWeatherInfo():
  apiUrl = os.environ.get('WEATHERAPIURL')

  res = requests.get(apiUrl)
  jsonData = res.json()

  weather = jsonData['weather'][0]['main']
  temp = jsonData['main']['temp'];
  humidity = jsonData['main']['humidity'];

  weatherToJapanese = {'Thunderstorm': '雷雨', 'Drizzle': '霧雨', 'Rain': '雨', 'Snow': '雪',
          'Atmosphere': '霧', 'Clear': '晴れ', 'Clouds': '曇り'}

  return (weatherToJapanese[weather], temp, humidity)
