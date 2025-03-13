import json
import boto3
import logging

# DynamoDBクライアント
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("LINE_Users")

# CloudWatch ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    print("LINE EVENT dump:", json.dumps(event, indent=2))

    # メッセージ送信、友達登録を行ったユーザーの userId と displayName を取得
    for event_data in event.get("events", []):
        if event_data["type"] != "follow":
            #follow event以外は処理しない
            continue

        if "source" in event_data and "userId" in event_data["source"]:
            user_id = event_data["source"]["userId"]
            display_name = event_data.get("source", {}).get("displayName", "Unknown")
            timestamp = event_data["timestamp"]
            user_data = {
                "userId": user_id,
                "displayName": display_name,
                "timestamp": timestamp
            }

            # DynamoDB に保存
            table.put_item(Item=user_data)
            logger.info(f"Saved userId: {user_id}, displayName: {display_name}")

    return {
        "statusCode": 200,
        "body": "OK"
    }
