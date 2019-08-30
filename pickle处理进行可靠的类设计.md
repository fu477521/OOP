## pickle模块
pickle模块可以将一个复杂的对象转换为一个字节数组，并且使用相同的内部结构将字节流转换为一个对象

```python
import pickle
with open("aaa.p", "wb") as target: # 注意使用的是wb
    pickle.dump(obj, target)

with open("aaa.p", "rb") as source: # 注意使用的是rb
    copy = pickle.load(source)

```

## 对pickle处理进行可靠的类设计
- 当一个类被unpickle（解压）的时候，会绕过__init__()方法，所以如果在__init__()里处理一些逻辑时需要注意。

```python
class Hand:
    def __init__(self):
        pass
    def __getstate__(self):
        """picking时，会调用"""
        return self.__dict__
    def __setstate__(self, state):
        """unpickling时，调用"""
        self.__dict__.update(state)
        # process something

```

## 安全性和全局性
在pickle流中的一个全局名称（类名或函数名）可能会导致一段自由代码的执行。
所以在类设计时必须对pickle.Unpickler类进行扩展，重写find_class()方法。
需要考虑一下问题：
- 必须阻止内置的exec()和eval()函数的使用
- 必须阻止导致不安全的模块或包的使用（sys，os...)
- 允许应用程序模块的使用
```python
import builtins
import pickle
class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "builtins":
            if name not in ("exec", "eval"):  # 禁止exec()和eval()
                return getattr(builtins, name)
        elif module == "__main__":  # 只允许在__main__使用
            return globals()[name]
        # elif module in any of our application modules...
        else:
            raise pickle.UnpicklingError(
                "global '{module}.{name}' is forbidden".format(module=module, 
                                                               name=name)
            )

```