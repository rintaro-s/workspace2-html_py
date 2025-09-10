FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# データベースディレクトリを作成
RUN mkdir -p /app/data

# ポート8060を公開
EXPOSE 8060

# アプリケーションを開始
CMD ["python", "app.py"]
