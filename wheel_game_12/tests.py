# 演示RESTful服务并创建单元测试
import time
import concurrent.futures

from wheel_game_12.Wheel_game import json_get, roulette_server


with concurrent.futures.ProcessPoolExecutor() as executor:
    executor.submit(roulette_server, 4)
    time.sleep(2)
    json_get()
    json_get()
    json_get("/european/")
    json_get("/european/")