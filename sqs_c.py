from uuid import uuid4
import boto3
import time
import json
from datetime import datetime

REGION = 'ap-northeast-1'
sqs_url = "https://sqs.ap-northeast-1.amazonaws.com/515491257789/jianzhan-profile-sqs"
s = boto3.Session()
sqs = s.client('sqs', region_name=REGION)

for i in range(0, 100):
    request_id = str(uuid4())
    now = datetime.now()
    msg = {
        "id": i,
        "request_id":request_id,
        "send_time": str(now)
    }

    msg_str = json.dumps(msg)
    response = sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=msg_str,
        DelaySeconds=0
    )

    print(msg)
    time.sleep(5)