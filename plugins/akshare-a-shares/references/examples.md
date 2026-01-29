# 使用示例

以下示例默认本地 akshare 源位于 `Recents/akshare`。如路径不同，请修改脚本中的 `AK_PATH`。

## 脚本方式

- 实时行情（EM）：
  - `python3 scripts/akshare_fetch.py spot --source em --format csv`

- 全市场实时（Sina）：
  - `python3 scripts/akshare_fetch.py spot --source sina --format csv`

- 历史日K（EM，前复权）：
  - `python3 scripts/akshare_fetch.py hist --symbol 600519 --period daily --start 20150101 --end 20251231 --adjust qfq --format csv`

- 分钟分时（EM，5分钟，不复权）：
  - `python3 scripts/akshare_fetch.py min --symbol 000001 --period 5 --start "2024-12-01 09:30:00" --end "2024-12-02 15:00:00" --format csv`

- 股东户数（最近一期）：
  - `python3 scripts/akshare_fetch.py gdhs --when 最新 --format csv`

- 股东户数详情（单只）：
  - `python3 scripts/akshare_fetch.py gdhs-detail --symbol 000001 --format csv`

- 公告披露（巨潮资讯）：
  - `python3 scripts/akshare_fetch.py cninfo --symbol 000001 --market 沪深京 --category 年报 --start 20230101 --end 20241231 --format csv`

## 内联Python（片段）

```python
import sys
from pathlib import Path

AK_PATH = Path.cwd() / "Recents" / "akshare"
if str(AK_PATH) not in sys.path:
    sys.path.insert(0, str(AK_PATH))

from akshare.stock_feature.stock_hist_em import stock_zh_a_hist

df = stock_zh_a_hist(symbol="600519", period="daily", start_date="20150101", end_date="20251231", adjust="qfq")
print(df.head())
```

