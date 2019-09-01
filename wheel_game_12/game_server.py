# 启动服务器的演示版本
from wsgiref.simple_server import make_server
from wheel_game_12.Wheel_game import wheel


def roulette_server(count=1):
    # 创建服务器对象，这个对象会回调wheel()处理请求。
    httpd = make_server('', 8080, wheel)  #
    if count is None:
        httpd.serve_forever()
    else:
        for c in range(count):
            httpd.handle_request()


######################################
# 方案二
######################################
import json
import wsgiref.util
from collections.abc import Callable
from wheel_game_12.Wheel_game import Table


class WSGI(Callable):
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class RESTException(Exception):
    pass


class Roulette(WSGI):
    """定义一个封装其他应用程序的WSGI应用程序"""
    def __init__(self, wheel):
        self.table = Table(100)
        self.rounds = 0
        self.wheel = wheel

    def __call__(self, environ, start_response, *args, **kwargs):
        app = wsgiref.util.shift_path_info(environ)
        try:
            if app.lower() == "player":
                return self.player_app(environ, start_response)
            elif app.lower() == "bet":
                return self.bet_app(environ, start_response)
            elif app.lower() == "wheel":
                return self.wheel_app(environ, start_response)
            else:
                raise RESTException("404 NOT_FOUND",
                                    "Unknown app in {SCRIPT_NAME}/{PATH_INFO}".format_map(environ))
        except RESTException as e:
            status = e.args[0]
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers, sys.exc_info())
            return [repr(e.args).encode("UTF-8")]

    def player_app(self, environ, start_response):
        if environ['REQUEST_METHOD'] == "GET":
            details = dict(
                stake=self.table.stake,
                rounds=self.rounds
            )
            status = '200 OK'
            headers = [('Content-type', 'application/json;charset=utf-8')]
            start_response(status, headers)
            return [json.dumps(details).encode('UTF-8')]
        else:
            raise RESTException("405 METHOD_NOT_ALLOWED",
                                "Method '{REQUEST_METHOD}' not allowed".format_map(environ))

    def bet_app(self, environ, start_response):
        if environ['REQUEST_METHOD'] == "GET":
            details = dict(
                stake=self.table.bets  # 投注的信息
            )
        elif environ['REQUEST_METHOD'] == "POST":  # 定义投注的数据
            size = int(environ['CONTENT_LENGTH'])  # 字节流的长度
            raw = environ['wsgi.input'].read(size).decode("UTF-8")  # 截取相应长度，然后解码
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    data = [data]
                for detail in data:
                    self.table.place_bet(detail['bet'], int(detail['amount']))
            except Exception as e:
                raise RESTException("403 FORBIDDEN",
                                    "Bet {raw!r}".format(raw=raw))
            details = dict(self.table.bets)
        else:
            raise RESTException("405 METHOD_NOT_ALLOWED",
                                "Method '{REQUEST_METHOD}' not allowed".format_map(environ))

        status = '200 OK'
        headers = [('Content-type', 'application/json; charset=utf-8')]
        start_response(status, headers)
        return [json.dumps(details).encode('UTF-8')]

    def wheel_app(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'POST':
            size = int(environ['CONTENT_LENGTH'])
            # """确认无参，如果有参，读取并忽略数据，这样避免套接字崩溃"""
            if size != '':
                raw = environ['wsgi.input'].read(size).decode("UTF-8")
                raise RESTException("403 FORBIDDEN",
                              "Data '{raw!r}' not allowed".format_map(raw=raw))
            spin = self.wheel.spin()
            payout = self.table.resolve(spin)
            self.rounds += 1
            details = dict(
                spin=spin,
                payout=payout,
                stake=self.table.stake,
                rounds=self.rounds
            )
            status = '200 OK'
            headers = [('Content-type', 'application/json; charset=utf-8')]
            start_response(status, headers)
            return [json.dumps(details).encode('UTF-8')]
        else:
            raise RESTException("405 METHOD_NOT_ALLOWED",
                                "Method '{REQUEST_METHOD}' not allowed".format_map(environ))

# 创建roulette服务器
def roulette_server_00(count=1):
    from wsgiref.simple_server import make_server
    from wsgiref.validate import validator
    from wheel_game_12.Wheel_game import American
    wheel = American()
    roulette = Roulette(wheel)  # application
    debug = validator(roulette)  # 验证应用程序使用的接口
    httpd = make_server('', 8080, debug)
    if count is None:
        httpd.serve_forever()
    else:
        for c in range(count):
            httpd.handle_request()


if __name__ == '__main__':
    # roulette_server()
    roulette_server_00()
