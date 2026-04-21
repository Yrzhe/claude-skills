# 免费 API 使用说明

## TheMealDB

**官网**：https://www.themealdb.com  
**base URL**：`https://www.themealdb.com/api/json/v1/1`  
**Auth**：开发阶段 API key 固定为 `1`，完全免费。  
**规模**：~283 道菜，覆盖 30+ 地区。

### 端点速查

| 用途 | 端点 |
|---|---|
| 名字搜 | `/search.php?s={query}` |
| 首字母筛 | `/search.php?f={a-z}` |
| 随机一道 | `/random.php` |
| ID 查菜 | `/lookup.php?i={id}` |
| 按食材过滤（只返 id+name） | `/filter.php?i={ingredient}` |
| 按地区过滤 | `/filter.php?a={Chinese|Italian|...}` |
| 按分类过滤 | `/filter.php?c={Beef|Chicken|Seafood|Dessert|...}` |
| 列地区 | `/list.php?a=list` |
| 列分类 | `/categories.php` |
| 列所有食材 | `/list.php?i=list` |

### 响应字段（meal 对象）

```
idMeal, strMeal, strCategory, strArea, strInstructions,
strMealThumb, strTags, strYoutube, strSource,
strIngredient1..20, strMeasure1..20
```

食材是 20 对"并列字段"——`strIngredient3` 对应 `strMeasure3`。空串表示那一槽没用上。

### curl 示例

```bash
# 名字搜
curl -s 'https://www.themealdb.com/api/json/v1/1/search.php?s=arrabiata' | jq .

# 随机
curl -s 'https://www.themealdb.com/api/json/v1/1/random.php' | jq '.meals[0].strMeal'

# 按食材找（返回 id 列表）
curl -s 'https://www.themealdb.com/api/json/v1/1/filter.php?i=chicken_breast' | jq '.meals | length'
```

### 在本 skill 里

`scripts/api_themealdb.py` 封装了所有端点，存菜到 `data/recipes/`：

```bash
python scripts/api_themealdb.py --search 'tikka'
python scripts/api_themealdb.py --random
python scripts/api_themealdb.py --area Chinese
python scripts/api_themealdb.py --bootstrap    # 全量拉
```

## Open Food Facts

**官网**：https://world.openfoodfacts.org（中文镜像 https://cn.openfoodfacts.org）  
**Auth**：无。  
**用途**：**营养数据库**，按产品/食材查每 100g 的热量、蛋白、脂肪、碳水、糖、钠、膳食纤维、Nutri-Score。不是食谱源。  
**协议**：Open Database License (ODbL)。

### 端点

```
v2 搜索：/api/v2/search?search_terms={q}&page_size={n}&fields=product_name,nutriments,...
v1 搜索：/cgi/search.pl?search_terms={q}&search_simple=1&action=process&json=1&page_size={n}
按条码： /api/v2/product/{barcode}.json
食材库： /ingredients.json
```

> **已知问题（2026-04 观察）**：搜索端点（v1 和 v2 都）有时 503。barcode 端点很稳。脚本 `api_openfoodfacts.py` 已经自动回退并给出友好提示——搜索挂时改用 barcode 查询。

### 响应结构（摘要）

```json
{
  "products": [{
    "product_name": "鸡蛋",
    "brands": "...",
    "code": "barcode",
    "nutriments": {
      "energy-kcal_100g": 143,
      "proteins_100g": 12.6,
      "fat_100g": 9.5,
      "carbohydrates_100g": 1.1,
      "sodium_100g": 0.14,
      "sugars_100g": 1.1,
      "fiber_100g": 0
    },
    "nutriscore_grade": "b"
  }]
}
```

### curl 示例

```bash
# 搜 "鸡蛋"（中文镜像）
curl -s 'https://cn.openfoodfacts.org/cgi/search.pl?search_terms=鸡蛋&search_simple=1&action=process&json=1&page_size=3' | jq '.products[0].nutriments'

# 按条码
curl -s 'https://world.openfoodfacts.org/api/v2/product/3017620422003.json' | jq '.product.product_name'
```

### 在本 skill 里

```bash
python scripts/api_openfoodfacts.py --query "鸡蛋"
python scripts/api_openfoodfacts.py --query "chicken breast" --lang en --limit 3
python scripts/api_openfoodfacts.py --barcode 3017620422003
```

## 为食谱估算总营养的流程

1. 先看 `data/recipes/{slug}.md` 的 `frontmatter.nutrition.calories_kcal` 是否已填
2. 没填 → 遍历 `ingredients`，逐个 `api_openfoodfacts.py --query <name>`
3. 按 `amount / 100 * value_per_100g` 线性汇总
4. 写回 frontmatter，标 `estimated: true` 和 `source: openfoodfacts-aggregated`
5. 注意：单位（g/ml/个）需统一；"1 颗鸡蛋" 按 50g 估

## 为什么没有其它 API

- **Spoonacular / Edamam**：freemium，需要 API key；用户选择不纳入
- **MyFitnessPal / USDA FoodData Central**：USDA 有免费 API 但注册流程在 api.nal.usda.gov 且 key 轮转——暂不纳入，改用 Open Food Facts 覆盖
