import flask_login
from GamingFog import login_manager

# Our mock database.
users = {"foo@bar.tld": {"password": "secret", "email": "foo@bar.tld"}}


class User(flask_login.UserMixin):
    pass


def authenticate(email, password):
    if email in users:
        if users[email]["password"] == password:
            return True
    return False
