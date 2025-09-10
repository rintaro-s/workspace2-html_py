# Next.js(Typescript) + Rails への完全移行ガイド

このフォルダは、既存の Flask + 単一HTML のアプリを Next.js(Typescript) + Ruby on Rails(API) に移行したプロジェクトです。

構成:

- frontend: Next.js 14 (Typescript)。API は Rails の `/api.cgi` を利用します。
   - ルート `/` は `app/page.tsx` 経由で `/index.html` へ遷移します。
   - `/index.html` は `public/index.html` が `/original-index.html` へ即時リダイレクトし、`public/original-index.html` を配信します。
   - 運用では、リポジトリ直下の最新 `index.html` を `convert/frontend/public/original-index.html` にコピーしてください。
- backend: Rails(API)。Flask の `/api.cgi` と互換のアクションディスパッチと、同等の DB スキーマ(SQLite)を実装しています。ファイル配信 `/files/*` も提供します。

互換ポリシー:

- エンドポイントは `/api.cgi` (POST, form-data) 1本に集約し、`action` パラメータで分岐する互換レイヤを Rails に実装。
- DB は SQLite を継続使用。テーブル: users, servers, server_members, server_invites, password_recovery, files, features, feature_content, sessions。
- 既存のファイル保存レイアウト `files/uploads`, `files/avatars`, `files/whiteboards` を継承。Rails 側で相対 `files/` 直下に保存し、`/files/*` で配信。

開発ポートの想定:

- Rails(API): http://localhost:3001
- Next.js: http://localhost:3000 (フロントから `/api.cgi` と `/files/*` は next.config の rewrite で Rails に転送)

起動手順(ローカル開発):

1) backend (Rails)

   - Ruby 3.2+ / Bundler が必要です。
   - GEM をインストールし、DB を作成・マイグレーションします。

   ```bash
   cd convert/backend
   bundle install
   bin/rails db:setup # 失敗する場合は db:create と db:migrate を順に
   bin/rails s -p 3001
   ```

   注: 初回は `files/` 配下の保存先を作成してください。

   ```bash
   mkdir -p files/uploads files/avatars files/whiteboards data
   ```

2) frontend (Next.js)

   - Node.js 18+ を推奨します。

   ```bash
   cd ../frontend
   npm i # or pnpm i / yarn
   npm run dev
   ```

   ブラウザで http://localhost:3000 を開きます。

プロダクション想定:

- Rails は `RAILS_ENV=production` で起動、DB は SQLite でも Postgres でも可。`DATABASE_URL` を設定してください。
- Next.js は `next build && next start`。
- リバースプロキシ(Nginx等)で `/api.cgi` と `/files/*` を Rails に、他を Next.js に振り分ける構成を推奨します。

差分と注意点:

- Rails のセッションは CookieStore を有効化済み。Flask の `session['user_id']` 相当は Rails の `session[:user_id]` を利用しています。
- Flask の `feature_content` は JSON 文字列で保存していたため、Rails でも文字列(JSON)として保存します。
- 画像/ファイルアップロードは 10MB 制限・UUID ファイル名付けなど Flask 実装を踏襲。
- 互換性のため Rails 側で `/api.cgi` を 1 アクションに集約し、`case` で分岐しています(将来は REST 化を推奨)。
 - フロントの一部で `memberId` と `userId` の両方が送信されるため、Rails 側で互換吸収しています。
 - 旧クライアントの `/file/:filename` パスに対応するため、Rails に `/file/:filename` を追加し `/files/uploads/:filename` を配信します。

テスト(スモーク):

1. Next.js を http://localhost:3000 で起動
2. Rails を http://localhost:3001 で起動
3. 画面のログイン/登録→サーバ作成→チャット投稿→ファイルアップロード→ホワイトボード保存→アンケート作成/回答→プロジェクト/タスク進行の順に動作確認

既知の制限/今後の改善:

- 既存の巨大な UI は最初は `public/index.html` として提供しています。段階的に React コンポーネントへ分割する計画を README に追記します。
- 高負荷時の N+1 クエリやバリデーション強化、権限管理(ロール/パーミッション)の詳細化、エラーハンドリングの拡充は次段階で実施予定です。
