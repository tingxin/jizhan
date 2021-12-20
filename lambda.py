import boto3
import os
from uuid import uuid4
import json
import base64
from datetime import datetime

REGION = 'ap-northeast-1'

profile_bucket = "jizhan"
status_tb = "status-user-profile"
model_folder = "model"
file_f = "https://{0}.s3.ap-northeast-1.amazonaws.com/{1}/{2}.glb"

sqs_url = "https://sqs.ap-northeast-1.amazonaws.com/515491257789/jianzhan-profile-sqs"


def lambda_handler(event, context):
    body_str = event["body"]
    body = json.loads(body_str)
    img_name = body["name"]
    img_raw_data = body["data"]

    img_raw_bytes = img_raw_data.encode("utf-8")
    img_data = base64.b64decode(img_raw_bytes)

    request_id = str(uuid4())

    session = boto3.Session()

    dynamodb = session.client('dynamodb', region_name=REGION)
    dynamodb_status = dynamodb.update_item(
        TableName=status_tb,
        Key={
            'request_id': {
                'S': request_id
            }
        },
        AttributeUpdates={
            'status': {
                'Value': {
                    'S': 'begin'}
            }
        }
    )

    print(dynamodb_status)

    os.chdir('/tmp')
    temp_file_path = '/tmp/{0}'.format(img_name)
    with open(temp_file_path, 'wb') as f:
        f.write(img_data)

    s3 = session.client('s3', region_name=REGION)
    suffix = img_name.split('.')[1]
    new_image_name = "{0}.{1}".format(request_id, suffix)
    with open(temp_file_path, 'rb') as f:
        s3_status = s3.upload_fileobj(f, 'jizhan', 'profile/{0}'.format(new_image_name))
        print(s3_status)

    os.remove(temp_file_path)

    k_info = {
        "request_id": request_id,
        "file_name": new_image_name
    }
    str_info = json.dumps(k_info)
    sqs = session.client('sqs', region_name=REGION)
    sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=str_info,
        DelaySeconds=0
    )
    result = {
        "request_id": request_id,
        "file_path": file_f.format(profile_bucket, model_folder, request_id)
    }
    return result
