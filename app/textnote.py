from flask import render_template, request, session, url_for, redirect
from app import app
from app import attachment

import json, os, uuid, boto3



@app.route('/textnote/<postID>',methods=['GET','POST'])
# open or create new note
def textnote(postID):

    # handle new post
    if postID == 'new':
        text = ""
        return render_template('textnote/form.html', text=text, postID=postID)

    # read text from existing note
    client = boto3.client('lambda')
    payload = {"postID": postID}

    response = client.invoke(
        FunctionName='a3ReadFile',
        Payload=json.dumps(payload))

    text = json.loads(response['Payload'].read().decode("utf-8"))
    print('textfile',text)

    # check for attachment
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("a3Attachment")
        response = table.get_item(Key={ 'postID': postID})
        print(response)
        attach = response['Item']['filename']
    except:
        attach = ''
        url = ''
    else: # generate url for attachment
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url('get_object', Params={'Bucket': 'ece1779a3note',
                                        'Key': 'attach-'+ str(postID) + "-" + str(attach)},ExpiresIn=3600)

        #url ="https://" + 'ece1779a3note.s3.amazonaws.com/attach-' + str(postID) +  "-" + str(attach)


    return render_template('textnote/form.html', text=text, postID=postID, attach = attach,url=url)


@app.route('/textnote_submit/<postID>',methods=['POST'])
# save the note
def textnote_submit(postID):
    text = request.form['text']
    print(text)

    # save note to database
    client = boto3.client('lambda')
    payload = {'postID':postID, "text": text, 'author': session['username']}

    response = client.invoke(
        FunctionName='a3TextNote',
        Payload=json.dumps(payload)
    )
    return redirect(url_for('index'))

@app.route('/textnote_delete/<postID>',methods=['POST'])
def textnote_delete(postID):

    try:
        # delete from database
        client = boto3.resource('dynamodb')
        table = client.Table("a3Note")

        response = table.get_item(Key={'postID': postID})
        file = response['Item']['file']
        table.delete_item(Key={'postID': postID})

        # delete from s3
        s3 = boto3.client('s3')
        s3.delete_object(Bucket="ece1779a3note", Key=file)


        #
        # # delete note
        # postID = "delete-" + postID
        #
        # client = boto3.client('lambda')
        # payload = {'postID': postID, "text": 'text', 'author': 'author'}
        #
        # response = client.invoke(
        #     FunctionName='a3TextNote',
        #     Payload=json.dumps(payload)
        # )
        #
        # response_payload = json.loads(response['Payload'].read().decode("utf-8"))
        # print(response_payload)

        try:
            attachment.attachment_delete(postID)
        except:
            print('no attachment')
        else:
            print('attachment deleted')
    except:
        print('nothing to delete')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


