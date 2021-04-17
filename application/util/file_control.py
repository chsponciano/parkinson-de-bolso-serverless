import os
import base64
import uuid
import boto3


S3_RESOURCE = boto3.resource("s3")
S3_CLIENT = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']

def add(file_data, path=''):
    _filename = path + get_uuid_name(file_data['filename'])
    _object = S3_RESOURCE.Object(BUCKET_NAME, _filename)
    _object.put(Body=to_byte(file_data['data']))
    _assign_public_reading(_filename)
    return _get_url(_filename)

def delete(filename):
    _filename = filename.split('/')[-1]
    S3_RESOURCE.Object(BUCKET_NAME, _filename).delete()

def to_byte(encoded_file):
    return base64.b64decode(encoded_file)

def get_uuid_name(filename):
    return str(uuid.uuid1()) + os.path.splitext(filename)[-1]

def _assign_public_reading(filename):
    _object_acl = S3_RESOURCE.ObjectAcl(BUCKET_NAME, filename)
    _object_acl.put(ACL='public-read')

def _get_url(filename):
    _location = S3_CLIENT.get_bucket_location(Bucket=BUCKET_NAME)['LocationConstraint']
    return "https://{}.s3-{}.amazonaws.com/{}".format(BUCKET_NAME, _location, filename)