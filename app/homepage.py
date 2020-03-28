import json
import boto3

from flask import render_template, request, session, url_for, redirect
from app import app
from datetime import datetime


@app.route('/home/<username>',methods=['GET'])
def homepage(username):

    client = boto3.client('lambda')
    payload = {'author': session['username']}
    response = client.invoke(
        FunctionName='a3ReadPosts',
        Payload=json.dumps(payload)
    )
    posts = json.loads(response['Payload'].read().decode("utf-8"))

    textnote = posts['a3Note']
    textract = posts['a3Textract']
    transcribe = posts['a3Transcribe']
    translate = posts['a3Translate']

    textnote = sorted(textnote, key=lambda i: i['timestamp'], reverse=True)
    textnote = sorted(textnote, key=lambda i: i['timestamp'], reverse=True)
    textract = sorted(textract, key=lambda i: i['timestamp'], reverse=True)
    transcribe = sorted(transcribe, key=lambda i: i['timestamp'], reverse=True)
    translate = sorted(translate, key=lambda i: i['timestamp'], reverse=True)
    translate = sorted(translate, key=lambda i: i['timestamp'], reverse=True)

    return render_template('homepage/home.html',
                           textnote = textnote, textract=textract, transcribe=transcribe, translate=translate)


@app.route('/test/hello',methods=['GET'])
def test():
    return render_template('index.html')

