import json

import boto3

# パフォーマンスの向上、コスト削減目的でDynamoDBとComprehendクライアントをグローバルで定義
dynamodb = boto3.resource('dynamodb')
comprehend = boto3.client('comprehend')

def fetch_review_text_from_dynamodb(review_id):
    # DynamoDBのテーブルを指定
    table = dynamodb.Table('reviews')
    # DynamoDBからレビューテキストを取得
    response = table.get_item(Key={'id': review_id})
    if 'Item' not in response:
        return None  # レビューが見つからない場合
    review_text = response['Item']['reviewText']

    return review_text

# レビューの感情分析
def analyze_sentiment(review_text):
    if not review_text:
        return None
    return comprehend.detect_sentiment(Text=review_text, LanguageCode='ja')["Sentiment"]

# レビューのレコードに感情分析結果を更新して追加
def update_review_sentiment_in_dynamodb(review_id, review_sentiment):
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

# メイン関数
def lambda_handler(event, context):
    # イベントからidを取得
    review_id = event['id']
    # レビューテキストを取得
    review_text = fetch_review_text_from_dynamodb(review_id)
    # テキストがない場合エラーをリターン
    if review_text is None:
        return {
            'statusCode': 404,
            'body': json.dumps('Review not found')
        }
    
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