## shelve的ACID属性说明
- shelve模块没有直接支持原子性，它没有提供处理包含多个操作的事务的方法。
- shelve模块不保证所有类型的改变都可以持久化。


### 创建shelf
shelve.open()需要两个参数：文件名和文件访问模式。
访问模式：
- 'c' 打开已存在的shelf，不存在则新建。
- 'r' 只读方式打开shelf。
- 'n' 新建空的shelf，如果已存在会覆盖。
- 'w' 必须指定已存在的shelf，否则抛出异常

注意：shelf必须要关闭才能确保它被正确写入磁盘中。contextlib.closing()来确保关闭。

```python
import shelve
from contextlib import closing
with closing(shelve.open('some_file')) as shelf:
    process(shelf)

```

## 设计一个带有简单代理键的类
```python
import datetime

class Blog:
    def __init__(self, title, *post):
        self.title = title
    def as_dict(self):
        return dict(
            title=self.title,
            underline = "="*len(self.title),
        )
"""
>>> import shelve
>>> shelf = shelve.open('blog')
>>> b1 = Blog(title="Travel Blog")
>>> b1._id = "Blog:1"
>>> shelf[b1._id] = b1
>>> shelf
Out[9]: <shelve.DbfilenameShelf at 0x104d3b9b0>
>>> shelf["Blog:1"]
Out[10]: <__main__.Blog at 0x104af0710>
>>> shelf.close()
"""
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
            underline="-" * len(self.title),
            rst_text=self.rst_text,
            tag_text=" ".join(self.tags),
        )

p2 = Post(
    date=datetime.datetime(2019,8,25,11,24),
    title="First Title",
    rst_text="""rst_text.rst_text""",
    tags=("#AAA", "#BBB", "#CCC")
)
p3 = Post(
    date=datetime.datetime(2019,8,25,12,44),
    title="Second Title",
    rst_text="""Second rst_text.Second rst_text""",
    tags=("#AAA", "#BBB", "#DDD")
)

"""
>>> shelf = shelve.open("blog")
>>> owner = shelf['Blog:1']
>>> p2._parent = owner._id
>>> p2._id = p2._parent + ":Post:2"
>>> shelf[p2._id] = p2
>>> p3._parent = owner._id
>>> p3._id = p3._parent + ":Psot:3"
>>> shelf[p3._id] = p3
>>> list(shelf.keys())
Out[28]: ['Blog:1:Psot:3', 'Blog:1', 'Blog:1:Post:2']
>>> p2._parent
Out[29]: 'Blog:1'
>>> p2._id
Out[30]: 'Blog:1:Post:2'
"""

```

## 为shelve设计数据访问层
```python
import shelve
from collections import defaultdict
class Access:
    def new(self, filename):
        """新建一个空的shelf"""
        self.database = shelve.open(filename, 'n')
        self.max = {"Post": 0, "Blog": 0}
        self.sync()
        self.database['_DB:Blog'] = list()  # 创建顶层索引列表
        self.database['_DB:Blog_Title'] = defaultdict(list)  # 创建标题索引列表
        
    def open(self, filename):
        """打开一个已存在的shelf"""
        self.database = shelve.open(filename, "w")
        self.max = self.database['_DB:max']
    def close(self):
        if self.database:
            self.database['_DB:max'] = self.max
            self.database.close()
        self.database = None
    def sync(self):
        self.database['_DB:max'] = self.max
        self.database.sync()
    def quit(self):
        self.close()
    # 操作方法
    def add_blog(self, blog):
        self.max['Blog'] += 1
        key = "BLog:{id}".format(id=self.max['Blog'])
        blog._id = key
        blog._post_list = []  # 创建索引列表
        self.database[blog._id] = blog  # 更新blog
        self.database['_DB:Blog'].append(blog._id)  # 添加顶层索引
        blog_title = self.database['_DB:Blog_Title']  # dict
        blog_title[blog.title].append(blog._id)
        self.database["_DB:Blog_Title"] = blog_title
        return blog
    def get_blog(self, id):
        return self.database[id]
    def update_blog(self, blog):
        self.database[blog._id] = blog
        blog_title = self.database['_DB:Blog_Title']
        # 移除
        empties = []
        for k in blog_title:
            if blog._id in blog_title[k]:
                blog_title[k].remove(blog._id)
                if len(blog_title[k]) == 0: empties.append(k)
        # 清理索引表
        for k in empties:
            del blog_title[k]
        # 添加索引
        blog_title[blog.title].append(blog._id)
        self.database['_DB:Blog_Title'] = blog_title
        
    def add_post(self, blog, post):
        self.max["Post"] += 1
        try:
            key = "{blog}:Post:{id}".format(blog=blog._id, id=self.max["Post"])
        except AttributeError:
            raise OperationError("Blog not added")
        post._id = key
        post._blog = blog._id
        self.database[post._id] = post
        blog._post_list.append(post._id)    # 加入索引
        self.database[blog._id] = blog      # 更新shelf
        return post
    def get_post(self):
        return self.database[id]
    def replace_post(self, post):
        self.database[post._id] = post
        return post
    def delete_post(self, post):
        del self.database[post._id]
        blog = self.database[post._blog]
        blog._post_list.remove(post._id)
        self.database[blog._id] = blog
        
    # 遍历查询
    def __iter__(self):
        for k in self.database:
            if k[0] == "_": continue
            yield self.database[k]
            
    def blog_iter(self):
        # for k in self.database:
        #     if not k.startswith("Blog:"): continue
        #     if ":Post:" in k: continue  # 跳过文章类
        #     yield self.database[k]
        return (self.database[k] for k in self.database['_DB:Blog'])
        
    def blog_title_iter(self, title):
        blog_title = self.database['_DB:Blog_Title']
        return (self.database[k] for k in blog_title[title])
        
    def post_iter(self, blog):
        # for k in blog._post_list:
        #     yield self.database[k]
        return (self.database[k] for k in blog._post_list)  # 生成器表达式
        
    def title_iter(self, blog, title):
        return (p for p in self.post_iter(blog) if p.title == title)
        
# 演示
from contextlib import closing
with closing(Access()) as access:
    access.new("blog")
    access.add_blog(b1)
    
    for post in p2, p3:
        access.add_post(b1, post)
    
    b = access.get_blog(b1._id)
    for p in access.post_iter(b):
        print(p._id, p)
    access.quit()

```
可以用writeback=True模式打开shelf，代替更新索引。
