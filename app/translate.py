from flask import render_template, request, session, url_for, redirect
from app import app


import json, os, uuid, boto3, datetime

@app.route('/translate/<postID>',methods=['GET','POST'])
def translate(postID):

    if postID == 'new':
        return render_template('translate/translate.html', postID=postID)

    else:
        client = boto3.resource('s3')
        obj = client.Object('ece1779a3translate', "source-" + postID + '.txt')
        body = obj.get()['Body'].read()
        text = body.decode(encoding="utf-8")
        text = text.rstrip()

        obj = client.Object('ece1779a3translate', "trans-" + postID + '.txt')
        body = obj.get()['Body'].read()
        translation = body.decode(encoding="utf-8")
        translation = translation.rstrip()

    return render_template('translate/translate.html', postID=postID, text=text, translation=translation)

@app.route('/translate_submit/<postID>',methods=['POST'])
def translate_submit(postID):


    text = request.form['text']
    if text == '' :
        return redirect(url_for('translate', postID=postID))

    author = session['username']


    # source_lan = request.form.get('source_lan')
    source_lan = 'auto'
    target_lan = request.form.get('target_lan')


    if postID == "new":
        checkNew = True
    else: checkNew = False


    client = boto3.client('lambda')
    payload = {'postID': postID, "text": text, 'author': author, "source_lan":source_lan, 'target_lan': target_lan}
    response = client.invoke(
        FunctionName='a3Translate',
        Payload=json.dumps(payload)
    )
    postID = json.loads(response['Payload'].read().decode("utf-8"))

    # add to databse
    timestamp = str(datetime.datetime.now())
    timestamp = timestamp.rsplit('.')[0]
    client = boto3.resource('dynamodb')
    table = client.Table("a3Translate")

    if len(text) > 50:
        start_with = text[:50] + '...'
    else: start_with = text

    if checkNew == True:
        response = {"postID": postID,
                    "author": author,
                    "timestamp": timestamp,
                    'start_with': start_with
        }
        table.put_item(Item=response)
    else:
        # table.update_item(
        #     Key={'postID': postID},
        #     UpdateExpression="SET timestamp = :val1, start_with = :val2",
        #     ExpressionAttributeValues={":val1": timestamp, ":val2": text[:30]}
        # )
        response = table.update_item(
            Key={'postID': postID},
            UpdateExpression='SET #attr1 = :val1, #attr2 = :val2' ,
            ExpressionAttributeNames={'#attr1': 'timestamp', '#attr2': "start_with" },
            ExpressionAttributeValues={':val1': timestamp, ':val2': start_with }
        )

    return redirect(url_for('translate',postID=postID))


@app.route('/translate_delete/<postID>',methods=['POST'])
def translate_delete(postID):
    try:
        #delete from dynamodb
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("a3Translate")

        table.delete_item(Key={'postID': postID})

        # delete from s3
        source = 'source-' + postID + '.txt'
        translation = 'trans-' + postID + '.txt'

        s3 = boto3.client('s3')
        s3.delete_object(Bucket="ece1779a3translate", Key=source)
        s3.delete_object(Bucket="ece1779a3translate", Key=translation)
    except:
        print('nothing to delete in translate')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


