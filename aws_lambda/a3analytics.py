import boto3
from uuid import uuid4


# analytics for website traffic and user behaviours, record requests from user associated with type of service and file size
# function triggers by s3 object creation

# creating task and receiving result are treated as two seperate requests so both source file and processed file are recorded.
# only new tasks are recorded, retrieving an old task from list is not counted


def update_total_sum(requestType, size):
    # update sum,
    # assume infrequent website visists so no two requests are made at exact same time
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('a3Analytics')
    response = table.get_item(Key={'requestID': 'total'})

    old_data = response['Item']

    attr_req = requestType + '_req'
    attr_size = requestType + '_size'

    response = table.update_item(Key={'requestID': 'total'},
                                 UpdateExpression=
                                 'SET #attr1 = :val1, #attr2 = :val2',
                                 ExpressionAttributeNames=
                                 {'#attr1': attr_req, '#attr2': attr_size},
                                 ExpressionAttributeValues={
                                     ':val1': old_data[attr_req] + 1,
                                     ':val2': old_data[attr_size] + size
                                 }
                                 )


# update number of service requests by each each along with requested file size
def update_user_statistics(user, requestType, size):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('a3Analytics')
    try:
        # obtain old data
        response = table.get_item(Key={'requestID': user})
        old_data = response['Item']
    except:
        # create new entry in dynomodb for new user
        item = {"requestID": user, "note_req": 0, "note_size": 0, "textract_req": 0, "textract_size": 0, \
                "transcribe_req": 0, "transcribe_size": 0, "translate_req": 0, "translate_size": 0, }
        dynamodb.Table('a3Analytics').put_item(Item=item)

        response = table.update_item(Key={'requestID': user},
                                     UpdateExpression='SET #attr1 = :val1, #attr2 = :val2',
                                     ExpressionAttributeNames={'#attr1': attr_req, '#attr2': attr_size},
                                     ExpressionAttributeValues={':val1': 1, ':val2': size})
    else:
        # update with new statisitcs
        attr_req = requestType + '_req'
        attr_size = requestType + '_size'

        response = table.update_item(Key={'requestID': user},
                                     UpdateExpression=
                                     'SET #attr1 = :val1, #attr2 = :val2',
                                     ExpressionAttributeNames=
                                     {'#attr1': attr_req, '#attr2': attr_size},
                                     ExpressionAttributeValues={
                                         ':val1': old_data[attr_req] + 1,
                                         ':val2': old_data[attr_size] + size
                                     }
                                     )


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    for record in event['Records']:
        print("record", record)

        # retrive s3 info
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        size = record['s3']['object'].get('size', -1)
        event_name = record['eventName']
        event_time = record['eventTime']

        # retrieve author info from db
        requestType = bucket_name.split('ece1779a3')[1]
        postID = (object_key.split('-')[1]).split('.')[0]
        tableName = 'a3' + requestType.capitalize()

        # record analytics to db
        table = dynamodb.Table(tableName)
        response = table.get_item(Key={'postID': postID})
        author = response['Item']['author']

        item = {'requestID': str(uuid4()), 'requestType': requestType, \
                "author": author, "file": object_key, "size": size, \
                "event_time": event_time
                }
        print(item)
        dynamodb.Table('a3RequestLog').put_item(Item=item)

        update_user_statistics(author, requestType, size)
        update_total_sum(requestType, size)
    return item