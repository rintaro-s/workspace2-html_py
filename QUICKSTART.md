# クイックスタートガイド

## 🚀 簡単起動（推奨）

### Windows用バッチファイル
```bash
# 開発環境で起動
start.bat

# Docker環境で起動
start-docker.bat
```

### 手動起動

#### 1. 開発環境
```bash
# 依存関係をインストール
pip install -r requirements.txt

# サーバー起動
python app.py
```

#### 2. Docker環境
```bash
# イメージをビルドして起動
docker-compose up -d

# または本番用設定で起動
docker-compose -f docker-compose.production.yml up -d
```

## 📝 初回セットアップ

1. **アクセス**: http://localhost:8060
2. **アカウント作成**: 新規ユーザー登録
3. **サークル作成**: 「+」ボタンから新しいサークルを作成
4. **機能利用開始**: 左サイドバーから各機能を利用

## 🔧 設定

### 環境変数
`.env.example`をコピーして`.env`ファイルを作成し、設定を調整：
```bash
cp .env.example .env
```

### ポート変更
デフォルト：8060番ポート
変更方法：
- `app.py`の最後の行を編集
- または環境変数`FLASK_PORT`を設定

## 📂 データ

- **保存場所**: `./data/circle_platform.db` (SQLite)
- **バックアップ**: `data`フォルダをコピー

## 🛠️ 開発

### デバッグモード
```bash
export FLASK_DEBUG=true
python app.py
```

### ログ監視（Docker）
```bash
docker-compose logs -f
```

## ❓ トラブルシューティング

### ポートが使用中
```bash
# Windowsで使用中のプロセスを確認
netstat -ano | findstr :8060

# プロセスを終了
taskkill /PID <プロセスID> /F
```

### データベースリセット
```bash
# データベースファイルを削除
rm -f data/circle_platform.db

# サーバー再起動でデータベースが再作成されます
```

### Docker問題
```bash
# コンテナを完全に削除して再構築
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🌟 機能一覧

- ✅ ユーザー認証（ログイン・登録）
- ✅ マルチサークル管理
- ✅ リアルタイムチャット
- ✅ フォーラム（掲示板）
- ✅ ホワイトボード（共同描画）
- ✅ Wiki（知識ベース）
- ✅ プロジェクト管理・タスク管理
- ✅ カレンダー・イベント管理
- ✅ 予算・財務管理
- ✅ 物品・インベントリ管理
- ✅ メンバー管理
- ✅ フォトアルバム
- ✅ 共有日記
- ✅ アンケート・投票機能

## 📞 サポート

問題が解決しない場合は、以下を確認してください：
1. Python 3.10以上がインストールされているか
2. 必要なポート（5060）が利用可能か
3. ファイアウォールの設定
4. ディスク容量の確認
