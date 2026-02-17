import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/common/providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Richlychee - 네이버 스마트스토어 대량 상품 등록",
  description: "엑셀 파일 업로드로 네이버 스마트스토어에 상품을 대량 등록하세요.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        <script src="https://cdn.portone.io/v2/browser-sdk.js"></script>
      </head>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
