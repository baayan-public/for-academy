import json

import boto3

# --------------------
# DynamoDBから口コミを取得
# --------------------
def fetch_review_text_from_dynamodb(review_id):
    # DynamoDBのクライアントを作成
    dynamodb = boto3.resource('dynamodb')
    
    # DynamoDBのテーブルを指定
    table = dynamodb.Table('reviews')
    
    # DynamoDBからレビューテキストを取得
    response = table.get_item(Key={'id': review_id})
    review_text = response['Item']['reviewText']
    
    return review_text

# --------------------
# 感情分析を実施
# --------------------
def analyze_sentiment(review_text):
    # Amazon Comprehendで感情分析
    comprehend = boto3.client('comprehend')
    analysis_result = comprehend.detect_sentiment(Text=review_text, LanguageCode='ja')

    return analysis_result["Sentiment"]

# --------------------
# 感情分析の結果を保存
# --------------------
def update_review_sentiment_in_dynamodb(review_id, review_sentiment):
    # DynamoDBのクライアントを作成
    dynamodb = boto3.resource('dynamodb')
    
    # DynamoDBのテーブルを指定
    table = dynamodb.Table('reviews')
    
    # 分析結果をDynamoDBに保存
    response = table.update_item(
        Key={'id': review_id},
        UpdateExpression='SET sentiment = :val',
        ExpressionAttributeValues={
            ':val': review_sentiment
        }
    )

# --------------------
# メイン関数
# --------------------
def lambda_handler(event, context):
    
    # イベントからidを取得
    review_id = event['id']
    
    # レビューテキストを取得
    review_text = fetch_review_text_from_dynamodb(review_id)
    
    # 取得したレビューをcomprehendで分析し感情を取得
    review_sentiment = analyze_sentiment(review_text)
    
    # 分析した結果(感情)をDynamoDBに保存
    update_review_sentiment_in_dynamodb(review_id, review_sentiment)
    
    # 処理の成功を返す
    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully updated sentiment for review {review_id}'),
        'id': review_id
    }