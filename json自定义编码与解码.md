```python
"""创建带有编码能力的类"""
import datetime
class Post:
    def __init__(self, date, title, rst_text, tags):
        self.date = date
        self.title = title
        self.rst_text = rst_text
        self.tags = tags

    def as_dict(self):
        return dict(
            date=str(self.date),
            title=self.title,
            underline='-'*len(self.title),
            rst_text=self.rst_text,
            tag_text=" ".join(self.tags)
        )

    @property
    def _json(self):
        return dict(
            __class__=self.__class__.__name__,
            __args__=[],
            __kw__=dict(
                date=self.date,
                title=self.title,
                rst_text=self.rst_text,
                tags=self.tags,
            )
        )

from collections import defaultdict
class Blog:
    def __init__(self, title, posts=None):
        self.title = title
        self.entries = posts if posts is not None else []

    def append(self, post):
        self.entries.append(post)

    def by_tag(self):
        tag_index = defaultdict(list)
        for post in self.entries:
            for tag in post.tags:
                tag_index[tag].append(post.as_dict())
        return tag_index

    def as_dict(self):
        return dict(
            title=self.title,
            underline="="*len(self.title),
            entries=[p.as_dict() for p in self.entries],
        )

    @property
    def _json(self):
        return dict(
            __class__=self.__class__.__name__,
            __kw__={},
            __args__=[self.title, self.entries]
        )

import json
def blog_encode(obj):
    if isinstance(obj, datetime.datetime):
        fmt = "%Y-%m-%dT%H:%M:%S"
        return dict(
            __class__="datetime.datetime.strptime",
            __args__=[obj.strftime(fmt), fmt],
            __kw__={},
        )
    else:
        try:
            encoding = obj._json()
        except AttributeError:
            encoding = json.JSONEncoder.default(obj)
        return encoding

def blog_decode(some_dict):
    if set(some_dict.keys()) == set(["__class__", "__args__", "__kw__"]):
        class_ = eval(some_dict['__class__'])
        return class_(*some_dict['__args__'], **some_dict['__kw__'])
    else:
        return some_dict


travel = Blog("Travel")
travel.append(
    Post(
        date=datetime.datetime(2019, 8, 23, 13, 23, 32),
        title="Hard Aground",
        rst_text="""string""",
        tags=("#AA", "#BB", "#CC"),
    )
)
# 用自定义的编码函数，将json写入文件
with open("temp.json", "w", encoding="UTF-8") as target:
    json.dump(travel, target, separators=(',', ':'), default=blog_encode)
# 用自定义的解码函数，读取json文件
with open("some_source.json", "r", encoding="UTF-8") as source:
    obj = json.load(source, object_hook=blog_decode)
```