"""이메일 알림 서비스."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class EmailService:
    """이메일 발송 서비스."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        template_dir: str = "app/templates/emails",
    ):
        """
        이메일 서비스 초기화.

        Args:
            smtp_host: SMTP 서버 호스트
            smtp_port: SMTP 서버 포트
            smtp_user: SMTP 사용자명
            smtp_password: SMTP 비밀번호
            from_email: 발신 이메일
            template_dir: 이메일 템플릿 디렉토리
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email

        # Jinja2 템플릿 환경 설정
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """
        이메일 발송.

        Args:
            to_email: 수신자 이메일
            subject: 제목
            html_content: HTML 본문
            text_content: 텍스트 본문 (선택)

        Returns:
            성공 여부
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # 텍스트 버전 추가
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                msg.attach(part1)

            # HTML 버전 추가
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part2)

            # SMTP 연결 및 발송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"이메일 발송 실패: {e}")
            return False

    def send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> bool:
        """
        템플릿 기반 이메일 발송.

        Args:
            to_email: 수신자 이메일
            subject: 제목
            template_name: 템플릿 파일명 (예: "payment_success.html")
            context: 템플릿 변수

        Returns:
            성공 여부
        """
        try:
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**context)
            return self.send_email(to_email, subject, html_content)
        except Exception as e:
            print(f"템플릿 이메일 발송 실패: {e}")
            return False

    # === 알림 유형별 메서드 ===

    def send_payment_success(
        self,
        to_email: str,
        user_name: str,
        plan_name: str,
        amount: int,
        billing_cycle: str,
        payment_date: str,
    ) -> bool:
        """결제 성공 알림."""
        return self.send_template_email(
            to_email=to_email,
            subject=f"[Richlychee] {plan_name} 구독 결제가 완료되었습니다",
            template_name="payment_success.html",
            context={
                "user_name": user_name,
                "plan_name": plan_name,
                "amount": f"{amount:,}원",
                "billing_cycle": "월간" if billing_cycle == "monthly" else "연간",
                "payment_date": payment_date,
            },
        )

    def send_payment_failed(
        self,
        to_email: str,
        user_name: str,
        plan_name: str,
        error_message: str,
    ) -> bool:
        """결제 실패 알림."""
        return self.send_template_email(
            to_email=to_email,
            subject="[Richlychee] 결제 처리 중 오류가 발생했습니다",
            template_name="payment_failed.html",
            context={
                "user_name": user_name,
                "plan_name": plan_name,
                "error_message": error_message,
            },
        )

    def send_crawl_completed(
        self,
        to_email: str,
        user_name: str,
        crawl_job_id: str,
        target_url: str,
        success_count: int,
        total_items: int,
    ) -> bool:
        """크롤링 완료 알림."""
        return self.send_template_email(
            to_email=to_email,
            subject=f"[Richlychee] 크롤링 작업이 완료되었습니다 ({success_count}개 수집)",
            template_name="crawl_completed.html",
            context={
                "user_name": user_name,
                "crawl_job_id": crawl_job_id,
                "target_url": target_url,
                "success_count": success_count,
                "total_items": total_items,
            },
        )

    def send_crawl_failed(
        self,
        to_email: str,
        user_name: str,
        crawl_job_id: str,
        target_url: str,
        error_message: str,
    ) -> bool:
        """크롤링 실패 알림."""
        return self.send_template_email(
            to_email=to_email,
            subject="[Richlychee] 크롤링 작업이 실패했습니다",
            template_name="crawl_failed.html",
            context={
                "user_name": user_name,
                "crawl_job_id": crawl_job_id,
                "target_url": target_url,
                "error_message": error_message,
            },
        )

    def send_usage_warning(
        self,
        to_email: str,
        user_name: str,
        feature_name: str,
        usage_percent: int,
        current_usage: int,
        limit: int,
    ) -> bool:
        """사용량 경고 알림 (80% 도달 시)."""
        return self.send_template_email(
            to_email=to_email,
            subject=f"[Richlychee] {feature_name} 사용량이 {usage_percent}%에 도달했습니다",
            template_name="usage_warning.html",
            context={
                "user_name": user_name,
                "feature_name": feature_name,
                "usage_percent": usage_percent,
                "current_usage": current_usage,
                "limit": limit,
            },
        )

    def send_usage_limit_reached(
        self,
        to_email: str,
        user_name: str,
        feature_name: str,
        limit: int,
    ) -> bool:
        """사용량 한도 도달 알림."""
        return self.send_template_email(
            to_email=to_email,
            subject=f"[Richlychee] {feature_name} 사용량 한도에 도달했습니다",
            template_name="usage_limit_reached.html",
            context={
                "user_name": user_name,
                "feature_name": feature_name,
                "limit": limit,
            },
        )

    def send_registration_completed(
        self,
        to_email: str,
        user_name: str,
        job_id: str,
        success_count: int,
        total_rows: int,
    ) -> bool:
        """상품 등록 완료 알림."""
        return self.send_template_email(
            to_email=to_email,
            subject=f"[Richlychee] 상품 등록이 완료되었습니다 ({success_count}개)",
            template_name="registration_completed.html",
            context={
                "user_name": user_name,
                "job_id": job_id,
                "success_count": success_count,
                "total_rows": total_rows,
            },
        )
