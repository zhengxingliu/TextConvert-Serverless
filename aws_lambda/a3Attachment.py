import json, boto3


def lambda_handler(event, context):
    postID = event['postID']
    filename = event['filename']
    status = event['status']

    client = boto3.resource('dynamodb')
    table = client.Table("a3Attachment")

    if status == 'new':

        # make new entry in databse
        response = {"postID": postID,
                    "filename": filename
                    }
        table.put_item(Item=response)
        return 'attachment created'

    else:
        # update databse
        table.update_item(
            Key={'postID': postID},
            UpdateExpression='SET #n = :val1',
            ExpressionAttributeValues={":val1": filename},
            ExpressionAttributeNames={"#n": "filename"})

        response = table.get_item(Key={'postID': postID})
        item = response['Item']
        return 'attachment updated'

