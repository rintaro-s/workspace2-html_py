# Frontend (Next.js)

- app/page.tsx: ルートアクセスは `public/index.html` にリダイレクトします。
- app/index.html/route.ts: リポジトリ直下の元の `index.html` を配信するルート(API Routes)。
- public/index.html: 開発メモ用の最小ラッパー。通常は `/index.html` ルートを利用してください。

開発:
- `npm i` または `pnpm i` で依存を入れて `npm run dev`。
- `/api.cgi` と `/files/*` は Next の rewrite により Rails(3001)へ転送されます。
