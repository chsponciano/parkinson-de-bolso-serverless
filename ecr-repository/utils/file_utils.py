import os
import base64
import boto3
import uuid

S3_RESOURCE = boto3.resource('s3')
S3_CLIENT = boto3.client('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']
TEMP_PATH = os.path.join(os.getcwd(), os.environ.get('TMP_PATH'))

def add_collection_image(file_path, path='dataCollectedTesting/'):
    _filename = path + _get_uuid_name(os.path.basename(file_path))
    _object = S3_RESOURCE.Object(BUCKET_NAME, _filename)
    
    with open(file_path) as fp:
        _object.put(Body=fp)

    _assign_public_reading(_filename)
    return _get_url(_filename)

def delete_standby_image(filename):
    _filename = filename.split('/')[-1]
    S3_RESOURCE.Object(BUCKET_NAME, f'dataCollectedTesting/wait/{_filename}').delete()

def delete_local_tmp_imagem(file_path):
    if TEMP_PATH not in file_path:
        file_path = os.path.join(TEMP_PATH, file_path)
    os.remove(file_path)

def download_image(url):
    os.system(f'wget -P {TEMP_PATH} {url}')
    return os.path.join(TEMP_PATH, os.path.basename(url))

def _get_uuid_name(filename):
    return str(uuid.uuid1()) + os.path.splitext(filename)[-1]

def _assign_public_reading(filename):
    _object_acl = S3_RESOURCE.ObjectAcl(BUCKET_NAME, filename)
    _object_acl.put(ACL='public-read')

def _get_url(filename):
    _location = S3_CLIENT.get_bucket_location(Bucket=BUCKET_NAME)['LocationConstraint']
    return "https://{}.s3-{}.amazonaws.com/{}".format(BUCKET_NAME, _location, filename)

if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)