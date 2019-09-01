"""
用消息队列传递对象
管道流程：
1 一个全局驱动器将模拟请求放入处理队列(setup_queue)中.
2 模拟器池中的模拟器从队列获取请求，执行模拟操作，然后存入结果队列(result_queue).
3 总结者(summarizer)从队列中取得结果，然后创建一个最终结果列表
"""

import multiprocessing


class Simulate:
    """模拟操作"""
    def __init__(self, table, player, samples):
        self.table = table
        self.player = player
        self.samples = samples

    def __iter__(self):
        yield summaries


class Simulation(multiprocessing.Process):
    def __init__(self, setup_queue, result_queue):
        self.setup_queue = setup_queue
        self.result_queue = result_queue
        super().__init__()

    def run(self):
        print(self.__class__.__name__, "start")
        item = self.setup_queue.get()
        while item != (None, None):
            table, player = item
            self.sim = Simulate(table, player, samples=1)
            results = list(self.sim)
            self.result_queue.put((table, player, results[0]))
            item = self.setup_queue.get()
        print(self.__class__.__name__, "finish")


class Summarize(multiprocessing.Process):
    def __init__(self, queue):
        self.queue = queue
        super().__init__()

    def run(self):
        print(self.__class__.__name__, "start")
        count = 0
        item = self.queue.get()
        while item != (None, None, None):
            print(item)
            count += 1
            item = self.queue.get()
        print(self.__class__.__name__, "finish", count)


setup_q = multiprocessing.SimpleQueue()
result_q = multiprocessing.SimpleQueue()
result = Summarize(result_q)
result.start()

simulators = []
for i in range(4):
    sim = Simulation(setup_q, result_q)
    sim.start()
    simulators.append(sim)


# 批量生产请求
table = Table(
    decks=6, limit=50, dealer=Hit17(),
    split=ReSplit(), payout=(3, 2))
for bet in Flat, Martingale, OneThreeTwoSix:
    player = Player(SomeStrategy, bet(), 100, 25)
    for sample in range(5):
        setup_q.put(table, player)

for sim in simulators:
    setup_q.put((None, None))  # 添加哨兵对象
for sim in simulators:
    sim.join()

result_q.put((None, None, None))
result.join()