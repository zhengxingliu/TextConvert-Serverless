import json, boto3


# connect to API Gateway to display user usage
def lambda_handler(event, context):
    username = event['username']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('a3Analytics')
    response = table.get_item(Key={'requestID': username})

    response = response['Item']
    total_s3_size = float(
        response['note_size'] + response['textract_size'] + response['transcribe_size'] + response['translate_size'])
    total_s3_req = float(
        response['note_req'] + response['textract_req'] + response['transcribe_req'] + response['translate_req'])

    s3_storage_pc = 0.023 * total_s3_size / (1024 * 1024 * 1024)
    s3_request_pc = 0.005 * total_s3_req

    # assume each request has only 1 page from uploaded image
    textract_pc = 0.015 * float(response['textract_req'])

    translate_pc = 0.000015 * float(response['translate_size'])

    # assume audio has 44100 Hz, 16 bit/sample, and 2 channels = 14411200 bps
    transcribe_pc = 0.0004 * float((response['transcribe_size'] / 14411200))

    # dynamodb
    read = 0.25 / 1000000
    write = 1.25 / 1000000
    read_post_scan = total_s3_req / 2
    dynamodb_pc = float(response['note_req']) * (2 * read + write) + float(response['textract_req']) * (read + write) + \
                  float(response['translate_req']) * write + float(response['transcribe_req']) * (
                              read + write) + read_post_scan * read

    print(s3_request_pc)
    print(s3_storage_pc)
    print(textract_pc)
    print(translate_pc)
    print(transcribe_pc)
    print(dynamodb_pc)

    total = s3_request_pc + s3_storage_pc + textract_pc + transcribe_pc + translate_pc + dynamodb_pc
    print(total)

    #  return response['Item']
    return response


