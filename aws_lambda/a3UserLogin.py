# from __future__ import print_function
import json
import boto3
import hashlib, random

from boto3.dynamodb.conditions import Key, Attr


def lambda_handler(event, context):
    # query for existing user in database
    client = boto3.resource('dynamodb')
    table = client.Table("a3User")

    action = event['action']
    username = event['username']
    password = event['password']
    item = table.query(KeyConditionExpression=Key('username').eq(username))

    # register new user
    if action == 'new_user':

        # check if user existed
        if item['Items'] != []:
            return {
                'statusCode': 409,
                'body': "user existed"
            }

        # save password as hash and salt
        salt = str(random.getrandbits(16))
        salted_password = "{}{}".format(salt, password)
        m = hashlib.md5()
        m.update(salted_password.encode('utf-8'))
        hash = m.digest()

        response = {'username': username, 'hash': str(hash), 'salt': str(salt)}

        table.put_item(Item=response)

        return {
            'statusCode': 200,
            'body': "user created"
        }

    # user login
    elif action == 'login':

        # check if user exist
        if item['Items'] == []:
            return {
                'statusCode': 400,
                'body': "login failed"
            }

        # valid login by comparing salt and hash from database
        salt = item['Items'][0]['salt']
        hash = item['Items'][0]['hash']

        salted_password = "{}{}".format(salt, password)
        m = hashlib.md5()
        m.update(salted_password.encode('utf-8'))
        new_hash = m.digest()

        if str(hash) == str(new_hash):
            return {
                'statusCode': 200,
                'body': {"username": username}
            }
        else:
            return {
                'statusCode': 400,
                'body': "login failed"
            }


