"use client";

import { Button } from "@/components/ui/button";

export function SocialLoginButtons() {
  const handleNaverLogin = () => {
    // TODO: 네이버 OAuth 연동
    window.alert("네이버 로그인은 준비 중입니다.");
  };

  const handleKakaoLogin = () => {
    // TODO: 카카오 OAuth 연동
    window.alert("카카오 로그인은 준비 중입니다.");
  };

  return (
    <div className="space-y-2">
      <Button variant="naver" className="w-full" onClick={handleNaverLogin}>
        네이버로 로그인
      </Button>
      <Button variant="kakao" className="w-full" onClick={handleKakaoLogin}>
        카카오로 로그인
      </Button>
    </div>
  );
}
