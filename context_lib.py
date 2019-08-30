import os
import random

"""
上下文的异常处理：
抛出的异常会传给上下文管理器的__exit__()方法，异常的标准信息（类，参数，追踪栈）
都会作为参数传入。
两种处理方式：
- 通过返回为True的值把异常吞掉。
- 通过返回为False或None的值允许异常正常抛出。
在返回值之前可以做一些相关的处理。
"""

"""
# 在有些类库中提供了打开/关闭操作，但其中的对象不是上下文对象，
# 可以使用contextlib.closing()来形成上下文的模式（前提是对象中有close()方法）。

import contextlib

class MyClass:
    def close(self):
        pass
    
with contextlib.closing(MyClass()) as my_obj:
    # process(my_obj)
    pass
"""


class Updating:
    """
    在写文件之前对原先的文件进行备份，如果它不存在，则不会有任何行为。

    使用示例：
    with Updating("some_file"):
        with open("some_file", "w") as f:
            process(f)
    将原文件重命名为some_file-copy并备份，如果上下文出现异常没有正常工作，
    把文件重命名为some_file-error并重新旧文件为some_file。
    """
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        try:
            self.previous = self.filename + "-copy"
            os.rename(self.filename, self.previous)
        except FileNotFoundError:
            self.previous = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                os.rename(self.filename, self.filename + "-error")
            except FileNotFoundError:
                pass
            if self.previous:
                os.rename(self.previous, self.filename)


class KnownSequence:
    """
    自定义随机种子，保证在上下文中多次使用随机数时，随机算法一致，固定随机数。
    示例：
    with KnownSequence():
        print(tuple(random.randint(-1, 26) for i in range(6)))

    工厂模式：
    with KnownSequence(size=6) as obj:
        process(obj)
    """
    def __init__(self, seed=0):
        self.seed = 0

    def __enter__(self):
        self.was = random.getstate()
        random.seed(self.seed, version=1)
        return self
        # 可以通过返回指定的类，来形成上下管理器工厂
        # return MyClass(*args, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        random.setstate(self.was)


