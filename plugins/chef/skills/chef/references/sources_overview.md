# 数据源总览

每个源的配置详情见 `sources/*.json`。下表是快速选源参考。

## 选源决策树

- **有一个具体 URL** → `fetch.py --url ...`（走 scrape_web.py：recipe-scrapers → JSON-LD 回退）
- **要中餐食谱** → 下厨房（最广）、美食杰（菜系分类最全）、豆果（竞品）
- **要英文食谱** → `themealdb` 免费 API（轻量 283 道）、`allrecipes` / `bbcgoodfood` 单抓
- **冷启动批量** → Kaggle 预爬数据集 `food_com` (18w 道)、`epicurious` (2w 道)
- **只要营养** → `openfoodfacts` API（食材级营养）
- **未知站点** → `recipe-scrapers` 库（631+ 支持）+ wild_mode 兜底

## 全表（按 access_method 分组）

### API（免费、零依赖）
| id | 语言 | 规模 | 说明 |
|---|---|---|---|
| `themealdb` | en | ~283 | 开发 key `1` 无限用；a-z 字母 bootstrap 即全量 |
| `openfoodfacts` | mix | 400w+ 产品 | 营养源，不是食谱源 |

### Kaggle/学术 预爬数据集（下载一次）
| id | 语言 | 规模 | 文件 |
|---|---|---|---|
| `food_com` | en | 180,000 | RAW_recipes.csv |
| `epicurious` | en | 20,000+ | full_format_recipes.json |
| `tada_chinese` | zh | 12,142 | 学术数据集，需自找 release |

### 爬虫库（631 站点内置）
| id | 语言 | 说明 |
|---|---|---|
| `recipe_scrapers_generic` | mix | `pip install recipe-scrapers`；直接喂 URL |
| `allrecipes` | en | 库一等公民；爬取难度 1/5 |
| `bbcgoodfood` | en | 库一等公民；17000+ 道 |

### 手写选择器（国内中文站）
| id | 语言 | 说明 |
|---|---|---|
| `xiachufang` | zh | 列表页 + 详情页选择器见 sources/xiachufang.json |
| `douguo` | zh | 移动站 m.douguo.com 比 PC 更易抓 |
| `meishij` | zh | 菜系分类最完整；可能需 cookie |
| `xiangha` | zh | 9000w 用户 |
| `xinshipu` | zh | Food-530 数据集的菜名源 |

## 合规注意（个人非商用）

- robots.txt 仅作知情参考，本 skill 个人使用时不作硬拦截
- 每个源 JSON 的 `robots_note` 字段记录了该站限制——若将来做商业化使用，需回去补签授权
- 输出食谱必须在末尾标明来源站 + URL（SKILL.md 硬规则 #7）
- 食谱的"事实部分"（食材列表、配比）不受版权保护；图片、视频、文字表达可能受保护，**抓图和视频要当心**
- 请求频率：默认每个源 JSON 里有 `rate_limit_sec`；批量抓的时候 `scrape_web.py` 会遵守它
- 付费 API（Spoonacular / Edamam）已经整个砍掉——本 skill 不做

## 冷启动剧本

```bash
# 1. 装依赖
python scripts/setup.py --yes

# 2. 英文种子（~30s）
python scripts/api_themealdb.py --bootstrap

# 3. 大批量（可选，需先去 Kaggle 下 CSV）
python scripts/import_dataset.py --source food_com --file ~/Downloads/RAW_recipes.csv --limit 10000

# 4. 中文冷启动：搜一个就抓一批（下厨房）
python scripts/fetch.py --source xiachufang --query 家常菜 --limit 20

# 5. 验证
python scripts/search.py --random
python scripts/suggest.py --have "鸡蛋,西红柿,葱"
```
