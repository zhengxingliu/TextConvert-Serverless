from flask import render_template, request, session, url_for, redirect
from app import app

import json, os, boto3, re, uuid, datetime


@app.route('/transcribe/<postID>',methods=['GET'])
def transcribe(postID):

    if postID == 'new':
        result = ''
        url = ''
        file = ''
    else:

        # read transcription
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("a3Transcribe")
        response = table.get_item(Key={'postID': postID})
        status = response['Item']['status']
        file = response['Item']['filename']

        if status == 'processing':
            result = 'file is still processing...'

        else:
            s3 = boto3.resource('s3')
            obj = s3.Object('ece1779a3transcribe', postID + '.json')
            body = obj.get()['Body'].read()
            response = body.decode(encoding="utf-8")
            text = json.loads(response)

            result = text['results']['transcripts'][0]['transcript']



        # attach uploaded file
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url('get_object', Params={'Bucket': 'ece1779a3transcribe',
                                                'Key': 'upload-' + postID + '-' + str(file)}, ExpiresIn=3600)



    return render_template('transcribe/transcribe.html', postID=postID, result=result, url=url, file=file)




@app.route('/transcribe_submit/<postID>',methods=['POST'])
def transcribe_submit(postID):
    file = request.files['file']

    file_format = check_file_format(file.filename)
    print('audio_format:', file_format)
    if file_format == 'not accepted':
        return redirect(url_for('transcribe', postID='new'))

    # make new entry in databse
    postID = uuid.uuid4().hex
    timestamp = str(datetime.datetime.now())
    timestamp = timestamp.rsplit('.')[0]

    client = boto3.resource('dynamodb')
    table = client.Table("a3Transcribe")
    response = {"postID": postID,
                "filename": file.filename,
                "author": session['username'],
                "timestamp": timestamp,
                "status": "processing"
                }
    table.put_item(Item=response)

    # upload source file to s3
    path = os.path.join('/tmp', file.filename)
    file.save(path)

    s3 = boto3.client('s3')
    name = 'upload-' + postID + '-' + file.filename
    with open(path, "rb") as f:
        s3.upload_fileobj(f, "ece1779a3transcribe", name)
    os.remove(path)

    # start transcription job
    client = boto3.client('lambda')
    payload = {"postID": postID, "file": file.filename, "format": file_format}
    response = client.invoke(FunctionName='a3Transcribe', Payload=json.dumps(payload))

    # return redirect(url_for('index'))
    return redirect(url_for('transcribe',postID=postID))


@app.route('/transcribe_delete/<postID>',methods=['POST'])
def transcribe_delete(postID):
    try:
        print('delete transcription ')
        #delete from dynamodb
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("a3Transcribe")

        response = table.get_item(Key={'postID': postID})
        file = response['Item']['filename']
        table.delete_item(Key={'postID': postID})

        # delete from s3
        source_audio = 'upload-' + postID + '-' + file
        transcription = postID + '.json'

        print(source_audio)
        print(transcription)

        s3 = boto3.client('s3')
        s3.delete_object(Bucket="ece1779a3transcribe", Key=source_audio)
        s3.delete_object(Bucket="ece1779a3transcribe", Key=transcription)
    except:
        print('nothing to delete')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))




def check_file_format(name):
    if re.search('.mp3$', name) is not None:
        return 'mp3'
    elif re.search('.mp4$', name) is not None:
        return 'mp4'
    elif re.search('.m4a$', name) is not None:
        return 'mp4'
    elif re.search('.wav$', name) is not None:
        return 'wav'
    elif re.search('.flac$', name) is not None:
        return 'flac'
    else:
        return 'not accepted'
