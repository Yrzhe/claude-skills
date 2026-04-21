# 中文食谱站抓取模式

国内站基本不在 `recipe-scrapers` 库里，只能手写。以下是常见坑和选择器模板。实际选择器会随站点改版变化——用前先打开一个详情页，用 DevTools 核对一遍。

## 通用坑

1. **User-Agent**：必须伪装成浏览器。用 `Mozilla/5.0 ...`。
2. **Referer**：部分站要求 Referer 与站同域。
3. **Cookie**：某些详情页（尤其美食杰深处分类）需要登录 cookie。建议实现到"如果 HTML < 2KB 就记下来回头补 cookie"的启发式。
4. **频率**：3s 间隔比较稳；批量 1000 道用 tmux 跑。
5. **编码**：全部 utf-8，正常不会乱码。
6. **图片懒加载**：常用 `data-src` / `data-original` 属性替代 `src`。

## 下厨房 xiachufang.com

详情页 URL 形式：`https://www.xiachufang.com/recipe/{id}/`

```
标题:      h1.page-title
食材表:    div.ings tr
  名字:    td.name a (或纯文本)
  用量:    td.unit
步骤:      div.steps p.text
步骤图:    div.steps img@src
作者:      div.author a
封面图:    div.cover img@src
简介:      div.desc
份量:      div.stats .number
```

列表页（`/explore/`）项：

```
每项:      li.recipe
标题链接:  p.name a@href
```

## 豆果美食 douguo.com

**建议用移动站** `m.douguo.com`，结构更简单：

```
详情 URL:  https://m.douguo.com/cookbook/{id}.html 或 https://www.douguo.com/cookbook/{id}.html
标题:      h1
食材:      .ct-item (PC) / .ct-item (m)
  名字:    span.name
  用量:    span.amount
步骤:      .step-txt
步骤图:    .step-pic img@src
```

## 美食杰 meishij.net

```
详情 URL:  https://www.meishij.net/zuofa/{slug}.html
标题:      .recipe_title h1
食材:      .yl li
  名字:    .yl li .c1 (或 a)
  用量:    .yl li .c2 (或 span)
步骤:      .method_detail 或 .recipeStep_word
步骤图:    .recipeStep img@src
烹饪时间:  .recipe_de_tags .recipe_de_cook
份量:      .recipe_de_tags .recipe_de_people
菜系:      .recipeCategory_sub_R .recipeCategory_sub_name
```

**菜系分类 URL 速查**：

| 菜系 | URL |
|---|---|
| 川菜 | `/chufang/diy/chuancai/` |
| 粤菜 | `/chufang/diy/yuecai/` |
| 鲁菜 | `/chufang/diy/lucai/` |
| 苏菜 | `/chufang/diy/sucai/` |
| 浙菜 | `/chufang/diy/zhecai/` |
| 闽菜 | `/chufang/diy/mincai/` |
| 湘菜 | `/chufang/diy/xiangcai/` |
| 徽菜 | `/chufang/diy/huicai/` |
| 家常菜 | `/chufang/diy/jiangchangcaipu/` |

## 香哈 xiangha.com

```
详情 URL:  https://www.xiangha.com/caipu/{id}.html
标题:      h1.recipe-title
食材:      .recipe-materials li
  名字:    .recipe-materials li .name
  用量:    .recipe-materials li .amount
步骤:      .recipe-steps .step-text
```

## 爱料理 iCook icook.tw

繁体中文。heading-anchor 模板（教科书级），解析友好度 5/5。

```
详情 URL:  https://icook.tw/recipes/{id}
标题:      h1
描述:      ## 描述 → 紧随 p
份量:      ## 份量
时间:      ## 時間
食材:      ## 食材
步骤:      ## 步驟
热量:      ## 熱量  (部分 VIP 页面不完整)
作者:      h1 后的 "by {name}" 或 author meta
图片域:    imgproxy.icook.network
```

**严禁**：`/recipes/*.json` 被 robots Disallow——即使端点可读也不要用。条款禁止"规避 robot exclusion headers"。

## Cookpad 台湾站 cookpad.com/tw

```
详情 URL:  https://cookpad.com/tw/食譜/{id}  （URL 中文需 percent-encode）
标题:      h1
食材:      ## 預備食材
步骤:      ## 料理步驟
```

Cookpad 在 cookie 里显式设 Perimeter X（_px*）——有 bot 管理。建议 3-6s 抖动 + 维持 session cookie。

## 美食天下 meishichina.com（注意：不是 meishij.net）

优先移动版：`m.meishichina.com/recipe/{id}/`

```
标题:       h1
描述:       p (第一段)
元信息:     难度/技法/口味/耗时  (内联标签)
食材分组:   ## 食材明细
            ### 主料 / ### 辅料 / ### 调料  （分组保存）
步骤:       做法步骤 1..n
```

版权声明禁止镜像；站外 API/RSS 引用视作接受条款。保存时建议分组保留 `group: 主料/辅料/调料`。

## Food Network（英文）

```
详情 URL:  https://www.foodnetwork.com/recipes/{author-slug}/{recipe-slug}-{id}
标题:      h1
难度:      Level
时间:      Total/Prep/Cook
份量:      Yield
营养:      Nutrition Analysis
食材:      ## Ingredients
步骤:      ## Directions
分类:      Categories
```

robots 封禁多个 AI bot（GPTBot/ClaudeBot/PerplexityBot 等）。Terms 明文禁 scrape——个人非商用抓取请低并发、crawl-delay ≥5s、避开 print/embed/ratings/search 路径。

## King Arthur Baking（英文，烘焙）

```
详情 URL:  https://www.kingarthurbaking.com/recipes/{slug}-recipe
标题:      h1
时间:      Prep/Bake/Total
产量:      Yield
营养:      Nutrition Information
食材:      Ingredients
步骤:      Instructions
```

Terms 明确禁 bot/crawler/scraper——个人单次查阅 OK，不要批量/镜像。

## 新食谱 xinshipu.com

```
详情 URL:  https://www.xinshipu.com/zuofa/{id}
标题:      h1
食材:      .ings li
步骤:      .steps li .text
封面:      .recipe-cover img@src
```

## 通用抓取骨架

```python
from bs4 import BeautifulSoup
import requests, time, re

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) chef-skill/1.0"

def get_soup(url):
    r = requests.get(url, headers={"User-Agent": UA,
                                   "Referer": url.rsplit('/', 3)[0] + '/'},
                     timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")

def extract_xiachufang(url):
    s = get_soup(url)
    title = s.select_one("h1.page-title").get_text(strip=True)
    ings = []
    for tr in s.select("div.ings tr"):
        name = tr.select_one("td.name")
        unit = tr.select_one("td.unit")
        ings.append({
            "name": name.get_text(strip=True) if name else "",
            "amount": unit.get_text(strip=True) if unit else "",
        })
    steps = [p.get_text(strip=True) for p in s.select("div.steps p.text")]
    return {"title": title, "ingredients": ings, "steps": steps}
```

## 反爬应对清单

- 403 / 429 → 降速 → 加 Referer → 换 UA → 加 Cookie → 换 IP（个人用一般不至于）
- 页面 < 1KB 且无错码 → 可能是懒加载，得跑 Playwright（参考 `mcp__playwright__*` 工具或本仓库 `.playwright-mcp/`）
- JSON-LD 存在 → 优先用，比 DOM 稳定
- 返回内容被 JS 渲染 → Playwright 或去掉 `?spm=...` 之类的跟踪参数看有没有静态版
