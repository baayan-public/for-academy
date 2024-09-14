import json
import os

import boto3

# 環境変数
bucket_name = os.getenv('S3_BUCKET_NAME', 'デフォルトのバケット名')

# --------------------
# DynamoDBから画像パスを取得
# --------------------
def fetch_image_path_from_dynamodb(review_id):
    # DynamoDBのクライアントを作成
    dynamodb = boto3.resource('dynamodb')
    
    # DynamoDBのテーブルを指定
    table = dynamodb.Table('reviews')
    
    # DynamoDBからレビューテキストを取得
    response = table.get_item(Key={'id': review_id})
    
    return response['Item'].get('imagePath')


# --------------------
# S3バケットから画像を取得
# --------------------
def fetch_image_data_from_s3(image_path):
    # S3 クライアントを初期化
    s3_client = boto3.client('s3')
    
    # S3 から画像を取得
    response = s3_client.get_object(Bucket=bucket_name, Key=f"images/{image_path}")
    image_data = response['Body'].read()

    return image_data

# --------------------
# 画像のコンプライアンスチェック
# --------------------
def compliance_check(image_data):
    # Rekognition クライアントを初期化
    rekognition_client = boto3.client('rekognition')
    rekognition_response = rekognition_client.detect_moderation_labels(
        Image={'Bytes': image_data}
    )

    # 不適切なコンテンツの有無をチェック
    if rekognition_response['ModerationLabels']:
        return True
    else:
        return False
    
# --------------------
# コンプライアンスチェックの結果を取得
# --------------------
def update_review_is_image_inappropriate_in_dynamodb(review_id, is_inappropriate):
    # DynamoDBのクライアントを作成
    dynamodb = boto3.resource('dynamodb')
    
    # DynamoDBのテーブルを指定
    table = dynamodb.Table('reviews')
    
    # 分析結果をDynamoDBに保存
    response = table.update_item(
        Key={'id': review_id},
        UpdateExpression='SET isInappropriate = :val',
        ExpressionAttributeValues={
            ':val': is_inappropriate
        }
    )

# --------------------
# メイン関数
# --------------------
def lambda_handler(event, context):
    
    # イベントからidを取得
    review_id = event['id']
    
    # 画像パスを取得
    image_path = fetch_image_path_from_dynamodb(review_id)
    
    # 画像パスがあった場合のみ実行
    if image_path is not None:
        
        # イメージデータを取得
        image_data = fetch_image_data_from_s3(image_path)
        
        # 画像のコンプライアンスチェック
        review_is_image_inappropriate = compliance_check(image_data)
        
        # 結果を保存
        update_review_is_image_inappropriate_in_dynamodb(review_id, review_is_image_inappropriate)
        
    # 処理の成功を返す
    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully updated compliance for review {review_id}'),
        'id': review_id
    }