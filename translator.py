import os
import pathlib
from dotenv import load_dotenv
from azure.ai.translation.text import TextTranslationClient, TranslatorCredential
from azure.ai.translation.text.models import InputTextItem
import jieba
import pandas as pd

# 載入 .env
env_path = pathlib.Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Translator API 設定
TRANSLATOR_KEY = os.getenv('TRANSLATOR_KEY')
TRANSLATOR_ENDPOINT = os.getenv('TRANSLATOR_ENDPOINT')
TRANSLATOR_REGION = os.getenv('TRANSLATOR_REGION')

if not TRANSLATOR_KEY or not TRANSLATOR_ENDPOINT:
    raise ValueError("❌ TRANSLATOR_KEY 或 TRANSLATOR_ENDPOINT 為空，請確認 .env 是否正確")

# 建立 Translator API 客戶端
translator_credential = TranslatorCredential(TRANSLATOR_KEY, TRANSLATOR_REGION)
translator_client = TextTranslationClient(endpoint=TRANSLATOR_ENDPOINT, credential=translator_credential)

# 載入食物名稱作為自訂詞典
def load_food_dictionary():
    try:
        df = pd.read_excel("nutrition.ods", engine="odf", sheet_name="工作表1", header=1)
        df = df[["樣品名稱"]]
        df.columns = ["食物名稱"]
        df.dropna(subset=["食物名稱"], inplace=True)
        food_names = df["食物名稱"].tolist()
        # 添加常見食物名稱變體
        food_variants = {
            "雞蛋": ["雞蛋", "蛋", "雞蛋平均值"],
            "漢堡": ["漢堡", "漢堡包"],
            "義大利麵": ["義大利麵", "義麵"],
            "西蘭花": ["西蘭花", "花椰菜"]
        }
        for main_food, variants in food_variants.items():
            for variant in variants:
                jieba.add_word(variant, freq=10000, tag='n')
        print(f"已載入 {len(food_names)} 個食物名稱到 jieba 詞典")
    except Exception as e:
        print(f"❌ 無法載入 nutrition.ods 作為詞典: {str(e)}")

# 初始化詞典
load_food_dictionary()

def translate_text(text: str, target_language: str = "zh-Hant") -> str:
    try:
        print("翻譯輸入文字:", text)
        print("目標語言:", target_language)
        input_text = [InputTextItem(text=text)]
        response = translator_client.translate(input_text, to=[target_language])
        translated_text = response[0].translations[0].text
        print("翻譯結果:", translated_text)
        return translated_text
    except Exception as e:
        print(f"❌ 翻譯錯誤: {str(e)}")
        raise

def extract_keywords(text: str, top_n: int = 5) -> list:
    try:
        # 動態添加詞彙
        jieba.add_word("義大利麵", freq=10000, tag='n')
        jieba.add_word("西蘭花", freq=10000, tag='n')
        jieba.add_word("雞蛋", freq=10000, tag='n')
        jieba.add_word("漢堡", freq=10000, tag='n')

        # 檢查並載入自訂詞典
        user_dict_path = pathlib.Path(__file__).parent / "user_dict.txt"
        if user_dict_path.exists():
            jieba.load_userdict(str(user_dict_path))
        else:
            print("⚠️ 未找到 user_dict.txt")

        # 停用詞列表，包含數量詞
        stop_words = {
            '一盤', '一碗', '一杯', '一份', '的', '是', '在', '有',
            '幾個', '一些', '一堆', '一塊', '一', '兩個', '三個', '四個', '五個'
        }

        # 使用精確分詞
        words = jieba.cut(text, cut_all=False)
        word_list = list(words)
        print(f"分詞結果: {word_list}")

        # 過濾停用詞和無效詞
        keywords = [word for word in word_list if len(word) > 1 and not word.isdigit() and word not in stop_words]
        
        # 過濾子詞（避免短詞包含在長詞中）
        valid_keywords = []
        for word in keywords:
            if not any(word in other_word and len(other_word) > len(word) for other_word in keywords):
                valid_keywords.append(word)
        
        # 如果無有效關鍵字，返回預設值
        if not valid_keywords:
            print("⚠️ 無有效關鍵字，檢查分詞邏輯")
            return ["無關鍵字"]
        
        print(f"提取的關鍵字: {valid_keywords[:top_n]}")
        return valid_keywords[:top_n]
    except Exception as e:
        print(f"❌ 關鍵字提取錯誤: {str(e)}")
        return ["無關鍵字"]