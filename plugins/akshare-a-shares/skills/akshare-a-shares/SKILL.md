---
name: akshare-a-shares
description: 针对中国A股的行情与数据查询（基于本地 akshare 源代码与API映射）。当用户请求获取A股实时行情、历史K线（日/周/月）、分钟级分时（1/5/15/30/60）、复权数据（前复权/后复权）、股东户数（含详情）、以及巨潮资讯公告披露结果时使用本Skill。默认优先使用东方财富(EM)接口；如用户指定新浪(Sina)来源或需要特定接口，则按映射调用对应函数。可使用内置脚本输出CSV/JSON，或内联Python调用。
---

# A股数据查询（akshare）

本Skill指导如何基于本地 akshare 源码目录的数据接口完成 A 股数据查询，并提供一个可直接运行的脚本以便快速拉取数据。

目录约定：本地 akshare 源位于 `Recents/akshare`（相对当前工作目录）。如不一致，请在执行脚本前修改脚本内 `AK_PATH`。

## 快速开始

- 方式一（推荐）脚本直取：使用 `scripts/akshare_fetch.py` 拉取数据，支持 CSV 或 JSON 输出。
  - 示例见 `references/examples.md`
- 方式二 内联Python：在任务中按“接口映射”选定函数与参数，直接编写最小可运行代码。

## 核心流程

1) 识别用户意图与来源
   - 行情总览（实时行情）、历史K线（日/周/月）、分钟分时、复权、股东户数、公告检索等
   - 来源优先级：未指定则默认 EastMoney(EM)；用户指明“新浪”则用 Sina 接口
2) 选择接口与参数
   - 查 `references/endpoints.md` 的“意图→接口”映射与参数说明
3) 拉取与校验
   - 使用脚本或内联Python调用；如返回为空，检查代码格式（是否需交易所前缀、日期格式、是否退市等）
4) 返回结果
   - 表格/CSV/JSON；必要时附带参数回显与数据来源

## 接口映射总览（最常用）

- 实时全市场 A 股：`stock_feature.stock_hist_em.stock_zh_a_spot_em()`
- 历史K线（日/周/月，支持复权）：`stock_feature.stock_hist_em.stock_zh_a_hist(symbol, period, start_date, end_date, adjust)`
- 分钟分时（1/5/15/30/60，支持复权）：`stock_feature.stock_hist_em.stock_zh_a_hist_min_em(symbol, start_date, end_date, period, adjust)`
- 股东户数（批量/季度末）：`stock_feature.stock_gdhs.stock_zh_a_gdhs(symbol)`；详情：`stock_feature.stock_gdhs.stock_zh_a_gdhs_detail_em(symbol)`
- 公告披露（巨潮资讯）：`stock_feature.stock_disclosure_cninfo.stock_zh_a_disclosure_report_cninfo(...)`、`stock_zh_a_disclosure_relation_cninfo(...)`
- 新浪来源（如指定）：实时报价 `stock.stock_zh_a_sina.stock_zh_a_spot()`、日线/复权 `stock.stock_zh_a_sina.stock_zh_a_daily(...)`、分钟线 `stock.stock_zh_a_sina.stock_zh_a_minute(...)`

详细参数、示例与注意事项见 `references/endpoints.md` 与 `references/examples.md`。

## 使用内置脚本

脚本路径：`scripts/akshare_fetch.py`

- 基本用法（CSV）：
  - `python3 scripts/akshare_fetch.py spot --source em --format csv`
  - `python3 scripts/akshare_fetch.py hist --symbol 600519 --period daily --start 20200101 --end 20251231 --adjust qfq --format csv`
  - 更多示例见 `references/examples.md`

脚本特性：
- 自动将 `Recents/akshare` 加入 `sys.path`，直接导入本地 akshare 源
- 默认输出到标准输出；`--format json` 输出JSON
- 依赖：`python3`、`pandas`、`requests`（Sina 接口还需 `py_mini_racer`）
- 若依赖缺失，会给出友好错误提示

## 符号与日期规范

- `EM` 接口通常使用纯数字代码：沪市以 `6` 开头（如 `600519`），深市以 `0/3` 开头（如 `000001`）
- `Sina` 接口部分函数使用带交易所前缀的代码（如 `sh600519`、`sz000001`）
- 日期：`YYYYMMDD`（日/周/月K）；分钟分时使用 `YYYY-MM-DD HH:MM:SS`
- 复权：`adjust` 取值 `{ "": 不复权, "qfq": 前复权, "hfq": 后复权 }`

## 仅在需要时阅读的参考

- `references/endpoints.md`：接口清单、参数与返回字段概述
- `references/examples.md`：常见请求的可直接运行示例及脚本命令

请按需加载参考文件，避免无关内容占用上下文。

