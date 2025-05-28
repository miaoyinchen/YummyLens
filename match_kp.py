import pandas as pd
from difflib import get_close_matches

# 載入營養成分資料
file_path = "nutrition.ods"
try:
    df = pd.read_excel(file_path, engine="odf", sheet_name="工作表1", header=1)
    df = df[["樣品名稱", "熱量(kcal)", "粗蛋白(g)"]]
    df.columns = ["食物名稱", "熱量(kcal)", "蛋白質(g)"]
    df.dropna(subset=["食物名稱"], inplace=True)
except Exception as e:
    print(f"❌ 無法載入 nutrition.ods: {str(e)}")
    df = pd.DataFrame()

# 載入推薦餐廳資料
try:
    recommend_df = pd.read_excel("recommend.xlsx")
except Exception as e:
    print(f"❌ 無法載入 recommend.xlsx: {str(e)}")
    recommend_df = pd.DataFrame()

# 食物名稱映射
FOOD_MAPPING = {
    "雞蛋": "雞蛋平均值",
    "漢堡": "漢堡包",
    "義大利麵": "義大利麵",
    "西蘭花": "西蘭花"
}

# 查詢營養成分函式
def search_nutrition(keyword: str, df: pd.DataFrame, top_n: int = 1):
    if df.empty:
        return pd.DataFrame([{
            "食物名稱": "無資訊",
            "熱量(kcal)": 0,
            "蛋白質(g)": 0
        }])
    all_names = df["食物名稱"].tolist()
    # 檢查是否有映射
    keyword = FOOD_MAPPING.get(keyword, keyword)
    matches = get_close_matches(keyword, all_names, n=top_n, cutoff=0.6)
    if matches:
        result = df[df["食物名稱"].isin(matches)].reset_index(drop=True)
        return result
    else:
        return pd.DataFrame([{
            "食物名稱": "無資訊",
            "熱量(kcal)": 0,
            "蛋白質(g)": 0
        }])

# 篩除同類重複詞
def remove_similar_variants(food_list):
    final = []
    for food in food_list:
        is_similar = False
        for kept in final:
            if food in kept or kept in food:
                is_similar = True
                if len(food) > len(kept):
                    final.remove(kept)
                    final.append(food)
                break
            shared_chars = set(food) & set(kept)
            if len(shared_chars) >= min(len(food), len(kept)) // 2:
                is_similar = True
                break
        if not is_similar:
            final.append(food)
    return final

# 擷取句子中的食物詞
def get_all_matched_foods_from_sentence(sentence: str, food_names: list, min_overlap: int = 2, top_k: int = 3):
    matched = [food for food in food_names if food in sentence]
    filtered = []
    for food in matched:
        is_substring = False
        for other in matched:
            if food != other and food in other:
                is_substring = True
                break
        if not is_substring:
            filtered.append(food)
    matched_set = set(filtered)
    remaining_foods = [f for f in food_names if f not in matched_set]
    scores = []
    for food in remaining_foods:
        overlap = 0
        for i in range(len(food) - min_overlap + 1):
            sub = food[i:i + min_overlap]
            if sub in sentence:
                overlap += 1
        if overlap > 0:
            scores.append((food, overlap))
    scores.sort(key=lambda x: x[1], reverse=True)
    top_matches = [food for food, _ in scores[:top_k] if food not in matched_set]
    return remove_similar_variants(list(matched_set) + top_matches)

def find_nutrition(keywords):
    try:
        if not isinstance(keywords, str):
            keywords = " ".join(keywords)  # 將關鍵字列表轉為字串
        if df.empty:
            print("❌ 營養資料庫為空")
            return 0, 0
        food_list = df["食物名稱"].tolist()
        matched_foods = get_all_matched_foods_from_sentence(keywords, food_list)
        if not matched_foods:
            print("❌ 無匹配食物")
            return 0, 0
        for food in matched_foods:
            result = search_nutrition(food, df)
            calories = result.iloc[0]["熱量(kcal)"]
            protein = result.iloc[0]["蛋白質(g)"]
            if isinstance(calories, (int, float)) and isinstance(protein, (int, float)):
                print(f"找到營養資訊 - 食物: {food}, 熱量: {calories}, 蛋白質: {protein}")
                return calories, protein
        print("❌ 無有效營養資訊")
        return 0, 0
    except Exception as e:
        print(f"❌ find_nutrition 錯誤: {str(e)}")
        return 0, 0

def recommend_restaurants(keywords):
    try:
        if not isinstance(keywords, str):
            keywords = " ".join(keywords)  # 將關鍵字列表轉為字串
        if recommend_df.empty or df.empty:
            print("❌ 資料庫為空")
            return []
        food_list = df["食物名稱"].tolist()
        matched_foods = get_all_matched_foods_from_sentence(keywords, food_list)
        if not matched_foods:
            print("❌ 無匹配食物")
            return []
        for food in matched_foods:
            result = search_nutrition(food, df)
            name = result.iloc[0]["食物名稱"]
            if name == "無資訊":
                continue
            matched_row = recommend_df[recommend_df["可能包含食物"] == name]
            if not matched_row.empty:
                restaurant = matched_row.iloc[0]["推薦餐廳"]
                restaurants = [r.strip() for r in restaurant.split("、")]
                print(f"找到餐廳 - 食物: {name}, 餐廳: {restaurants}")
                return restaurants
        print(f"❌ 無推薦餐廳 for 食物: {name}")
        return []
    except Exception as e:
        print(f"❌ recommend_restaurants 錯誤: {str(e)}")
        return []