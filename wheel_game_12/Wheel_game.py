import random
from collections.abc import Callable


class Wheel(Callable):
    def __init__(self):
        self.rng = random.Random()
        self.bins = [
            {
                str(n): (35, 1),
                self.redblack(n): (1, 1),
                self.hilo(n): (1, 1),
                self.evenodd(n): (1, 1),
             } for n in range(1, 37)
        ]

    def __call__(self, environ, start_response, *args, **kwargs):
        winner = self.spin()
        status = '200 OK'
        headers = [('Content-type', 'application/json; charset=utf-8')]
        start_response(status, headers)
        return [json.dumps(winner).encode('UTF-8')]

    @staticmethod
    def redblack(n):
        return "Red" if n in (1, 3, 5, 7, 9, 12, 14, 16, 18, 19,
                              21, 23, 25, 27, 30, 32, 34, 36) else "Black"

    @staticmethod
    def hilo(n):
        return "Hi" if n >= 19 else "Lo"

    @staticmethod
    def evenodd(n):
        return "Even" if n % 2 == 0 else "Odd"

    def spin(self):
        return self.rng.choice(self.bins)


class Zero:
    """单零"""
    def __init__(self):
        super().__init__()
        self.bins += [{"0": (35, 1)}]


class DoubleZero:
    """双零"""
    def __init__(self):
        super().__init__()
        self.bins += [{"00": (35, 1)}]


class American(Zero, DoubleZero, Wheel):
    """美式玩法"""
    pass


class European(Zero, Wheel):
    """欧式玩法"""
    pass

american = American()
european = European()
# print("SPIN", american.spin())


# WSGI程序
import sys
import wsgiref.util
import json

def wheel(environ, start_response):
    # 解析environ['PATH_INFO']的值
    request = wsgiref.util.shift_path_info(environ)
    # 在调用start_response之前，任何打印信息都会导致异常，所以需要设置file=sys.stderr
    print("wheel", request, file=sys.stderr)
    if request.lower().startswith('eu'):
        winner = european.spin()
    else:
        winner = american.spin()
    status = '200 OK'
    headers = [('Content-type', 'application/json; charset=utf-8')]
    start_response(status, headers)
    return [json.dumps(winner).encode('UTF-8')]


class Wheel00(Callable):
    def __init__(self):
        self.am = American()
        self.eu = European()

    def __call__(self, environ, start_response):
        # 解析environ['PATH_INFO']的值
        request = wsgiref.util.shift_path_info(environ)
        # 在调用start_response之前，任何打印信息都会导致异常，所以需要设置file=sys.stderr
        print("wheel", request, file=sys.stderr)
        if request.lower().startswith('eu'):
            response = self.eu(environ, start_response)
        else:
            response = self.am(environ, start_response)
        return response


# 启动服务器的演示版本
from wsgiref.simple_server import make_server

def roulette_server(count=1):
    # 创建服务器对象，这个对象会回调wheel()处理请求。
    httpd = make_server('', 8080, wheel)  #
    if count is None:
        httpd.serve_forever()
    else:
        for c in range(count):
            httpd.handle_request()


# 实现REST客户端
import http.client
import json

def json_get(path="/"):
    rest = http.client.HTTPConnection('localhost', 8080)
    rest.request("GET", path)
    response = rest.getresponse()
    print(response.status, response.reason)
    print(response.getheaders())
    raw = response.read().decode('utf-8')
    if response.status == 200:
        document = json.loads(raw)
        print(document)
    else:
        print(raw)





if __name__ == '__main__':
    roulette_server()
