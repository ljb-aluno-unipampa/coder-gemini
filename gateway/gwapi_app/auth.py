from functools import wraps
from flask import request, Response, current_app

def check_auth(username, password):
    return username == current_app.config['API_USER'] and password == current_app.config['API_PASS']

def authenticate():
    return Response('Autenticação necessária', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated