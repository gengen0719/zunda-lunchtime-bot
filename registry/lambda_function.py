import json
import boto3

# DynamoDBクライアント
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("LINE_Users")

def lambda_handler(event, context):
    print("LINE EVENT dump:", json.dumps(event, indent=2))
    return_message = "Not registered"

    # メッセージ送信、友達登録を行ったユーザーの userId と displayName を取得
    for event_data in event.get("events", []):
        if event_data["type"] != "follow":
            #follow event以外は処理しない
            print("LINE EVENT is not follow.")
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
            print("Saved userId: ", user_id, "displayName: ", display_name)
            return_message = "Registered"

    return {
        "statusCode": 200,
        "body": return_message
    }
