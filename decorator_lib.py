import functools
import logging


# 类方法的状态追踪器
def audit(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        audit_log = logging.getLogger('audit')
        try:
            before = repr(self)
        except AttributeError as e:
            before = repr(e)
        after = None
        try:
            result = method(self, *args, **kwargs)
            after = repr(self)
        except Exception as e:
            audit_log.exception("%s before %s\n after %s", method.__qualname__, before, after)
            raise
        audit_log.info("%s before %s\n after %s", method.__qualname__, before, after)
        return result
    return wrapper


def logged(cls):
    """
    装饰类的装饰器，为类添加一个类属性--logger。
    示例：
    @logged
    class SomeClass:
        def method(self, *args):
            self.logger.info("xxx")

    :param cls: 传入的类对象
    :return: cls
    """
    cls.logger = logging.getLogger(cls.__qualname__)

    # 向类中添加方法
    # def method(self):
    #     pass
    # cls.method_ = method
    return cls




