import json
import boto3
from boto3.dynamodb.conditions import Key, Attr


def lambda_handler(event, context):
    # read all posts for current user

    author = event["author"]

    response = {}
    tableName = ['a3Note', 'a3Textract', 'a3Transcribe', 'a3Translate']
    posts = []
    dynamodb = boto3.resource('dynamodb')
    for item in tableName:

        table = dynamodb.Table(item)
        lists = table.scan(FilterExpression=Attr('author').eq(author))
        response[item] = lists["Items"]

        for key in lists["Items"]:
            posts.append(key)

    # check status of transcription posts that was still in progress
    try:
        transcribe = response['a3Transcribe']
    except:
        print('no transcribe job')
    else:

        client = boto3.client('lambda')
        print(transcribe)

        for item in transcribe:
            print(item['status'])
            print(item["postID"])

            if item['status'] == 'processing':
                payload = {'job_name': item["postID"]}

                status = client.invoke(FunctionName='a3TranscribeCheckState',
                                       Payload=json.dumps(payload))

    return response
