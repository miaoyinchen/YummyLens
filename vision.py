import os
import pathlib
from dotenv import load_dotenv
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import requests

# 載入 .env
env_path = pathlib.Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

VISION_KEY = os.getenv('VISION_KEY')
VISION_ENDPOINT = os.getenv('VISION_ENDPOINT')

if not VISION_KEY or not VISION_ENDPOINT:
    raise ValueError("❌ KEY 或 ENDPOINT 為空，請確認 .env 是否正確")

# 建立 Vision API 客戶端
client = ComputerVisionClient(
    endpoint=VISION_ENDPOINT,
    credentials=CognitiveServicesCredentials(VISION_KEY)
)

def analyze_image_vision_url(image_url, key, endpoint):
    try:
        analyze_url = f"{endpoint}/vision/v3.2/analyze"
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/json"
        }
        params = {"visualFeatures": "Tags,Description"}
        data = {"url": image_url}

        print(f"發送 Vision API 請求，URL: {image_url}")
        response = requests.post(analyze_url, headers=headers, params=params, json=data)
        response.raise_for_status()
        analysis = response.json()
        print(f"Vision API 回應: {analysis}")

        tags = [tag["name"] for tag in analysis.get("tags", [])]
        desc = analysis.get("description", {}).get("captions", [{}])[0].get("text", "")
        return tags, desc
    except Exception as e:
        print(f"❌ Vision API 錯誤: {str(e)}")
        raise

def analyze_image_vision(image_data, key, endpoint):
    try:
        analyze_url = f"{endpoint}/vision/v3.2/analyze"
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/octet-stream"
        }
        params = {"visualFeatures": "Tags,Description"}

        print(f"發送 Vision API 請求，上傳圖片")
        response = requests.post(analyze_url, headers=headers, params=params, data=image_data)
        response.raise_for_status()
        analysis = response.json()
        print(f"Vision API 回應: {analysis}")

        tags = [tag["name"] for tag in analysis.get("tags", [])]
        desc = analysis.get("description", {}).get("captions", [{}])[0].get("text", "")
        return tags, desc
    except Exception as e:
        print(f"❌ Vision API 錯誤: {str(e)}")
        raise