import gzip
import csv
import re

# 将Apache HTTP 服务器日志文件解析成通用日志格式，并保存为CSV格式
format_pat = re.compile(
    r"([\d\.]+)\s+"     # digits and .'s:host
    r"(\S+)\s+"         # non-space: logname
    r"(\S+)\s+"         # non-space: user
    r"\[(.+?)\]\s+"     # Everything in []:time
    r'"(.+?)"\s+'       # Everything in "": request
    r"(\d+)\s+"         # digits: status
    r"(\S+)\s+"         # non-space: bytes
    r'"(.*?)"\s+'       # Everything in "": referrer
    r'"(.*?)"\s*'       # Everything in "": user agent
)
path = ""
with open("subset.csv", "w") as target:
    writer = csv.writer(target)
    with gzip.open(path) as source:
        line_iter = (b.decode() for b in source)
        match_iter = (format_pat.match(line) for line in line_iter)
        writer.writerows((m.groups() for m in match_iter if m is not None))


from functools import total_ordering
