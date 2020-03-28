import json
import uuid
import datetime, os, boto3


# handles text based notes

def lambda_handler(event, context):
    postID = event['postID']
    text = event['text']
    author = event['author']
    source_lan = event['source_lan']
    target_lan = event['target_lan']

    if postID == "new":
        # create txt file
        postID = uuid.uuid4().hex

    # save txt to s3
    path = os.path.join('/tmp', "source-" + postID + ".txt")
    with open(path, "w") as text_file:
        text_file.write(text)

    s3 = boto3.client('s3')
    with open(path, "rb") as f:
        s3.upload_fileobj(f, "ece1779a3translate", "source-" + postID + ".txt")

    # translate
    translate = boto3.client('translate')
    trans_path = os.path.join('/tmp', 'trans-' + postID + '.txt')

    # write translation file
    with open(trans_path, "w") as text_file:
        f = open(path, "r")
        for line in f:
            result = translate.translate_text(Text=line, SourceLanguageCode=source_lan, TargetLanguageCode=target_lan)
            text_file.write(result.get('TranslatedText') + '\n')
        f.close()

    # save translation to s3
    with open(trans_path, "rb") as f:
        s3.upload_fileobj(f, "ece1779a3translate", 'trans-' + postID + '.txt')

    return postID
