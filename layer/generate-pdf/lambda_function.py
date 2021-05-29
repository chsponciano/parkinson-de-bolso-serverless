import os, boto3, json
from datetime import datetime
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


BUCKET_NAME = 'parkinson-de-bolso-bucket'
S3_CLIENT = boto3.client('s3')
S3_RESOURCE = boto3.resource("s3")

def get_style():
    _styles = getSampleStyleSheet()
    return _styles["BodyText"]

def get_header(data, style):
    _title = data['title']
    return Paragraph(f'<center><bold><font size=18>Parkinson de bolso - {_title}</font></bold></center>', style)

def json_to_table(items):
    _data = []
    for item in items:
        _data.append(list(item.values()))
    return _data

def generate_pdf(data, file_path):
    _size = [540, 720]
    _canvas = Canvas(file_path, pagesize=letter)
    _canvas.setTitle(data['title'])
    _canvas.setAuthor(data['userid'])

    _style = get_style()
    _header = get_header(data, _style)

    _content = json_to_table(data['items']) 
    _table = Table(_content)
    _table.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.25, colors.black), ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black)]))

    for index in range(len(_content)):
        _bg_color = colors.whitesmoke if index % 2 == 0 else colors.lightgrey
        _table.setStyle(TableStyle([('BACKGROUND', (0, index), (-1, index), _bg_color)]))

    _, _height = _header.wrap(_size[0], _size[1])
    _header.drawOn(_canvas, 72, _size[1])
    
    _size[1] = _size[1] - _height

    _, _height = _table.wrap(_size[0], _size[1])
    _table.drawOn(_canvas, 72, _size[1] - _height)
    
    return _canvas.getpdfdata()

def s3_upload(file_path):
    _s3_path = file_path[1:]
    S3_CLIENT.upload_file(file_path, BUCKET_NAME, _s3_path)
    _object_acl = S3_RESOURCE.ObjectAcl(BUCKET_NAME, _s3_path)
    _object_acl.put(ACL='public-read')
    _location = S3_CLIENT.get_bucket_location(Bucket=BUCKET_NAME)['LocationConstraint']
    return "https://{}.s3-{}.amazonaws.com/{}".format(BUCKET_NAME, _location, _s3_path)

def lambda_handler(event, context):
    _data = json.loads(json.dumps(event['body']))
    _user_id = _data['userid']
    _file_path =  f'/tmp/{_user_id}.pdf'
    _pdf = generate_pdf(_data, _file_path)
    _url = None
    
    if _pdf:
        with open(_file_path, 'wb') as file:
            file.write(_pdf)
        try:
            _url = s3_upload(_file_path)
        except Exception as e:
            return {
                'statusCode': 500,
                'error': e
            }
        else:
            os.remove(_file_path)
            return {
                'statusCode': 200,
                'error': None,
                'url': _url
            }