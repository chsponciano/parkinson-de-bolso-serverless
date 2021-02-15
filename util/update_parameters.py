import boto3
import os


def get(body):
    update_expression = ["set "]
    update_values = dict()

    for key, val in body.items():
        update_expression.append(f" {key} = :{key},")
        update_values[f":{key}"] = val

    return "".join(update_expression)[:-1], update_values

def get_s3_url(filename):
    _bucket = os.environ['BUCKET_NAME']
    _location = boto3.client('s3').get_bucket_location(Bucket=_bucket)['LocationConstraint']
    return "https://{}.s3-{}.amazonaws.com/{}".format(_bucket, _location, filename)

