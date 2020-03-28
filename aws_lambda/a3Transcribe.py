import json, boto3, uuid, re


def lambda_handler(event, context):
    transcribe = boto3.client('transcribe')

    job_name = event['postID']
    file = event['file']
    media_format = event['format']
    job_uri = "https://" + 'ece1779a3transcribe.s3.amazonaws.com/upload-' + str(job_name) + "-" + str(file)

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat=media_format,
        LanguageCode='en-US',
        OutputBucketName='ece1779a3transcribe'
    )

    return "transcription job started"

