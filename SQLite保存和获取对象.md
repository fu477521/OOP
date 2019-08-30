```SQLite
CREATE TABLE BLOG(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TITLE TEXT
);

CREATE TABLE POST(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    DATE TIMESTAMP,
    TITLE TEXT,
    RST_TEXT TEXT,
    BLOG_ID INTEGER REFERENCES BLOG(ID)
);
CREATE TABLE TAG(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PHRASE TEXT UNIQUE ON CONFLICT FAIL
);
# 关联表
CREATE TABLE ASSOC_POST_TAG(
    POST_ID INTEGER REFERENCES POST(ID),
    TAG_ID INTEGER REFERENCES TAG(ID)
);
```
### 创建数据库
```python
import sqlite3

sql_ddl = """
CREATE TABLE BLOG(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TITLE TEXT
);
CREATE TABLE POST(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    DATE TIMESTAMP,
    TITLE TEXT,
    RST_TEXT TEXT,
    BLOG_ID INTEGER REFERENCES BLOG(ID)
);
CREATE TABLE TAG(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PHRASE TEXT UNIQUE ON CONFLICT FAIL
);
CREATE TABLE ASSOC_POST_TAG(  # 关联表
    POST_ID INTEGER REFERENCES POST(ID),
    TAG_ID INTEGER REFERENCES TAG(ID)
);
"""
db = sqlite3.connect('myblog.db')
db.executescript(sql_ddl)
# 等同如下操作
cur = db.cursor()
for stmt in sql_ddl.split(';'):
    cur.execute(stmt)

```

### 使用SQL的DML语句完成CRUD
- SQL语句的占位符（位置绑定？/关键词绑定:name）
```python
import sqlite3
# 插入数据
create_blog = """
INSERT INTO BLOG(TITLE) VALUES(?)
"""
db = sqlite3.connect('myblog.db')
db.execute(create_blog, ("Travel Blog",))

# 修改数据
update_blog = """
UPDATE BLOG SET TITLE=:new_title WHERE TITLE=:old_title
"""
db.execute("BEGIN")  # 开启事务
db.execute(update_blog, 
    dict(
        new_title='2018-2019 Travel', 
        old_title='Travel Blog')
)
db.commit()  # 提交事务

# 级联删除数据
delete_post_tag_by_blog_title = """
DELETE FROM ASSOC_POST_TAG 
WHERE POST_ID IN (
    SELECT DISTINCT POST_ID 
    FROM BLOG JOIN POST ON BLOG.ID=POST.BLOG_ID 
    WHERE BLOG.TITLE=:old_title
)
"""
delete_blog_by_blog_title="""
DELETE FROM POST WHERE BLOG_ID IN (
    SELECT ID FROM BLOG WHERE TITLE=:old_title
)
"""
delete_blog_by_title = """
DELETE FROM BLOG WHERE TITLE=:old_title
"""
try:
    with db: # 通过上下文管理器开启事务功能及失败回滚
        title = dict(old_title='2018-2019 Travel')
        db.execute(delete_post_tag_by_blog_title, title)
        db.execute(delete_blog_by_blog_title, title)
        db.execute(delete_blog_by_title, title)
    print("Delete finished normally.")
except Exception as e:
    print("Rolled back due to {0}".format(e))

# 查询
query_blog_by_title = """
SELECT * FROM BLOG WHERE TITLE=?
"""
for blog in db.execute(query_blog_by_title, ("2018-2019 Travel",)):
    print(blog[0], blog[1])
# 或者如下操作
cur = db.cursor()
cur.execute(query_blog_by_title, ("2018-2019 Travel",))
for blog in cur.fetchall():
    print(blog[0], blog[1])

```

### SQL事务和ACID属性
SQLite的隔离级别：
- isolation_level=None : 默认设置，自动提交模式，这种模式下，每个SQL语句执行后直接提交到数据库，会破坏原子性。
- isolation_level='DEFERRED' : 这种模式下，事务中锁的添加越晚越好。BEGIN语句并没有立即获得锁，对于其他读操作可以获得共享锁，
写操作将获得保留的锁。可最大化并发，但多进程中可能发生死锁。
- isolation_level='EXCLUSIVE' : 这种模式中，事务中的BEGIN语句会获得一个锁，阻止其他操作访问。

```python
import sqlite3
db = sqlite3.connect('blog.db', isolation_level='DEFERRED')
# 常规事务操作
try:
    db.execute('BEGIN')
    db.execute("some statement")
    db.execute("another statement")
    db.commit()
except Exception as e:
    db.rollback()
    raise e

# 上下文形式的事务操作
with db:
    db.execute("some statement")
    db.execute("another statement")

```

### 纯SQL中实现类似于类的处理方式

```python
from collections import defaultdict
class Blog:
    def __init__(self, title, *posts):
        self.title = title
        self.entries = list(posts)
    def append(self, post):
        self.entries.append(post)
    def by_tag(self):
        tag_index = defaultdict(list)
        for post in self.entries:
            for tag in post.tags:
                tag_index[tag].append(post)
        return tag_index
    def as_dict(self):
        return dict(
            title=self.title,
            underline = "="*len(self.title),
            entries = [p.as_dict() for p in self.entries],
        )

```
用SQL的形式实现by_tag()的数据提取功能：
```python
query_by_tag = """
SELECT TAG.PHRASE, POST.TITLE, POST.ID 
FROM TAG JOIN ASSOC_POST_TAG ON TAG.ID = ASSOC_POST_TAG.TAG_ID 
JOIN POST ON POST.ID = ASSOC_POST_TAG.POST_ID 
JOIN BLOG ON POST.BLOG_ID = BLOG.ID
WHERE BLOG.TITLE=?
"""
tag_index = defaultdict(list)
for tag, post_title, post_id in database.execute(query_by_tag,
("2018-2019 Travel",)):
    tag_index[tag].append((post_title, post_id))
print(tag_index)
```

### 扩展SQLite的类型支持
通过注册适配器和转换器，来获得类型的支持
```python
import decimal
import sqlite3

def adapt_currency(value):
    return str(value)
sqlite3.register_adapter(decimal.Decimal, adapt_currency)

def convert_currency(bytes):
    return decimal.Decimal(bytes.decode())
sqlite3.register_converter("DECIMAL", convert_currency)

# 现在可以使用新的数值类型来定义表
decimal_ddl = """
CREATE TABLE BUDGET(
    year INTEGER,
    month INTEGER,
    category TEXT,
    amount DECIMAL
)
"""
# 在建立数据库连接时通过设置detect_types=sqlite3.PARSE_DECLTYPES来通知SQLite新增的类型
db = sqlite3.connect('blog.db', detect_types=sqlite3.PARSE_DECLTYPES)
db.execute(decimal_ddl)

insert_budget = """
INSERT INTO BUDGET(year, month, category, amount) VALUES(:year, 
:month, :category, :amount)
"""
db.execute(insert_budget, dict(
    year=2019, month=8, category="fuel", amount=decimal.Decimal('256.78')
))

query_budget = """
SELECT * FROM BUDGET
"""
for row in db.execute(query_budget):
    print(row)
# (2019, 8, 'fuel', Decimal('256.78'))
```

### 手动完成python对象到数据库行的映射
```python
import sqlite3
from collections import defaultdict

class TooManyValues(Exception):
    pass
    
class Blog:
    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', None)
        self.title = kwargs.pop('title', None)
        if kwargs: raise TooManyValues(kwargs)  # 只允许相关的值传入
        # self.entries = list()
        
    @property
    def entries(self):
        """将Access对象注入到本类实例中，调用Access方法来实现容器的数据"""
        return self._access.post_iter(self)
        
    def append(self, post):
        self.entries.append(post)
    def by_tag(self):
        tag_index = defaultdict(list)
        for post in self.entries:
            for tag in post.tags:
                tag_index[tag].append(post)
        return tag_index
    def as_dict(self):
        return dict(
            title=self.title,
            underline = "="*len(self.title),
            entries = [p.as_dict() for p in self.entries],
        )


class Post:
    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', None)
        self.date = kwargs.pop('date', None)
        self.title = kwargs.pop('title', None)
        self.rst_text = kwargs.pop('rst_text', None)
        self.tags = list()
        if kwargs: raise TooManyValues(kwargs)  # 只允许相关的值传入
    def append(self, tag):
        self.tags.append(tag)
    def as_dict(self):
        return dict(
            date=str(self.date),
            title=self.title,
            underline="-" * len(self.title),
            rst_text=self.rst_text,
            tag_text=" ".join(self.tags),
        )
# 设计一个访问层
class Access:
    get_last_id = """SELECT last_insert_rowid()"""
    
    def open(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.row_factory = sqlite3.Row  # Row类允许通过数字索引和列名来访问
    def get_blog(self, id):
        query_blog = """SELECT * FROM BLOG WHERE ID=?"""
        row = self.db.execute(query_blog, (id,)).fetchone()
        blog = Blog(id=row['ID'], title=row['TITLE'])
        blog._access = self  # 把访问层实例存入对象中，方便各自调用
        return blog
    def add_blog(self, title):
        insert_blog="""INSERT INTO BLOG(TITLE) VALUES(:title)"""
        self.db.execute(insert_blog, dict(title=title))
        row = self.db.execute(get_last_id).fetchone()
        blog = Blog(title=title)
        blog.id = row[0]
        blog._access = self  # 把访问层实例存入对象中，方便各自调用
        return blog
        
    def get_post(self, id):
        query_post = """SELECT * FROM POST WHERE ID=?"""
        row = self.db.execute(query_post, (id,)).fetchone()
        post = Post(
            id=row['ID'],
            title=row['TITLE'],
            date=row['DATE'],
            irst_text=row['RST_TEXT'],
        )
        query_tags = """
        SELECT TAG.* FROM TAG 
        JOIN ASSOC_POST_TAG ON TAG.ID = ASSOC_POST_TAG.TAG_ID 
        WHERE ASSOC_POST_TAG.POST_ID=?
        """
        results = self.db.execute(query_tags, (id,))
        for id, tag in results:
            post.append(tag)
        post._access = self  # 把访问层实例存入对象中，方便各自调用
        return post
    def add_post(self, blog, title, date, rst_text, tags):
        insert_post = """
        INSERT INTO POST(TITLE, DATE, RST_TEXT, BLOG_ID) 
        VALUES(:title, :date, :rst_text, :blog_id)
        """
        query_tag = """
        SELECT * FROM TAG WHERE PHRASE=?
        """
        insert_tag = """
        INSERT INTO TAG(PHRASE) VALUES(?)
        """
        insert_association = """
        INSERT INTO ASSOC_POST_TAG(POST_ID, TAG_ID) VALUES(:post_id, :tag_id)
        """
        post_data = dict(
            title=title,
            date=date,
            rst_text=rst_text,
            blog_id=blog.id
        )
        post = Post(**post_data)
        with self.db:
            self.db.execute(insert_post, post_data)
            row = self.db.execute(get_last_id).fetchone()
            post.id = row[0]
            for tag in post.tags:
                tag_row = self.db.execute(query_tag, (tag,)).fetchone()
                if tag_row is not None:
                    tag_id = tag_row['ID']
                else:
                    self.db.execute(insert_tag, (tag, ))
                    row = self.db.execute(get_last_id).fetchone()
                    tag_id = row[0]
                self.db.execute(insert_association, dict(tag_id=tag_id, post_id=post.id))
        post._access = self  # 把访问层实例存入对象中，方便各自调用
        return post
    def blog_iter(self):
        query = """SELECT * FROM BLOG"""
        results = self.db.execute(query)
        for row in results:
            blog = Blog(id=row['ID'], title=row['TITLE'])
            blog._access = self  # 把访问层实例存入对象中，方便各自调用
            yield blog
    def post_iter(self, blog):
        query = """SELECT ID FROM POST WHERE BLOG_ID=?"""
        results = self.db.execute(query, (blog.id))
        for row in results:
            yield self.get_post(row['ID'])
```
### 使用索引提高性能
<code>CREATE INDEX IX_BLOG_TITLE ON BLOG(TITLE);</code>

### 添加ORM层

当使用ORM时，需要在根本上改变设计的方法并且实现持久化类。类定义将会包括3种不同层次的含义。
- 类可以是一个python类，用于创建python对象。方法函数由这些对象来使用。
- 类也可以用于描述SQL表，可被ORM用于创建SQL DDL语句，完成数据库结构的新建和维护。
- 类也定义了SQL表和python类之间的映射。他将完成将python操作转换为SQL DML并基于SQL查询创建python对象。

大多数ORM的设计使得我们需要使用修饰符来正式地定义类中的属性。
以SQLAlchemy为例，需要定义性的基类，这个基类为应用的类定义提供了元类。
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Table
from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, Enum,
    Float, Integer, Interval, LargeBinary, Numeric, PickleType,
    SmallInteger, String, Text, Time, Unicode, UnicodeText, ForeignKey
)
from sqlalchemy.orm import relationship, backref

Base = declarative_base()  # 创建元类

# 这个关联表只在SQL技术上需要，因此不必添加python类的映射。
assoc_post_tag = Table("ASSOC_POST_TAG", Base.metadata,
    Column('POST_ID', Integer, ForeignKey('POST.id')),
    Column('TAG_ID', Integer, ForeignKey('TAG.id'))
)


class Blog(Base):
    __tablename__ = "BLOG"
    id = Column(Integer, primary_key=True)
    title = Column(String)  # SQLite不需要加长度上限
    def as_dict(self):
        return dict(
            title=self.title,
            underline="="*len(self.title),
            entries=[e.as_dict() for e in self.entries]
        )

class Post(Base):
    __tablename__ = "POST"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    date = Column(DateTime)
    rst_text = Column(UnicodeText)
    blog_id = Column(Integer, ForeignKey('BLOG.id'))
    blog = relationship('Blog', backref='entries')  # backref：向后引用
    tags = relationship("Tag", secondary=assoc_post_tag, backref="posts")  # 通过关联表来向后引用
    def as_dict(self):
        return dict(
            title=self.title,
            underline='_'*len(self.title),
            date=self.date,
            rst_text=self.rst_text,
            tags=[t.phrase for t in self.tags]
        )

class Tag(Base):
    __tablename__ = "TAG"
    id = Column(Integer, primary_key=True)
    phrase = Column(String, unique=True)
    


# 创建数据库引擎
from sqlalchemy import create_engine
engine = create_engine('sqlite:///./blog2.db', echo=True)  # echo=True生成的SQL语句会打印输出
Base.metadata.create_all(engine)
"""
2019-08-27 15:39:39,078 INFO sqlalchemy.engine.base.Engine SELECT CAST('test plain returns' AS VARCHAR(60)) AS anon_1
2019-08-27 15:39:39,078 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,079 INFO sqlalchemy.engine.base.Engine SELECT CAST('test unicode returns' AS VARCHAR(60)) AS anon_1
2019-08-27 15:39:39,079 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,079 INFO sqlalchemy.engine.base.Engine PRAGMA main.table_info("BLOG")
2019-08-27 15:39:39,079 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,080 INFO sqlalchemy.engine.base.Engine PRAGMA temp.table_info("BLOG")
2019-08-27 15:39:39,080 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,080 INFO sqlalchemy.engine.base.Engine PRAGMA main.table_info("ASSOC_POST_TAG")
2019-08-27 15:39:39,080 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine PRAGMA temp.table_info("ASSOC_POST_TAG")
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine PRAGMA main.table_info("POST")
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine PRAGMA temp.table_info("POST")
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine PRAGMA main.table_info("TAG")
2019-08-27 15:39:39,081 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,082 INFO sqlalchemy.engine.base.Engine PRAGMA temp.table_info("TAG")
2019-08-27 15:39:39,082 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,083 INFO sqlalchemy.engine.base.Engine 
CREATE TABLE "BLOG" (
	id INTEGER NOT NULL, 
	title VARCHAR, 
	PRIMARY KEY (id)
)
2019-08-27 15:39:39,083 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,085 INFO sqlalchemy.engine.base.Engine COMMIT
2019-08-27 15:39:39,085 INFO sqlalchemy.engine.base.Engine 
CREATE TABLE "TAG" (
	id INTEGER NOT NULL, 
	phrase VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (phrase)
)
2019-08-27 15:39:39,085 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,087 INFO sqlalchemy.engine.base.Engine COMMIT
2019-08-27 15:39:39,087 INFO sqlalchemy.engine.base.Engine 
CREATE TABLE "POST" (
	id INTEGER NOT NULL, 
	title VARCHAR, 
	date DATETIME, 
	rst_text TEXT, 
	blog_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(blog_id) REFERENCES "BLOG" (id)
)
2019-08-27 15:39:39,087 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,088 INFO sqlalchemy.engine.base.Engine COMMIT
2019-08-27 15:39:39,088 INFO sqlalchemy.engine.base.Engine 
CREATE TABLE "ASSOC_POST_TAG" (
	"POST_ID" INTEGER, 
	"TAG_ID" INTEGER, 
	FOREIGN KEY("POST_ID") REFERENCES "POST" (id), 
	FOREIGN KEY("TAG_ID") REFERENCES "TAG" (id)
)
2019-08-27 15:39:39,088 INFO sqlalchemy.engine.base.Engine ()
2019-08-27 15:39:39,089 INFO sqlalchemy.engine.base.Engine COMMIT
"""

# 使用ORM层操作对象
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine) # 绑定到引擎
session = Session() # 创建session对象

# blog的添加
blog = Blog(title="Travel 2019")
session.add(blog)   # 加载到会话中

# tag先查询，不存在则添加
tags = []
for phrase in "#RedRanger", "#Whitby42", "#ICW":
    try:
        tag = session.query(Tag).filter(Tag.phrase == phrase).one()
    except sqlalchemy.orm.exc.NoResultFound:
        tag = Tag(phrase=phrase)
        session.add(tag)
    tags.append(tag)

# 创建Post对象
p2 = Post(
    date=datetime.datetime(2019,8,27,16,17),
    title="Hard Aground",
    rst_text="""Some embarrassing revelation. Including...""",
    blog=blog,
    tags=tags
)
session.add(p2)
blog.posts=[p2]

# 未提交之前，所有操作都在session的缓存中，没有实际入库
session.commit() # 提交会话

# 通过指定标签字符串查询文章对象(通过join实现连接查询)
for post in session.query(Post).join(assoc_post_tag).join(Tag).filter(
    Tag.phrase == "#Whitby42"):
    print(post.blog.title, post.date, post.title, 
    [t.phrase for t in post.tags])
# 实际底层的sql：
"""
SELECT 
"POST".id AS "POST_id", 
"POST".title AS "POST_title", 
"POST".date AS "POST_date", 
"POST".rst_text AS "POST_rst_text", 
"POST".blog_id AS "POST_blog_id" 
FROM "POST" 
JOIN "ASSOC_POST_TAG" ON "POST".id = "ASSOC_POST_TAG"."POST_ID" 
JOIN "TAG" ON "TAG".id = "ASSOC_POST_TAG"."TAG_ID" 
WHERE "TAG".phrase = ?
"""


# 是否需要创建索引，进行相应的测试是必要的。有时候需要权衡性能和负载
# 创建索引如下所示：
class Post(Base):
    __tablename__ = "POST"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    date = Column(DateTime, index=True)
    # 为blog_id添加索引，可能会加速Blog和Post表中的行的连接操作
    blog_id = Column(Integer, ForeignKey('BLOG.id'), index=True)


```