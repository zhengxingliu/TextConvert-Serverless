import json
import uuid
import datetime, os, boto3


# handles text based notes

def lambda_handler(event, context):
    postID = event['postID']
    text = event['text']
    print('text received:', text)
    author = event['author']

    # create new file if it's a new file
    if postID == 'new':
        # create txt file
        postID = uuid.uuid4().hex
        fileName = 'text-' + postID + '.txt'
        path = os.path.join('/tmp', fileName)
        with open(path, "w") as text_file:
            text_file.write(text)

        # save txt to s3
        s3 = boto3.client('s3')
        with open(path, "rb") as f:
            s3.upload_fileobj(f, "ece1779a3note", fileName)

        # add to databse
        client = boto3.resource('dynamodb')
        table = client.Table("a3Note")

        timestamp = str(datetime.datetime.now())
        timestamp = timestamp.rsplit('.')[0]

        # save first few characters for preview
        if len(text) > 50:
            start_with = text[:50] + "..."
        elif text == '':
            start_with = ' '
        else:
            start_with = text

        response = {"postID": postID,
                    "author": author,
                    "file": fileName,
                    "timestamp": timestamp,
                    "start_with": start_with
                    }

        print(response)

        table.put_item(Item=response)
        return postID

    # # delete file if it is prompted
    # elif postID.startswith( 'delete-' ):

    #     postID = postID.lstrip('delete-')

    #     #delete from database
    #     client = boto3.resource('dynamodb')
    #     table = client.Table("a3Note")

    #     response = table.get_item(Key={ 'postID': postID})
    #     file = response['Item']['file']
    #     table.delete_item(Key={'postID': postID})

    #     #delete from s3
    #     s3 = boto3.client('s3')
    #     s3.delete_object(Bucket="ece1779a3note", Key=file)

    #     return "textNote deleted"

    # upate file if it's a edit for old file
    else:

        # update txt file
        fileName = 'text-' + postID + '.txt'
        path = os.path.join('/tmp', fileName)
        with open(path, "w") as text_file:
            text_file.write(text)

        # save txt to s3
        s3 = boto3.client('s3')
        with open(path, "rb") as f:
            s3.upload_fileobj(f, "ece1779a3note", fileName)

        # update databse
        client = boto3.resource('dynamodb')
        table = client.Table("a3Note")

        timestamp = str(datetime.datetime.now())
        timestamp = timestamp.rsplit('.')[0]

        # save first few characters for preview
        if len(text) > 50:
            start_with = text[:50] + "..."
        else:
            start_with = text

        table.update_item(
            Key={'postID': postID},
            UpdateExpression='SET #attr1 = :val1, #attr2 = :val2',
            ExpressionAttributeNames={'#attr1': 'timestamp', '#attr2': "start_with"},
            ExpressionAttributeValues={':val1': timestamp, ':val2': start_with})

        # response = table.get_item(Key={ 'postID': postID})
        # item = response['Item']

        return "textNote updated"


