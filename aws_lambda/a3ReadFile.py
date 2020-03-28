import json
import boto3


# read file from s3  with associated postID
def lambda_handler(event, context):
    postID = event['postID']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("a3Note")

    response = table.get_item(Key={'postID': postID})
    item = response['Item']
    file = item['file']

    client = boto3.resource('s3')
    obj = client.Object('ece1779a3note', file)
    body = obj.get()['Body'].read()

    text = body.decode(encoding="utf-8")
    text = text.rstrip()

    return text







