import os
import json
import boto3
import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_free_time():
    # Google Calendar API 設定
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    SERVICE_ACCOUNT_FILE = '/tmp/service_account.json'  # Lambda内で一時ファイルとして保存
    CALENDAR_ID = os.getenv('CALENDAR_ID')  # 環境変数から取得

    # タイムゾーンオブジェクトを定義
    JST = pytz.timezone('Asia/Tokyo')

    # 認証情報をLambdaの環境変数から取得し、一時ファイルとして保存
    service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    with open(SERVICE_ACCOUNT_FILE, "w") as f:
        json.dump(service_account_info, f)

    # Google Calendar API クライアントの初期化
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    # 今日の日付を取得
    utcnow = datetime.datetime.utcnow().date()
    start_datetime = datetime.datetime.combine(utcnow, datetime.time(2, 0))  # UTCで11:00 (JST) を指定 TODO 9時以降に実行される前提のコードになっている
    end_datetime = datetime.datetime.combine(utcnow, datetime.time(5, 0))    # UTCで14:00 (JST) を指定 TODO 9時以降に実行される前提のコードになっている
    jstnowdate = datetime.datetime.now(JST).date()


    # Freebusy API を利用して空き時間を取得
    body = {
        "timeMin": start_datetime.isoformat() + "Z",
        "timeMax": end_datetime.isoformat() + "Z",
        "items": [{"id": CALENDAR_ID}]
    }
    freebusy = service.freebusy().query(body=body).execute()

    # 予定のリストを取得
    busy_times = freebusy['calendars'][CALENDAR_ID].get('busy', [])
    free_times = []

    # 予定のない時間を取得
    current_time = start_datetime
    for event in busy_times:
        start = datetime.datetime.fromisoformat(event['start'][:-1])
        if current_time < start:
            free_times.append((current_time.astimezone(JST), start.astimezone(JST)))
        current_time = datetime.datetime.fromisoformat(event['end'][:-1])

    if current_time < end_datetime:
        free_times.append((current_time.astimezone(JST), end_datetime.astimezone(JST)))

    # 空き時間をフォーマット
    if free_times:
        free_time_texts = [f"{s.hour}時{s.minute:02d}分、から、{e.hour}時{e.minute:02d}分、" for s, e in free_times]
        free_time_str = "、".join(free_time_texts)
        message = f"おはようなのだ！{jstnowdate.month}月{jstnowdate.day}日の、お昼ご飯を食べられる時間は、{free_time_str} なのだ！"
    else:
        message = f"おはようなのだ……{jstnowdate.month}月{jstnowdate.day}日は、お昼ご飯を食べられる時間はないのだ……悲しいのだ……😭"
    
    return message



client = boto3.client('lambda')

def lambda_handler(event, context):
    text = get_free_time()
    
    payload = {
        "text": text
    }

    response = client.invoke(
        FunctionName="ZundaTest",
        InvocationType="Event",  # 非同期実行
        Payload=json.dumps(payload)
    )

    # 結果を返す
    return {
        "statusCode": 200,
    }