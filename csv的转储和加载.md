### 将简单的序列转储为CSV
```python
from collections import namedtuple
GameStat = namedtuple("GameStat", "player,bet,rounds,final")

def gamestat_iter(player, betting, limit=100):
    for sample in range(30):
        b = Blackjack(player(), betting())
        b.until_broke_or_rounds(limit)
        yield GameStat(player.__name__, betting.__name__, b.rounds, b.betting.stake)
        
        
import csv

with open("blackjack.stats", "w", newline="") as target:
    writer = csv.DictWriter(target, GameStat._fields)
    writer.writeheader()
    # 逐行写入
    # for gamestat in gamestat_iter(Player_Strategy_1, Martingale_Bet):
    #     writer.writerow(gamestat._asdict())
    
    # 批量写入
    data = gamestat_iter(Player_Strategy_1, Martingale_Bet)
    writer.writerows(g._asdict() for g in data)

```

### 从CSV文件中加载简单的序列
```python
import csv

def gamestat_iter(iterator):
    for row in iterator:
        yield GameStat(row['player'], row['bet'], 
                       int(row['rounds']), int(row['final']))
                       
with open("blackjack.stats", "r", newline="") as source:
    reader = csv.DictReader(source)
    assert set(reader.fieldnames) == set(GameStat._fields)  # 检查列名
    for gs in gamestat_iter(reader):
        print(gs)

```