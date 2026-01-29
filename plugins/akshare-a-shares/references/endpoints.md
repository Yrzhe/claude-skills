# A股接口清单（基于本地 akshare）

仅列最常用接口，参数以本地源码为准；本表用于选型参考。

注意：
- EM 接口股票代码通常为纯数字（如 600519）。
- Sina 接口部分函数要求带交易所前缀（sh600519 / sz000001）。
- 日期：日线/周线/月线多为 `YYYYMMDD`；分钟多为 `YYYY-MM-DD HH:MM:SS`。
- 复权：`adjust` 取值 `{ "": 不复权, "qfq": 前复权, "hfq": 后复权 }`。

## 行情总览（实时）

- EM: `akshare.stock_feature.stock_hist_em.stock_zh_a_spot_em() -> pd.DataFrame`
  - 返回字段：代码、名称、最新价、涨跌幅、成交额等

- Sina: `akshare.stock.stock_zh_a_sina.stock_zh_a_spot() -> pd.DataFrame`
  - 注意：高频调用可能被限制

## 历史K线（日/周/月）

- EM: `akshare.stock_feature.stock_hist_em.stock_zh_a_hist(symbol: str, period: str = 'daily', start_date: str, end_date: str, adjust: str = '') -> pd.DataFrame`
  - `period`: `daily` | `weekly` | `monthly`
  - `symbol`: 纯数字代码（例 600519）
  - 返回列：日期、开盘、收盘、最高、最低、成交量、成交额、涨跌幅等

- Sina: `akshare.stock.stock_zh_a_sina.stock_zh_a_daily(symbol: str, start_date: str, end_date: str, adjust: str = '') -> pd.DataFrame`
  - `symbol`: `sh600519` / `sz000001`
  - `adjust`: `'' | 'qfq' | 'hfq' | 'qfq-factor' | 'hfq-factor'`

## 分钟分时（1/5/15/30/60）

- EM: `akshare.stock_feature.stock_hist_em.stock_zh_a_hist_min_em(symbol: str, start_date: str, end_date: str, period: str = '5', adjust: str = '') -> pd.DataFrame`
  - `symbol`: 纯数字代码（例 000001）
  - `period`: `1|5|15|30|60`

- Sina: `akshare.stock.stock_zh_a_sina.stock_zh_a_minute(symbol: str, period: str = '1', adjust: str = '') -> pd.DataFrame`
  - `symbol`: `sh600519` / `sz000001`

## 特色数据：股东户数

- 批量/季度末：`akshare.stock_feature.stock_gdhs.stock_zh_a_gdhs(symbol: str = '最新' | 'YYYYMMDD') -> pd.DataFrame`

- 详情：`akshare.stock_feature.stock_gdhs.stock_zh_a_gdhs_detail_em(symbol: str = '000001') -> pd.DataFrame`

## 公告披露（巨潮资讯）

- 公告检索：`akshare.stock_feature.stock_disclosure_cninfo.stock_zh_a_disclosure_report_cninfo(symbol: str, market: str = '沪深京', keyword: str = '', category: str = '', start_date: str, end_date: str) -> pd.DataFrame`
  - `category` 示例：年报、半年报、一季报、三季报、业绩预告、权益分派等

- 预约披露/调研：`akshare.stock_feature.stock_disclosure_cninfo.stock_zh_a_disclosure_relation_cninfo(symbol: str, market: str = '沪深京', start_date: str, end_date: str) -> pd.DataFrame`

## 代码前缀与自动补全建议

- 若来源为 EM：传入纯数字代码。若用户输入了 `sh/sz` 前缀，可自动去除。
- 若来源为 Sina：如用户传入纯数字代码，根据首位自动补前缀：
  - 以 `6` 开头 → `sh`；以 `0/3` 开头 → `sz`

