"""
创建安全的REST服务（验证和授权）

"""

from hashlib import sha256
import os


class Authentication:
    iterations = 1000
    # __slots__ =

    def __init__(self, username, password):
        self.username = username
        self.salt = os.urandom(24)
        self.hash = self._iter_hash(self.iterations, self.salt, username, password)

    @staticmethod
    def _iter_hash(iterations, salt, username, password):
        seed = salt + b":" + username + b":" + password
        for i in range(iterations):
            seed = sha256(seed).digest()
        return seed

    def __eq__(self, other):
        return self.username == other.username and self.hash == other.hash

    def __hash__(self):
        return hash(self.hash)

    def __repr__(self):
        salt_x = "".join(("{0:x}".format(b) for b in self.salt))
        hash_x = "".join(("{0:x}".format(b) for b in self.hash))
        return "{username} {iterations:d}:{salt}:{hash}".format(
            username=self.username, iterations=self.iterations,
            salt=salt_x, hash=hash_x
        )

    def match(self, password):
        test = self._iter_hash(self.iterations, self.salt,
                               self.username, password)
        return self.hash == test


class Users(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self[""] = Authentication(b"__dummy__", b"Dosen't Matter")

    def add(self, authentication):
        if authentication.username == "":
            raise KeyError("Invalid Authentication")
        self[authentication.username] = authentication

    def match(self, username, password):
        if username in self and username != "":
            return self[username].match(password)
        else:
            return self[""].match(b"Something which dosen't match")



import base64
from wheel_game_12.game_server import WSGI


class Authenticate(WSGI):
    """WSGI验证程序"""
    def __init__(self, users, target_app):
        self.users = users  # 用户池
        self.target_app = target_app

    def __call__(self, environ, start_response, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in environ:  # 必须提供HTTP_AUTHORIZATION
            scheme, credentials = environ['HTTP_AUTHORIZATION'].split()
            if scheme == "Basic":  # 请求头的验证模式必须是Basic
                username, password = base64.b64decode(credentials).split(b":")
                if self.users.match(username, password):
                    environ['Authentication.username'] = username
                    return self.target_app(environ, start_response)
        status = "401 UNAUTHORIZED"
        headers = [('Content-type', 'text/plain; charset=utf-8'),
                   ('WWW-Authenticate', 'Basic realm="roulette@localhost"')]
        start_response(status, headers)
        return ["Not authorized".encode('utf-8')]
