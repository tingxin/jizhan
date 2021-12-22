import boto3
from boto3.dynamodb.conditions import Key
import json

status_tb = "status-user-profile"
REGION = 'ap-northeast-1'
request_key = 'x-jizhan-request-id'


def lambda_handler(event, context):
    try:
        headers = event["headers"]
        if request_key not in headers:
            raise ValueError("lock of request id")

        request_id = headers[request_key]
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        tb = dynamodb.Table(status_tb)
        response = tb.query(
            KeyConditionExpression=Key('request_id').eq(str(request_id))
        )
        code = 404
        t = {
            "error": "{0} does not found".format(request_id)
        }
        if "ResponseMetadata" in response:
            r_code = response["ResponseMetadata"]["HTTPStatusCode"]
            if r_code == 200:
                items = response["Items"]
                if len(items) > 0:
                    code = 200
                    t = {
                        "status": items[0]["status"]
                    }
                    
        return {
            "statusCode": code,
            "body": json.dumps(t)
        }
    except Exception as e:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "error ": str(e)
            })
        }
