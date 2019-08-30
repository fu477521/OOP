## 使用ABC可调用对象进行设计

```python
import collections

class BettingStrategy(collections.abc.Callable):
    def __init__(self):
        self.win = 0
        self.loss = 0

    def __call__(self, *args, **kwargs):
        return 1

class BettingMartingale(BettingStrategy):
    def __init__(self):
        self._win = 0
        self._loss = 0
        self.stage = 1

    @property
    def win(self):
        return self._win

    @win.setter
    def win(self, value):
        self._win = value
        self.stage = 1  # 赢了就重新置1

    @property
    def loss(self):
        return self._loss

    @loss.setter
    def loss(self, value):
        self._loss = value
        self.stage *= 2  # 输了就加注

    def __call__(self, *args, **kwargs):
        return self.stage  # 直接调用返回注码


"""
>>> bet = BettingMartingale()
>>> bet()
Out[15]: 1
>>> bet.win += 1
>>> bet()
Out[17]: 1
>>> bet.loss += 1
>>> bet()
Out[19]: 2
>>> bet.loss += 1
>>> bet()
Out[21]: 4
"""


# 上面的代码看起来可能有些臃肿，可以使用__setattr__()来简化定义
class BettingMartingale2(BettingStrategy):
    def __init__(self):
        self.win = 0
        self.loss = 0
        self.stage = 1

    def __setattr__(self, key, value):
        if key == 'win':
            self.stage = 1
        elif key == 'loss':
            self.stage *= 2
        super().__setattr__(key, value)

    def __call__(self):
        return self.stage


"""
>>> bet2 = BettingMartingale()
>>> bet2()
Out[15]: 1
>>> bet2.win += 1
>>> bet2()
Out[17]: 1
>>> bet2.loss += 1
>>> bet2()
Out[19]: 2
>>> bet2.loss += 1
>>> bet2()
Out[21]: 4
"""

```
可调用对象的设计：
优点：
- 可以使用collections.abc.Callable来确保可调用API被正确创建，并且让读代码的人很明确地了解类的目的。
- 可调用对象可以保存状态，记忆化设计模式很好的运用了有状态的可调用对象。
缺点：
- 需要的语法更多。

### 使用collections.abc.Callable来构造对象还可以帮助调试
```python
import collections


class Power(collections.abc.Callable):
    def __call_(self, x, n, *args, **kwargs):  # 少一个下划线
        p = 1
        for i in range(n):
            p *= x
        return p


"""
>>> pow = Power()
Traceback (most recent call last):
  File "/IPython/core/interactiveshell.py", line 3296, in run_code
    exec(code_obj, self.user_global_ns, self.user_ns)
  File "<ipython-input-3-c7fb4f72bc65>", line 1, in <module>
    pow = Power()
TypeError: Can't instantiate abstract class Power with abstract methods __call__
"""

```
### 而不使用使用collections.abc.Callable的情况，给出的错误提示就显得模糊：
```python

class Power:
    def __call_(self, x, n, *args, **kwargs):  # 少一个下划线
        p = 1
        for i in range(n):
            p *= x
        return p


"""
>>> pow = Power()
>>> pow(2,10)
Traceback (most recent call last):
  File "/Users/lym/cmlpy/venv3.7/lib/python3.7/site-packages/IPython/core/interactiveshell.py", line 3296, in run_code
    exec(code_obj, self.user_global_ns, self.user_ns)
  File "<ipython-input-6-60bf32bfc18f>", line 1, in <module>
    pow(2,10)
TypeError: 'Power' object is not callable
"""
```

### 提高可调用对象的性能
#### 使用更好的算法
```python
# 快速幂算法
import collections
class Power(collections.abc.Callable):
    def __call__(self, x, n):
        if n == 0: return 1
        elif n % 2 == 1:
            return self.__call__(x, n-1) * n
        else:
            t = self.__call__(x, n//2)
            return t * t
```
#### 记忆化与缓存
```python
# 使用dict缓存
import collections
class Power(collections.abc.Callable):
    def __init__(self):
        self.memory = {}
    def __call__(self, x, n):
        if (x, n) not in self.memory:
            if n == 0: 
                self.memory[x, n] = 1
            elif n % 2 == 1:
                self.memory[x, n] = self.__call__(x, n-1) * n
            elif n % 2 == 0:
                t = self.__call__(x, n//2)
                self.memory[x, n] = t * t
            else:
                raise Exception("Logic Error")
        return self.memory[x,n]
        
# 使用lru_cache来装饰函数达到缓存的效果
from functools import lru_cache
@lru_cache(None)    # 最近最少使用原则(Least Recently Used)
def power(x, n):
    if n == 0: return 1
    elif n % 2 == 1:
        return power(x, n-1) * n
    else:
        t = power(x, n//2)
        return t * t

```