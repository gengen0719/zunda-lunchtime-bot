import json
import boto3
import requests
import os

# LINEのアクセストークン（環境変数から取得）
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

# S3クライアント
s3 = boto3.client('s3')

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    line_user_ids = get_all_user_ids()
    print("Send Target User IDs:", line_user_ids)

    # S3イベント情報を取得
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        
        # S3の音声ファイルのURLを生成（署名付きURLを発行）
        s3_url = generate_presigned_url(bucket_name, object_key)
        # S3の音声ファイルのメタデータから音声ファイルの長さを取得
        duration = get_audio_duration(bucket_name, object_key)
        
        # LINEに音声メッセージを送信
        for current_user_id in line_user_ids:
            send_voice_message(current_user_id, s3_url, duration)

    return {'statusCode': 200, 'body': 'Message sent'}

def generate_presigned_url(bucket_name, object_key, expiration=300):
    """S3の署名付きURLを発行"""
    return s3.generate_presigned_url('get_object',
                                     Params={'Bucket': bucket_name, 'Key': object_key},
                                     ExpiresIn=expiration)

def get_audio_duration(bucket_name, object_key):
    """Metaデータに含まれる音声ファイルの長さを取得"""
    response = s3.head_object(Bucket=bucket_name, Key=object_key)
    metadata = response.get('Metadata', {})
    return metadata.get('duration', '30000') # デフォルト値はメッセージが十分入る30秒とする

def send_voice_message(line_user_id, audio_url, audio_duration):
    """LINEのMessaging APIで音声メッセージを送信"""
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": line_user_id,
        "messages": [{
            "type": "audio",
            "originalContentUrl": audio_url,
            "duration": audio_duration  
        }]
    }

    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
    print(response.text)

def get_all_user_ids():
    # DynamoDBクライアントの初期化
    dynamodb = boto3.client('dynamodb')
    
    table_name = 'LINE_Users'
    user_ids = []
    
    # 全スキャン実行
    response = dynamodb.scan(TableName=table_name)

    # userIdカラムを抽出してリストに追加
    for item in response.get('Items', []):
        user_id = item.get('userId', {}).get('S')
        if user_id:
            user_ids.append(user_id)
    
    # 次ページがある場合は繰り返し取得
    while 'LastEvaluatedKey' in response:
        response = dynamodb.scan(
            TableName=table_name,
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for item in response.get('Items', []):
            user_id = item.get('userId', {}).get('S')
            if user_id:
                user_ids.append(user_id)

    return user_ids