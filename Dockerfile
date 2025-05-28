FROM python:3.10-slim

RUN apt update

# 設置工作目錄
WORKDIR /app

# 複製 requirements.txt（稍後創建）
COPY requirements.txt .

# 安裝系統依賴和 Python 套件
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY main.py vision.py translator.py match_kp.py ./
COPY templates/food.html ./templates/
COPY nutrition.ods recommend.xlsx ./
COPY .env ./

# 暴露端口
EXPOSE 8080

# 設置環境變數（確保 Flask 運行在 production 模式）
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# 啟動 Flask 應用
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]