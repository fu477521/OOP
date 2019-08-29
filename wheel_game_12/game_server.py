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