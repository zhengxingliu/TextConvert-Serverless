import json, boto3, uuid, re


# check status of transcribe jobs
def lambda_handler(event, context):
    job_name = event['job_name']

    transcribe = boto3.client('transcribe')

    read_status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    status = read_status['TranscriptionJob']['TranscriptionJobStatus']

    # update status if job is finished
    if status == "COMPLETED":
        client = boto3.resource('dynamodb')
        table = client.Table("a3Transcribe")

        table.update_item(
            Key={'postID': job_name},
            UpdateExpression='SET #attr1 = :val1',
            ExpressionAttributeNames={'#attr1': 'status'},
            ExpressionAttributeValues={':val1': 'completed'})

    return "transcribe status checked "
