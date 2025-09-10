import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'サークル管理プラットフォーム',
  description: 'Next.js + Rails 移植版',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
