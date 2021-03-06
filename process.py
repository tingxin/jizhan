import boto3
from threading import Thread
import time
import json
from datetime import datetime, timedelta
import subprocess
import queue
import os
import random

REGION = 'ap-northeast-1'


# 从新消费n分钟之前的数据，再早的数据任务过时
TimeTolerant = 1000 * 60 * 0
status_tb = "status-user-profile"

# s3 配置
profile_bucket = "jizhan"
profile_folder = "profile"
bucket_model_folder = "model"
#
modeling_timeout = 40

# 本地文件路径配置
# output_folder = "model-viewer/packages/modelviewer.dev/shared-assets/models/"
output_folder = "/home/ec2-user/work/jizhan/work/temp"
output_file_name = "final3c2.glb"
shell_path = "/home/ec2-user/work/jizhan/work/ml.sh"
output_model_prefix = "glb"

hair_model_folder = "/home/ec2-user/work/jizhan/work/hair"

sqs_url = "https://sqs.ap-northeast-1.amazonaws.com/515491257789/jianzhan-profile-sqs"

class MsgThread(Thread):
    def __init__(self, thread_id, t_queue):
        Thread.__init__(self)
        self.thread_id = thread_id
        self.task_queue = t_queue

    def run(self):
        s = boto3.Session()
        sqs = s.client('sqs', region_name=REGION)
        s3 = s.client('s3', region_name=REGION)
        dynamodb = s.client('dynamodb', region_name=REGION)

        while True:
            response = sqs.receive_message(
                QueueUrl=sqs_url,
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
                    request_id = body["request_id"]
                    file_name = body["file_name"]
                    params = body["params"]
                    print("receive data : {0}".format(body))
                    
                    hair_model = "{0}/{1}/{2}.fbx".format(hair_model_folder,params,params)
                    hair_model_texture = "{0}/{1}/{2}.png".format(hair_model_folder,params,params)
                    
                    status = "bad"
                    print(hair_model)
                    if os.path.exists(hair_model) and os.path.exists(hair_model_texture) :
                        status = "processing"
                        download_profile_path = "{0}/{1}".format(output_folder, file_name)
                        with open(download_profile_path, 'wb') as data:
                            file_key = "{0}/{1}".format(profile_folder, file_name)
                            s3.download_fileobj(profile_bucket, file_key, data)

                        self.task_queue.put(
                            {
                                "request_id": request_id,
                                "file_path": download_profile_path,
                                "hair_model":hair_model,
                                "hair_model_texture":hair_model
                            }
                        )
                    
                    dynamodb.update_item(
                        TableName=status_tb,
                        Key={
                            'request_id': {
                                'S': request_id
                            }
                        },
                        AttributeUpdates={
                            'status': {
                                'Value': {
                                    'S': status}
                            }
                        }
                    )

    


class ModelThread(Thread):
    def __init__(self, thread_id, t_queue):
        Thread.__init__(self)
        self.thread_id = thread_id
        self.task_queue = t_queue

    def run(self):
        s = boto3.Session()
        dynamodb = s.client('dynamodb', region_name=REGION)
        s3 = s.client('s3', region_name=REGION)
        while True:
            task = self.task_queue.get()
            print("get process task {0}".format(task))
            request_id = task["request_id"]
            face_file_path = task["file_path"]
            hair_model = task["hair_model"]
            hair_model_texture = task["hair_model_texture"]
            
            status = "done"
            while True:

                output_file = "{0}/{1}".format(output_folder, output_file_name)
                if os.path.exists(output_file):
                    os.remove(output_file)

                print("prepare output_file {0}".format(output_file))
                subprocess.call(["bash", shell_path, face_file_path, hair_model, hair_model_texture])
                # subprocess.call([shell_path, face_file_path, hair_file_path, hair_texture_path])

                is_exist = False
                for i in range(0, modeling_timeout*5):
                    if os.path.exists(output_file):
                        is_exist = True
                        break
                    time.sleep(0.2)
                    
                if not is_exist:
                    status = "timeout"
                    break

                print("get output_file {0}".format(output_file))
                output_model = '{0}/{1}.{2}'.format(bucket_model_folder, request_id, output_model_prefix)
                with open(output_file, 'rb') as f:
                    s3_status = s3.upload_fileobj(f, profile_bucket, output_model)
                    print(s3_status)

                time.sleep(0.1)
                s3.put_object_acl(
                    ACL='public-read',
                    Bucket=profile_bucket,
                    Key=output_model
                )
                os.remove(output_file)
                os.remove(face_file_path)
                break
                
            r = dynamodb.update_item(
                TableName=status_tb,
                Key={
                    'request_id': {
                        'S': request_id
                    }
                },
                AttributeUpdates={
                    'status': {
                        'Value': {
                            'S': status}
                    }
                }
            )
            print(status)


if __name__ == '__main__':
    while True:
        try:
            
            task_queue = queue.Queue()
            msg_worker = MsgThread(1, task_queue)
            msg_worker.start()
            print("msg_worker process started")

            model_worker = ModelThread(2, task_queue)
            model_worker.start()
            print("model process started")

            msg_worker.join()
            model_worker.join()

        except Exception as e:
            print(e)
        time.sleep(60)
