import json
import boto3

from flask import render_template, request, session, url_for, redirect
from app import app


@app.route('/',methods=['GET'])
def index():
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    #return render_template("index.html")
    #return redirect(url_for('textnote'))
    return redirect(url_for('homepage', username=session['username']))


@app.route('/login', methods=['POST','GET'])
def login():
    username = None
    error = None
    if 'username' in session:
        username = session['username']
    if 'error' in session:
        error = session['error']
        session.pop('error')

    return render_template("login/login.html", error=error, username=username)


@app.route('/login_submit', methods=['POST'])
def login_submit():

    username = request.form.get('username', "")
    password = request.form.get('password', "")

    if username == "" or password == "":
        error = "Error: All fields are required!"
        return render_template("login/login.html", error=error, username=username, )


    client = boto3.client('lambda')
    payload = {
      "action": "login",
      "username": username,
      "password": password
    }

    response = client.invoke(
        FunctionName='a3UserLogin',
        Payload=json.dumps(payload)
    )

    response_payload = json.loads(response['Payload'].read().decode("utf-8"))
    print ("login response: {}".format(response_payload))

    if response_payload['body'] == "login failed":
        session['error'] = "Invalid username or password"
        return render_template("login/login.html", error=session['error'])

    print(response_payload['body']['username'], 'logged in')
    session['authenticated'] = True
    session.permanent = True
    session['username'] = username
    if 'error' in session:
        session.pop('error')
    return redirect(url_for('index'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/new_user', methods=['GET','POST'])
def new_user():
    username = None
    error = None
    if 'username' in session:
        username = session['username']
    if 'error' in session:
        error = session['error']
        session.pop('error')
    return render_template("login/new.html", error=error, username=username)


@app.route('/new_user_submit', methods=['POST'])
def new_user_submit():

    username = request.form.get('username', "")
    password = request.form.get('password', "")
    confirm_pw = request.form.get('confirm', "")

    if username == "" or password == "":
        error = "Error: All fields are required!"
        return render_template("login/new.html", title="New User", error=error, username=username )
    if password != confirm_pw:
        error = "Error: Re-entered password unmatched!"
        return render_template("login/new.html", title="New User", error=error, username=username)

    client = boto3.client('lambda')
    payload = {
        "action": "new_user",
        "username": username,
        "password": password
    }

    response = client.invoke(
        FunctionName='a3UserLogin',
        Payload=json.dumps(payload)
    )

    response_payload = json.loads(response['Payload'].read().decode("utf-8"))
    print("login response: {}".format(response_payload))

    if response_payload['body'] == "user existed":
        error = "Error: user existed"
        return render_template("login/new.html", title="New User", error=error, username=username)

    return redirect(url_for('login'))






