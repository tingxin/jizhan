from uuid import uuid4
import boto3
import time
import json
from datetime import datetime


REGION = 'ap-northeast-1'
sqs_url = "https://sqs.ap-northeast-1.amazonaws.com/515491257789/jianzhan-profile-sqs"
s = boto3.Session()
sqs = s.client('sqs', region_name=REGION)

while True:
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        AttributeNames=[
            'All'
        ],
        VisibilityTimeout=2
    )
    if "Messages" in response:
        messages = response["Messages"]
        for msg in messages:
            body_str = msg["Body"]
            body = json.loads(body_str)
            receipt_handle = msg["ReceiptHandle"]
            clean = sqs.delete_message(
                QueueUrl=sqs_url,
                ReceiptHandle=receipt_handle
            )
            now = datetime.now()
            print(now)
            print(msg)