import os
import glob
import base64
import uuid


TEMP_PATH = os.path.join(os.getcwd(), os.environ.get('TMP_PATH'))

def clear_tmp():
    for f in glob.glob(f'{TEMP_PATH}/*'):
        os.remove(f)

def to_str_byte(encoded_file):
    return base64.b64decode(encoded_file)

def to_byte_str(file_path):
    _encode = None
    with open(file_path, "rb") as f:
        _encode = base64.b64encode(f.read())
    return _encode

def get_uuid_name(filename):
    return str(uuid.uuid1()) + os.path.splitext(filename)[-1]

def create_tmp_image(file_data):
    _file_path = os.path.join(TEMP_PATH, get_uuid_name(file_data['filename']))
    
    with open(_file_path, 'wb') as f:
        f.write(to_str_byte(file_data['data']))
    
    return _file_path

if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)
else:
    clear_tmp()