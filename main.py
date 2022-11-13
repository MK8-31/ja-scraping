import requests
from bs4 import BeautifulSoup
import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

# .envファイルの内容を読み込見込む
load_dotenv()

@app.route("/")
def ja_scraping():
    # メールアドレスとパスワードの指定
    USERID = os.environ.get('USERID')
    PASS = os.environ.get('PASS')
    SHOP = os.environ.get('SHOP')
    LOGIN_URL = os.environ.get('LOGIN_URL')
    SALES_BULLETIN_URL = os.environ.get('SALES_BULLETIN_URL')

    # SHEETのidを取得
    TORI_SHEET = os.environ.get('TORI_SHEET')
    MENNOMI_SHEET = os.environ.get('MENNOMI_SHEET')
    GUZAI_SHEET = os.environ.get('GUZAI_SHEET')
    TENPURA_SHEET = os.environ.get('TENPURA_SHEET')


    # print(SHOP)

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

    # 売上個数を取得
    sales_bulletin = session.get(sales_bulletin_url, cookies=response_cookie)

    print(sales_bulletin.text)

    soup = BeautifulSoup(sales_bulletin.content, "html.parser")

    elems = soup.select("pre")

    # 売れた個数を計算
    tori_num = int(elems[1].contents[2].split("　")[1])
    men_num = int(elems[2].contents[2].split("　")[1])
    total = tori_num + men_num

    # 品物ごとの定価の数と値引きの数を取得
    teika_nebiki_array = set_teika_and_nebiki(elems[4].contents)

    # 天気の情報を取得
    weather, temp, humidity = getWeatherInfo()

    # 時間関係
    today, w, h = getTimeInfo()

    # use creds to create a client to interact with the Google Drive API
    scope =['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("JA弁当売上").worksheet("時間別売上")
    tori_sheet = client.open_by_key(TORI_SHEET).worksheet("2022")
    mennomi_sheet = client.open_by_key(MENNOMI_SHEET).worksheet("2022")
    guzai_sheet = client.open_by_key(GUZAI_SHEET).worksheet("2022")
    tenpura_sheet = client.open_by_key(TENPURA_SHEET).worksheet("2022")

    sheet_array = [tori_sheet, mennomi_sheet, guzai_sheet, tenpura_sheet]


    row = [today, w, h, weather,temp, humidity, total]

    # 最終行に追加
    sheet.append_row(row)

    # 品目毎のデータを記録
    data = [today, w, weather, temp, 0 , 0, 0, "", 0]

    for i in range(len(sheet_array)):
        sheet = sheet_array[i]
        update_sheet(sheet, data, teika_nebiki_array[i][0], teika_nebiki_array[i][1], today)

    return "success"

# それぞれの品目の定価と値引きの数を調べる
def set_teika_and_nebiki(contents):
    array = []
    for i in range(len(contents)):
        m = re.findall(r'\d+円\s+\d+個', str(contents[i]))  # 文字列から数字にマッチするものをリストとして取得
        array.extend(m)

    array2 = []
    for e in array:
        array2.append(re.findall(r'\d+', e))

    # 0: 鳥飯, 1: 麺のみ, 2: 具材, 3: 天ぷら
    # teika_nebiki_array = [[定価の数, 値引きの数], ...]
    teika_nebiki_array = [[0 for i in range(2)] for j in range(4)]
    for element in array2:
        if element[0] == '396':
            teika_nebiki_array[0][0] = int(element[1])
        elif element[0] == '296':
            teika_nebiki_array[0][1] = int(element[1])
        elif element[0] == '275':
            teika_nebiki_array[1][0] = int(element[1])
        elif element[0] == '175':
            teika_nebiki_array[1][1] = int(element[1])
        elif element[0] == '450':
            teika_nebiki_array[2][0] = int(element[1])
        elif element[0] == '350':
            teika_nebiki_array[2][1] = int(element[1])
        elif element[0] == '460':
            teika_nebiki_array[3][0] = int(element[1])
        elif element[0] == '360':
            teika_nebiki_array[3][1] = int(element[1])

    return teika_nebiki_array

# スプレッドシートを更新
def update_sheet(sheet, data, teika, nebiki, today):
    next_row = next_available_row(sheet)
    # shipments = sheet.acell(f"E{next_row}").value
    pre_row = next_row - 1
    date = sheet.acell(f"A{pre_row}").value
    if date == today:
        next_row -= 1

    row_list = sheet.row_values(next_row)
    if len(row_list) == 0:
        row_list = ["", "", "", "", 0]
    elif len(row_list) < 5:
        row_list.append(0)
    print(row_list)
    # 天気
    if row_list[2] != "":
        data[2] = row_list[2]

    # 気温
    if row_list[3] != "":
        data[3] = row_list[3]

    data[4] = row_list[4]
    data[5] = teika
    data[6] = nebiki
    data[7] = f"=E{next_row}-F{next_row}-G{next_row}"
    sheet.update(f"A{next_row}:I{next_row}", [data], value_input_option='USER_ENTERED')

def next_available_row(worksheet):
    str_list = worksheet.col_values(5)
    return len(str_list)+1

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
