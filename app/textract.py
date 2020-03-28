from flask import render_template, request, session, url_for, redirect
from app import app
from app import attachment

import json, os, uuid, boto3, datetime


@app.route('/image/<postID>',methods=['GET'])
def image(postID):

    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("a3Textract")


    try: # look for user uploaded image
        response = table.get_item(Key={'postID': postID})
        image = response['Item']['filename']

    except:  # display nothing if no image has been uploaded
        image = ''
        url = ''
        text = ''
        return render_template('image/image.html', postID=postID, url=url, text=text)

    else:  # get uploaded image from s3
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url('get_object', Params={'Bucket': 'ece1779a3textract',
                                                              'Key': 'upload-' + postID + '-' + str(image)},ExpiresIn=3600)


    try: # check if textract has been performed for current image
        s3name = "textract-" + postID + '-' + image.split('.')[0] + '.txt'
        client = boto3.resource('s3')
        obj = client.Object('ece1779a3textract', s3name)
        body = obj.get()['Body'].read()
        text = body.decode(encoding="utf-8")


    except: # otherwise perform textract for the first and only time
        print("performing textract")
        name = 'upload-' + postID + '-' + image
        print("source:", name)
        client = boto3.client('lambda')
        payload = {"file": name}

        response = client.invoke(
            FunctionName='a3textract',
            Payload=json.dumps(payload))
        s3name = "textract-" + postID + '-' + image.split('.')[0] + '.txt'
        print('newname:',s3name)
        client = boto3.resource('s3')
        try:
            obj = client.Object('ece1779a3textract', s3name)
            body = obj.get()['Body'].read()
            text = body.decode(encoding="utf-8")
        except:
            print("file not readable")
            text = ''
        else: print('read textract')
    else:
        print("textract already performed for this file")

    return render_template('image/image.html', postID=postID, url=url, text = text)




# check if uploaded file has allowed image extensions
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/image_submit<postID>',methods=['POST'])
def image_submit(postID):
    file = request.files['file']

    # verify acceptable file format
    if allowed_file(file.filename) == True :

        path = os.path.join('/tmp', file.filename)
        file.save(path)

        # create empty post for new file
        if postID == 'new':
            postID = uuid.uuid4().hex

            timestamp = str(datetime.datetime.now())
            timestamp = timestamp.rsplit('.')[0]

            # make new entry in databse
            client = boto3.resource('dynamodb')
            table = client.Table("a3Textract")
            response = {"postID": postID,
                        "filename": file.filename,
                        "author": session['username'],
                        "timestamp": timestamp}
            table.put_item(Item=response)
        else:
            # if this is an existing post then update database
            client = boto3.resource('dynamodb')
            table = client.Table("a3Textract")

            timestamp = str(datetime.datetime.now())
            timestamp = timestamp.rsplit('.')[0]

            table.update_item(
                Key={'postID': postID},
                UpdateExpression='SET #attr1 = :val1, #attr2 = :val2',
                ExpressionAttributeNames={'#attr1': 'timestamp', '#attr2': "filename"},
                ExpressionAttributeValues={':val1': timestamp, ':val2': file.filename})

        # save image to bucket
        s3 = boto3.client('s3')
        name = 'upload-' + postID + '-' + file.filename
        with open(path, "rb") as f:
            s3.upload_fileobj(f, "ece1779a3textract", name)
        os.remove(path)

    return redirect(url_for("image", postID=postID))


@app.route('/image_delete/<postID>',methods=['POST'])
def image_delete(postID):
    try:
        #delete from dynamodb
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("a3Textract")

        response = table.get_item(Key={'postID': postID})
        image = response['Item']['filename']
        table.delete_item(Key={'postID': postID})

        # delete from s3
        original = 'upload-' + postID + '-' + image
        text = 'textract-' + postID + '-'  + image.split('.')[0] + '.txt'

        s3 = boto3.client('s3')
        s3.delete_object(Bucket="ece1779a3textract", Key=original)
        s3.delete_object(Bucket="ece1779a3textract", Key=text)

        print("detele orginal image",original)
        print("detele textract image",text)
    except:
        print("nothing to delete")
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

