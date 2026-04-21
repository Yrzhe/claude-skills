# data/recipes/*.md — Frontmatter 规范

所有本地缓存的食谱都用这个结构。`scripts/_lib.py` 的 `write_recipe()` 就是按这个发出的 YAML。

## 完整模板

```yaml
---
# 基本信息（必填）
title: 红烧肉
title_en: Braised Pork Belly          # 可选
cuisine: 中餐家常                      # 自由字符串 或 null
category: 主菜                         # 主菜/汤/甜点/早餐/前菜/主食
language: zh                           # zh / en / mix

# 来源（强制：至少 site）
source:
  site: xiachufang                     # 对应 sources/xiachufang.json 的 id，或 food.com / themealdb 等
  url: https://www.xiachufang.com/recipe/12345/
  external_id: "12345"                 # 站内 id（字符串）
  author: 某厨                          # 可选
  scraped_at: 2026-04-16               # YYYY-MM-DD
  dataset: kaggle-food_com             # 如果来自数据集

# 时间 / 份量（可选）
time:
  prep_min: 15
  cook_min: 60
  total_min: 75
servings: 4
difficulty: medium                     # easy / medium / hard

# 分类标签
tags:
  - 猪肉
  - 红烧
  - 下饭
  - 家常

# 食材（必填，至少一个）
ingredients:
  - name: 五花肉
    amount: 500
    unit: g
    group: 主料                         # 可选分组：主料/调料/配菜
  - name: 冰糖
    amount: 30
    unit: g
    group: 调料
  - name: 生抽
    amount: 2
    unit: tbsp
    group: 调料
  - name: 葱
    amount: 2
    unit: 段
    note: 拍松                          # 可选备注

# 营养（可选）
nutrition:
  calories_kcal: 520
  protein_g: 28
  fat_g: 42
  carbs_g: 8
  sodium_mg: 680
  source: food.com dataset             # 数据来源
  estimated: false                     # 原站已给 = false；我们按食材汇总 = true

# 技法 / 器具（可选）
techniques:
  - 煸炒糖色
  - 焖煮
equipment:
  - 炒锅
  - 砂锅

# 其它（可选）
image: https://.../cover.jpg
video: https://youtube.com/...
rating: 4.7                             # 原站评分
---

## 简介
简短介绍或故事背景。

## 步骤
1. 五花肉切 3cm 见方块。冷水下锅焯 2 分钟...
2. ...

## 备注
常见坑 / 变体。

## 来源
- 站点：xiachufang
- 链接：https://www.xiachufang.com/recipe/12345/
```

## 字段语义

### `title` / `title_en`
主标题用当地语言；若有官方英文名（比如用 Kaggle 数据集导入中餐名字没有中文）可反过来——`title` 英文，`title_en` 可空。

### `cuisine`
自由字符串。推荐值：
- 中餐分支：`中餐家常`、`川菜`、`粤菜`、`鲁菜`、`苏菜`、`浙菜`、`闽菜`、`湘菜`、`徽菜`、`东北菜`、`江南`、`西北`、`云贵`
- 西餐分支：`意餐`、`法餐`、`美式`、`英伦`、`地中海`、`墨西哥`、`西班牙`、`北欧`
- 其它：`日餐`、`韩餐`、`泰餐`、`印餐`、`中东`

### `category`
- `主菜` / `汤` / `甜点` / `早餐` / `主食`（面/饭/饺）/ `沙拉` / `前菜` / `酱汁`

### `servings`
整数优先；若原文是 "4-6 people" 就取 4（低估比高估安全）。

### `time.total_min`
整数分钟。包含 prep + cook。如果原站只给了"cook 60 min"，按合理估计补 prep（切菜 ~15 min）。

### `tags`
中英混合无所谓，小写化。常见 tag：
- 食材：`猪肉` / `鸡肉` / `牛肉` / `海鲜` / `鸡蛋` / `豆腐` / `蔬菜`
- 口味：`麻辣` / `清淡` / `酸甜` / `咸鲜`
- 场景：`家常` / `宴客` / `下饭` / `下酒` / `早餐` / `夜宵`
- 属性：`快手`(≤30min) / `懒人` / `健身` / `素食` / `vegan`

### `ingredients[*].amount` 和 `unit`

**amount 尽量是数字**（int 或 float）。如果原文是"适量" / "少许" / "一把"，保留字符串但标清楚：

```yaml
- name: 盐
  amount: 适量
  unit: ''
```

**unit** 优先级：
- 克重：`g`、`kg`
- 体积：`ml`、`L`、`tsp`（5ml）、`tbsp`（15ml）、`cup`（240ml）、`oz`（30ml）
- 计数：`个`、`颗`、`瓣`、`片`、`段`、`根`、`枝`、`束`、`匙`
- 描述：`适量`、`少许`

### `nutrition.estimated`
- `false`：数据来自原站或官方数据集
- `true`：`api_openfoodfacts.py` 按食材汇总的估算

## 单位换算速查

| 从 | 到 | 系数 |
|---|---|---|
| 1 tbsp | ml | 15 |
| 1 tsp | ml | 5 |
| 1 cup (US) | ml | 236.6 |
| 1 cup (metric) | ml | 250 |
| 1 oz (液) | ml | 29.6 |
| 1 oz (重) | g | 28.35 |
| 1 lb | g | 453.6 |
| 1 两 | g | 50（中国大陆）/ 31.25（台湾）|
| 1 斤 | g | 500（大陆）/ 600（台湾）|
| 1 kg | 斤 | 2 |

食材常见等价（烹饪估算，不绝对）：
| 食材 | 1 cup | 单个/个 |
|---|---|---|
| 面粉 | 120 g | — |
| 糖（细砂） | 200 g | — |
| 水 / 奶 | 240 g | — |
| 黄油 | 227 g | 1 stick = 113 g |
| 鸡蛋 | 5 个 | 50 g/个（带壳约 55g） |
| 米饭（熟） | 180 g | — |
| 番茄（中） | — | 120-150 g |
| 洋葱（中） | — | 170 g |
| 土豆（中） | — | 170 g |
| 鸡胸 | — | 200-250 g |

## 文件命名

由 `scripts/_lib.py:make_slug()` 生成。格式：

```
{title-slugified}-{source}-{external_id}.md
```

例：
- `红烧肉-xiachufang-12345.md`
- `tikka-masala-themealdb-52819.md`
- `world-s-best-lasagna-allrecipes-23600.md`

slug 规则：
- 小写
- 空格 / `/` → `-`
- 中日韩字符保留
- 非字母非 CJK 非数字非 `-` 一律删
- 最长 60 字符

## 去重

`write_recipe()` 默认 **不覆盖**。同 slug 出现 → 跳过、返回现有 path。
要强制刷新用 `overwrite=True` 或删文件重抓。

## 搜索友好

frontmatter 设计成一眼能 grep：

```bash
# 所有川菜
grep -l "cuisine: 川菜" data/recipes/*.md

# 所有用鸡蛋的
grep -l -- "- name: 鸡蛋" data/recipes/*.md

# 所有快手（标签）
grep -l "- 快手" data/recipes/*.md
```

`scripts/search.py` 封装了这些。
