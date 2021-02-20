import os
import base64
import uuid
import boto3


_s3_resource = boto3.resource("s3")
_s3_client = boto3.client('s3')
_bucket = os.environ['BUCKET_NAME']

def add(file_data: dict):
    _filename = get_uuid_name(file_data['filename'])
    _object = _s3_resource.Object(_bucket, _filename)
    _object.put(Body=to_byte(file_data['data']))
    _assign_public_reading(_filename)
    return _get_url(_filename)

def delete(filename: str):
    _filename = filename.split('/')[-1]
    _s3_resource.Object(_bucket, _filename).delete()

def to_byte(encoded_file):
    return base64.b64decode(encoded_file)

def get_uuid_name(filename):
    return str(uuid.uuid1()) + os.path.splitext(filename)[-1]

def _assign_public_reading(filename):
    _object_acl = _s3_resource.ObjectAcl(_bucket, filename)
    _object_acl.put(ACL='public-read')

def _get_url(filename):
    _location = _s3_client.get_bucket_location(Bucket=_bucket)['LocationConstraint']
    return "https://{}.s3-{}.amazonaws.com/{}".format(_bucket, _location, filename)