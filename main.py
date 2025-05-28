from flask import Flask, request, render_template, jsonify
from vision import analyze_image_vision_url, analyze_image_vision
from translator import translate_text, extract_keywords
from match_kp import find_nutrition, recommend_restaurants
import pathlib
from dotenv import load_dotenv
import os
import validators

app = Flask(__name__)

# 載入 .env 檔案
env_path = pathlib.Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# 取得環境變數
VISION_KEY = os.getenv('VISION_KEY')
VISION_ENDPOINT = os.getenv('VISION_ENDPOINT')
TRANSLATOR_KEY = os.getenv('TRANSLATOR_KEY')
TRANSLATOR_ENDPOINT = os.getenv('TRANSLATOR_ENDPOINT')
TRANSLATOR_REGION = os.getenv('TRANSLATOR_REGION')

# 檢查是否為有效圖片 URL
def is_image_url(url: str) -> bool:
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    if not url.lower().endswith(image_extensions):
        return False
    if url.startswith('https://www.google.com/url'):
        return False
    return True

# 檢查是否為有效圖片檔案
def is_valid_image_file(file):
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    max_size = 4 * 1024 * 1024  # 4MB
    if not file:
        return False, "未提供檔案"
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return False, "無效的檔案格式，僅支援 .jpg, .png, .gif, .bmp"
    if file.content_length and file.content_length > max_size:
        return False, "檔案過大，最大允許 4MB"
    return True, ""

@app.route("/", methods=["GET"])
def index():
    return render_template("food.html")

@app.route("/analyze", methods=["POST"])
def analyze_from_url():
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        
        # 驗證 URL
        if not image_url or not validators.url(image_url):
            return jsonify({"error": "無效的 URL，請輸入正確的網址"}), 400
        if not is_image_url(image_url):
            return jsonify({"error": "URL 必須指向圖片檔案（例如 .jpg 或 .png）"}), 400

        # 模組2：圖片分析
        try:
            tags, desc = analyze_image_vision_url(image_url, VISION_KEY, VISION_ENDPOINT)
        except Exception as e:
            print(f"❌ 圖片分析錯誤: {str(e)}")
            return jsonify({"error": f"圖片分析失敗：{str(e)}"}), 500

        # 模組3：翻譯標籤並擷取關鍵詞
        try:
            translated_description = translate_text(desc)
            keywords = extract_keywords(translated_description)
        except Exception as e:
            print(f"❌ 翻譯或關鍵字提取錯誤: {str(e)}")
            return jsonify({"error": "翻譯或關鍵字提取失敗"}), 500

        # 模組4：查找營養資訊與推薦餐廳
        try:
            calories, protein = find_nutrition(keywords)
            restaurants = recommend_restaurants(keywords)
        except Exception as e:
            print(f"❌ 營養或餐廳推薦錯誤: {str(e)}")
            return jsonify({"error": "營養或餐廳推薦失敗"}), 500

        # 回傳結果
        return jsonify({
            "english": desc or "No description",
            "chinese": keywords or [],
            "calories": calories if isinstance(calories, (int, float)) else 0,
            "protein": protein if isinstance(protein, (int, float)) else 0,
            "restaurants": restaurants if isinstance(restaurants, list) else []
        })
    except Exception as e:
        print(f"❌ 伺服器錯誤: {str(e)}")
        return jsonify({"error": "伺服器內部錯誤，請稍後再試"}), 500

@app.route("/analyze_upload", methods=["POST"])
def analyze_from_upload():
    try:
        # 檢查是否有檔案
        if 'image' not in request.files:
            return jsonify({"error": "未上傳圖片檔案"}), 400

        file = request.files['image']
        is_valid, error_msg = is_valid_image_file(file)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # 讀取檔案內容
        image_data = file.read()

        # 模組2：圖片分析
        try:
            tags, desc = analyze_image_vision(image_data, VISION_KEY, VISION_ENDPOINT)
        except Exception as e:
            print(f"❌ 圖片分析錯誤: {str(e)}")
            return jsonify({"error": f"圖片分析失敗：{str(e)}"}), 500

        # 模組3：翻譯標籤並擷取關鍵詞
        try:
            translated_description = translate_text(desc)
            keywords = extract_keywords(translated_description)
        except Exception as e:
            print(f"❌ 翻譯或關鍵字提取錯誤: {str(e)}")
            return jsonify({"error": "翻譯或關鍵字提取失敗"}), 500

        # 模組4：查找營養資訊與推薦餐廳
        try:
            calories, protein = find_nutrition(keywords)
            restaurants = recommend_restaurants(keywords)
        except Exception as e:
            print(f"❌ 營養或餐廳推薦錯誤: {str(e)}")
            return jsonify({"error": "營養或餐廳推薦失敗"}), 500

        # 回傳結果
        return jsonify({
            "english": desc or "No description",
            "chinese": keywords or [],
            "calories": calories if isinstance(calories, (int, float)) else 0,
            "protein": protein if isinstance(protein, (int, float)) else 0,
            "restaurants": restaurants if isinstance(restaurants, list) else []
        })
    except Exception as e:
        print(f"❌ 伺服器錯誤: {str(e)}")
        return jsonify({"error": "伺服器內部錯誤，請稍後再試"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)