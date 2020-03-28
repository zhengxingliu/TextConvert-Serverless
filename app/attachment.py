from flask import render_template, request, session, url_for, redirect
from app import app

import json, os, boto3

@app.route('/attachment/<postID>',methods=['POST'])
def attachment(postID):

    attach = request.files['file']
    attach.save(os.path.join('/tmp', attach.filename))
    client = boto3.client('lambda')

    # create empty post for new file
    if postID == 'new':
        print('new attachment')
        #get new postID with empty post
        payload = {"postID": postID, "text": "", "author": session["username"]}
        response = client.invoke(FunctionName='a3TextNote',Payload=json.dumps(payload))
        postID = json.loads(response['Payload'].read().decode("utf-8"))
        print(postID)
        print(attach.filename)

        # make new entry in databse
        client = boto3.resource('dynamodb')
        table = client.Table("a3Attachment")
        response = {"postID": postID,
                    "filename": attach.filename}
        table.put_item(Item=response)
        print( 'attachment created')
    else:
        # if editing existing post update database
        client = boto3.resource('dynamodb')
        table = client.Table("a3Attachment")
        table.update_item(
            Key={'postID': postID},
            UpdateExpression='SET #n = :val1',
            ExpressionAttributeValues={":val1": attach.filename},
            ExpressionAttributeNames={"#n": "filename"})

        response = table.get_item(Key={'postID': postID})
        item = response['Item']
        print('attachment updated')

    # save/update attachment file in s3
    s3 = boto3.client('s3')
    s3name = 'attach-' + postID + '-' + attach.filename
    s3.upload_file(os.path.join('/tmp', attach.filename), "ece1779a3note", s3name)
    os.remove(os.path.join('/tmp', attach.filename))

    return redirect(url_for('textnote', postID=postID))


def attachment_delete(postID):
    # retrieve file name
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("a3Attachment")
    postID = postID.split('delete-')[1]
    response = table.get_item(Key={'postID': postID})
    attach = response['Item']['filename']
    # delete from s3
    s3 = boto3.resource('s3')
    key = 'attach-'+ str(postID) + "-" + str(attach)
    s3.Object("ece1779a3note", key).delete()
    # delete from dynamodb
    response = table.delete_item(Key={'postID': postID})

