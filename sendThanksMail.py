import json
import os

import boto3


# 環境変数からパラメータを取得
from_mail_address = os.getenv('FROM_MAIL_ADDRESS')

# --------------------
# DynamoDBから口コミ情報を取得
# --------------------
def fetch_review_from_dynsmodb(review_id):
    # DynamoDBのクライアントを作成
    dynamodb = boto3.resource('dynamodb')
    
    # DynamoDBのテーブルを指定
    table = dynamodb.Table('reviews')
    
    # DynamoDBからレビューテキストを取得
    response = table.get_item(Key={'id': review_id})
    review_user_name = response['Item']['userName']
    review_mail_address = response['Item']['mailAddress']
    review_sentiment = response['Item']['sentiment']
    
    return review_user_name, review_mail_address, review_sentiment

# --------------------
# 感情に合わせたメッセージを取得
# --------------------
def get_sentiment_text(review_sentiment, review_user_name):
    if review_sentiment == "POSITIVE":
        text = f"頂いたご意見をスタッフ一同励みとして、今後も{review_user_name}様に安心してご利用いただけるよう努めてまいります。"
    elif review_sentiment == "NEGATIVE":
        text = f"{review_user_name}様より頂戴したご意見は真摯に受け止め、今後のサービスの改善に役立てたいと考えております。"
    else:
        text = f"{review_user_name}様より頂戴したご意見は社内にてしっかりご確認させていただきます！"
    
    return text

# --------------------
# body用のテキストを取得
# --------------------
def get_body_text(review_sentiment, review_user_name):
    # 感情に合わせたメッセージを取得
    sentiment_text = get_sentiment_text(review_sentiment, review_user_name)
    
    body_text = f"""
{review_user_name} 様
いつも当サービスをご利用いただき誠にありがとうございます。

{sentiment_text}

また機会がございましたら、当サービスをぜひご利用いただけますと幸いです。
スタッフ一同、心よりお待ち申し上げております。
"""
    
    return body_text

# --------------------
# メール送信
# --------------------
def send_email_using_ses(sentiment, user_name, mail_address):
    # SESクライアントの設定
    ses_client = boto3.client('ses', region_name='ap-northeast-1')

    # body用のテキストを取得
    body_text = get_body_text(sentiment, user_name)

    # メール設定

    subject = "口コミのご投稿ありがとうございました" 
    charset = "UTF-8"
    
    # SendEmail APIを使用してメールを送信
    response = ses_client.send_email(
        Destination={
            'ToAddresses': [
                mail_address
            ],
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': charset,
                    'Data': body_text,
                },
            },
            'Subject': {
                'Charset': charset,
                'Data': subject,
            },
        },
        Source=from_mail_address,
    )

# --------------------
# メイン関数
# --------------------
def lambda_handler(event, context):
    # イベントからidを取得
    review_id = event['id']
    
    # DynamoDBから氏名とメールアドレス
    review_user_name, review_mail_address, review_sentiment = fetch_review_from_dynsmodb(review_id)

    # メール送信
    send_email_using_ses(review_sentiment, review_user_name, review_mail_address)

    return {
        'statusCode': 200,
        'body': json.dumps('Email sent successfully!')
    }