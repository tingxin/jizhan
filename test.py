import boto3

REGION = 'ap-northeast-1'

s = boto3.Session()
s3 = s.client('s3', region_name=REGION)

response = s3.put_object_acl(
    ACL='public-read',
    Bucket='jizhan',
    Key='model/4b9eb8f3-0d1f-4fad-b835-ff543f66295f.glb'
)
print(response)