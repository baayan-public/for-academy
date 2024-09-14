import base64
import datetime
import json
import os

import boto3

# 環境変数(Lambdaで設定)
bucket_name = os.getenv('S3_BUCKET_NAME', 'デフォルトのバケット名')

# 画像ファイルをアップロードする
def upload_image_file(review_id, event):

    # base64形式の画像データを復号しバイトコードに
    image_data = base64.b64decode(event['b64EncodeImageFileStr'])

    # S3バケット名とファイル名の設定
    file_name = f'{review_id}.jpg'  # 保存するファイル名

    # S3クライアントの作成、画像をアップロード
    s3_client = boto3.client('s3')
    s3_client.put_object(Body=image_data, Bucket=bucket_name, Key=f"images/{file_name}")
    
    return file_name
    
# DynamoDBへのデータ保存
def insert_dynamodb(review_id, review_text, user_name, mail_address, image_path):
    # DynamoDBクライアントの初期化
    dynamodb = boto3.client('dynamodb')
    
    # DynamoDBに保存するデータの設定
    table_name = 'reviews'  
    insert_item = {
        'id': {'S': review_id},
        'reviewText': {'S': review_text},
        'userName': {'S': user_name},
        'mailAddress': {'S': mail_address}
    }
    if image_path:
        insert_item['imagePath'] = {'S': image_path}

    # DynamoDBにデータを保存
    dynamodb.put_item(TableName=table_name, Item=insert_item)
    
# Main関数
def lambda_handler(event, context):
    
    # レビューIDを取得
    review_id = datetime.now().isoformat()
    
    # imageFileの文字列がある場合はS3アップロードの関数を実行
    if "b64EncodeImageFileStr" in event:
        image_path = upload_image_file(review_id, event)
    else:
        image_path = None

    # DynamoDBに保存
    insert_dynamodb(
        review_id, 
        event["reviewText"], 
        event["userName"], 
        event["mailAddress"], 
        image_path)
    
    # 結果の確認
    return {
        'statusCode': 200,
        'body': json.dumps('DynamoDBにデータを追加しました'),
    }