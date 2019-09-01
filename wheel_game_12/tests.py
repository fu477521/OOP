# 演示RESTful服务并创建单元测试
import time
import json
import concurrent.futures

from wheel_game_12.Wheel_game import json_get
from wheel_game_12.game_server import roulette_server, roulette_server_00


# with concurrent.futures.ProcessPoolExecutor() as executor:
#     executor.submit(roulette_server, 4)
#     time.sleep(2)
#     json_get()
#     json_get()
#     json_get("/european/")
#     json_get("/european/")

########################
########################

import http.client

def roulette_client(method="GET", path="/", data=None):
    rest = http.client.HTTPConnection('localhost', 8080)
    if data:
        header = {'Content-type': 'application/json; charset=utf-8'}
        params = json.dumps(data).encode('UTF-8')
        rest.request(method, path, params, header)
    else:
        rest.request(method, path)
    response = rest.getresponse()
    print(response.headers)
    print(response.read())
    raw = response.read().decode("UTF-8")
    print(response.status)
    if 200 <= response.status < 300:
        print(raw)
        document = json.loads(raw)
        print(11, document )
        return document
    else:
        print(222)
        print(response.status, response.reason)
        print(response.getheaders())
        print(raw)


with concurrent.futures.ProcessPoolExecutor() as executor:
    executor.submit(roulette_server_00, 4)  # 请求4次
    time.sleep(3)  # 等待服务器开启
    print(1111)
    print(roulette_client("GET", "/player/"))   # 查看玩家状态
    print(2222)
    print(roulette_client("POST", "/bet/", {'bet': 'Black', 'amount': 2}))  # 投注
    print(3333)
    print(roulette_client("GET", "/bet/"))  # 查看投注状态
    print(4444)
    print(roulette_client("POST", "/wheel/"))  # 转动轮盘
