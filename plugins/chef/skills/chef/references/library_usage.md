# recipe-scrapers 库用法

GitHub: https://github.com/hhursev/recipe-scrapers  
安装：`pip install recipe-scrapers`（或跑 `scripts/setup.py --yes`）

## 基本模式

```python
from recipe_scrapers import scrape_me

s = scrape_me("https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/")
print(s.title())
print(s.total_time())           # 分钟
print(s.yields())               # "8 servings"
print(s.ingredients())          # list[str]
print(s.instructions())         # 全部步骤合成一个字符串
print(s.instructions_list())    # list[str]（推荐）
print(s.image())
print(s.host())
print(s.nutrients())            # dict（部分站点支持）
```

## 完整可调用方法

```
title(), host(), author(),
canonical_url(), image(),
total_time(), cook_time(), prep_time(), yields(),
ingredients(), ingredient_groups(),
instructions(), instructions_list(),
nutrients(), ratings(), ratings_count(),
cuisine(), category(), description(), language(),
site_name(), keywords()
```

不是每个站点都实现全部；调用时用 try/except 包起来最安全。本 skill 的 `scripts/scrape_web.py` 已经这样写。

## wild_mode

列表里没有的站点，尝试用 wild_mode 推断（靠 JSON-LD Schema.org 的 Recipe 类型）：

```python
s = scrape_me("https://new-unseen-site.com/recipe/abc", wild_mode=True)
# 成功率取决于站点是否内嵌了 <script type="application/ld+json"> 的 Recipe schema
```

很多现代英文食谱站都有 JSON-LD，wild_mode 命中率意外地高。

## 支持的 631 站点（节选）

| 类别 | 站点 |
|---|---|
| 北美主流 | allrecipes.com, foodnetwork.com, tasty.co, simplyrecipes.com, food52.com, seriouseats.com, bonappetit.com, epicurious.com, eatingwell.com, thekitchn.com |
| 英国 | bbcgoodfood.com, bbc.co.uk, delish.com, jamieoliver.com |
| 健康 | ambitiouskitchen.com, minimalistbaker.com, cookieandkate.com |
| 烘焙 | kingarthurbaking.com, bettycrocker.com, joyofbaking.com |
| 世界美食 | seriouseats.com (亚洲专栏), maangchi.com (韩), justonecookbook.com (日) |

完整列表：`python -c "from recipe_scrapers import SCRAPERS; print(list(SCRAPERS.keys()))"`

## 在本 skill 的兜底链

`scripts/scrape_web.py` 按这个顺序：

1. `scrape_me(url)` — 精确站点匹配
2. `scrape_me(url, wild_mode=True)` — JSON-LD 推断
3. 手工 JSON-LD 解析（`parse_jsonld`） — 连库都失败时最后的回退
4. 抛错提示"无法解析"

## 何时用 recipe-scrapers vs 手写选择器

| 场景 | 用什么 |
|---|---|
| URL 在支持列表 | recipe-scrapers |
| 大多数英文食谱站 | recipe-scrapers + wild_mode |
| 下厨房、豆果、美食杰、香哈、新食谱 | 手写（中文站基本不在库里） |
| 站点结构变了 | 查 `sources/{id}.json` 更新 `scrape_rules`，或向 recipe-scrapers 上游提 PR |
