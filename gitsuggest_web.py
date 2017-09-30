import os
from functools import wraps
from urllib.parse import parse_qs, urlencode
from uuid import uuid4

import requests
from flask import Flask, redirect, render_template, request, session
from gitsuggest import GitSuggest


app = Flask(__name__)
app.secret_key = uuid4().hex
app.debug = True

callback_url = os.environ['CALLBACK_URL']
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
state = uuid4().hex

AUTHORIZE_URL = 'https://github.com/login/oauth/'


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'token' not in session:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated


@app.route('/')
def home():
    return render_template('login.htm.j2')


@app.route('/login')
def login():
    return redirect(
        AUTHORIZE_URL + 'authorize?' + urlencode({
            'client_id': client_id,
            'redirect_uri': callback_url,
            'state': state,
            'allow_signup': True
        })
    )


@app.route('/callback')
def callback():
    # assert request.args.get('state') == state, "State mismatch from callback"

    params = {
        'code': request.args.get('code'),
        'client_id': client_id,
        'client_secret': client_secret,
        'state': state
    }
    response = requests.post(AUTHORIZE_URL + 'access_token', data=params)
    parsed_args = parse_qs(response.text)

    session['token'] = parsed_args['access_token'][0]
    return redirect('/suggest')


@app.route('/suggest')
@requires_auth
def suggest():
    gs = GitSuggest(token=session['token'])
    gs_repos = list(gs.get_suggested_repositories())

    if gs_repos:
        return render_template(
            'suggest.htm.j2',
            user_login=gs.github.get_user().login,
            repos=gs_repos)
    else:
        return render_template(
            '404.htm.j2',
            user_login=gs.github.get_user().login)


if __name__ == '__main__':
    app.run()
