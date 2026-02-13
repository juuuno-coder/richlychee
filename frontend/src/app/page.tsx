import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Cherry, Upload, Zap, BarChart3 } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* 네비게이션 */}
      <nav className="border-b">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2 font-bold text-lg">
            <Cherry className="h-6 w-6 text-red-500" />
            Richlychee
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">로그인</Button>
            </Link>
            <Link href="/register">
              <Button>시작하기</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* 히어로 */}
      <section className="mx-auto max-w-6xl px-4 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          네이버 스마트스토어
          <br />
          <span className="text-primary">대량 상품 등록</span>을 쉽게
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
          엑셀 파일 하나로 수백 개의 상품을 한 번에 등록하세요.
          자동 검증, 이미지 업로드, 실시간 진행률 확인까지.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link href="/register">
            <Button size="lg">무료로 시작하기</Button>
          </Link>
          <Link href="/api/v1/files/template">
            <Button variant="outline" size="lg">
              <Upload className="mr-2 h-4 w-4" />
              샘플 템플릿 다운로드
            </Button>
          </Link>
        </div>
      </section>

      {/* 기능 소개 */}
      <section className="mx-auto max-w-6xl px-4 pb-24">
        <div className="grid gap-8 md:grid-cols-3">
          <Card>
            <CardHeader>
              <Upload className="h-10 w-10 text-primary" />
              <CardTitle className="text-xl">간편한 업로드</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              엑셀 파일을 드래그 앤 드롭으로 업로드하면 자동으로 데이터를 검증하고
              오류를 알려드립니다.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Zap className="h-10 w-10 text-primary" />
              <CardTitle className="text-xl">빠른 등록</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              백그라운드에서 자동으로 상품을 등록합니다. 이미지 업로드부터
              API 호출까지 모두 자동화됩니다.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <BarChart3 className="h-10 w-10 text-primary" />
              <CardTitle className="text-xl">실시간 모니터링</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              등록 진행률을 실시간으로 확인하고, 완료 후 상세 결과를
              엑셀로 다운로드하세요.
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="border-t py-8">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground">
          &copy; 2026 Richlychee. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
