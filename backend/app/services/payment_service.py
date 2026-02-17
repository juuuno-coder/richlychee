"""포트원 v2 결제 서비스."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.models.user_subscription import UserSubscription
from app.services.email_service import EmailService
from app.core.config import get_app_settings


class PaymentService:
    """포트원 v2 결제 서비스."""

    def __init__(self, api_key: str, api_secret: str):
        """
        포트원 v2 서비스 초기화.

        Args:
            api_key: 포트원 API 키
            api_secret: 포트원 API 시크릿
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.portone.io"

    async def get_access_token(self) -> str:
        """포트원 API 액세스 토큰 발급."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/login/api-key",
                json={"apiKey": self.api_key},
            )
            response.raise_for_status()
            return response.json()["accessToken"]

    async def prepare_payment(
        self,
        db: AsyncSession,
        user_id: str,
        plan_id: str,
        billing_cycle: str,
    ) -> dict:
        """
        결제 준비.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            plan_id: 플랜 ID
            billing_cycle: 결제 주기 (monthly/yearly)

        Returns:
            결제 준비 정보
        """
        # 사용자 및 플랜 조회
        user_result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = user_result.scalar_one()

        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == uuid.UUID(plan_id))
        )
        plan = plan_result.scalar_one()

        # 결제 금액 계산
        amount = plan.price_monthly if billing_cycle == "monthly" else plan.price_yearly

        # 주문 ID 생성
        order_id = f"ORDER-{uuid.uuid4()}"

        # 구독 조회 또는 생성
        subscription_result = await db.execute(
            select(UserSubscription).where(UserSubscription.user_id == user.id)
        )
        subscription = subscription_result.scalar_one_or_none()

        if not subscription:
            # 새 구독 생성
            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status="pending",
                billing_cycle=billing_cycle,
                starts_at=datetime.now(UTC),
                ends_at=datetime.now(UTC) + timedelta(days=365 * 100),  # 임시
                usage={},
                usage_reset_at=datetime.now(UTC),
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)

        # 결제 내역 생성
        payment = Payment(
            user_id=user.id,
            subscription_id=subscription.id,
            payment_id=f"PAY-{uuid.uuid4()}",  # 임시, 실제로는 포트원에서 받음
            order_id=order_id,
            amount=amount,
            currency="KRW",
            status="pending",
            plan_name=plan.name,
            billing_cycle=billing_cycle,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        return {
            "order_id": order_id,
            "payment_id": str(payment.id),
            "amount": amount,
            "currency": "KRW",
            "plan_name": plan.display_name,
            "billing_cycle": billing_cycle,
            "customer_name": user.name,
            "customer_email": user.email,
        }

    async def verify_payment(
        self,
        db: AsyncSession,
        payment_id: str,
        portone_payment_id: str,
    ) -> dict:
        """
        결제 검증 (포트원 서버 조회).

        Args:
            db: 데이터베이스 세션
            payment_id: 내부 결제 ID
            portone_payment_id: 포트원 payment_id

        Returns:
            검증 결과
        """
        # 결제 내역 조회
        result = await db.execute(
            select(Payment).where(Payment.id == uuid.UUID(payment_id))
        )
        payment = result.scalar_one()

        try:
            # 포트원 API로 결제 정보 조회
            token = await self.get_access_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payments/{portone_payment_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                portone_data = response.json()

            # 금액 검증
            if portone_data["amount"]["total"] != payment.amount:
                raise ValueError("결제 금액이 일치하지 않습니다.")

            # 상태 검증
            if portone_data["status"] == "PAID":
                # 결제 성공 처리
                payment.status = "paid"
                payment.payment_id = portone_payment_id
                payment.payment_method = portone_data.get("method", {}).get("type")
                payment.portone_response = portone_data

                # 구독 활성화
                subscription = await db.execute(
                    select(UserSubscription).where(
                        UserSubscription.id == payment.subscription_id
                    )
                )
                sub = subscription.scalar_one()
                sub.status = "active"
                sub.starts_at = datetime.now(UTC)

                if payment.billing_cycle == "monthly":
                    sub.ends_at = datetime.now(UTC) + timedelta(days=30)
                else:
                    sub.ends_at = datetime.now(UTC) + timedelta(days=365)

                sub.last_payment_at = datetime.now(UTC)
                sub.usage = {}  # 사용량 리셋
                sub.usage_reset_at = datetime.now(UTC)

                await db.commit()

                # 이메일 알림 발송
                settings = get_app_settings()
                email_service = EmailService(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                    from_email=settings.FROM_EMAIL,
                )

                # 사용자 조회
                user_result = await db.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = user_result.scalar_one()

                # 플랜 조회
                plan_result = await db.execute(
                    select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
                )
                plan = plan_result.scalar_one()

                # 알림 이메일로 발송
                email_service.send_payment_success(
                    to_email=settings.NOTIFICATION_EMAIL,
                    user_name=user.name,
                    plan_name=plan.display_name,
                    amount=payment.amount,
                    billing_cycle=payment.billing_cycle,
                    payment_date=payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                )

                return {
                    "success": True,
                    "status": "paid",
                    "message": "결제가 완료되었습니다.",
                }
            else:
                payment.status = "failed"
                payment.portone_response = portone_data
                await db.commit()

                # 실패 이메일 알림 발송
                settings = get_app_settings()
                email_service = EmailService(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                    from_email=settings.FROM_EMAIL,
                )

                # 사용자 조회
                user_result = await db.execute(
                    select(User).where(User.id == payment.user_id)
                )
                user = user_result.scalar_one()

                email_service.send_payment_failed(
                    to_email=settings.NOTIFICATION_EMAIL,
                    user_name=user.name,
                    plan_name=payment.plan_name,
                    error_message=portone_data.get("failReason", "알 수 없는 오류"),
                )

                return {
                    "success": False,
                    "status": portone_data["status"],
                    "message": "결제에 실패했습니다.",
                }

        except Exception as e:
            payment.status = "failed"
            await db.commit()
            raise e

    async def cancel_payment(
        self,
        db: AsyncSession,
        payment_id: str,
        reason: str,
    ) -> dict:
        """
        결제 취소.

        Args:
            db: 데이터베이스 세션
            payment_id: 결제 ID
            reason: 취소 사유

        Returns:
            취소 결과
        """
        result = await db.execute(
            select(Payment).where(Payment.id == uuid.UUID(payment_id))
        )
        payment = result.scalar_one()

        if payment.status != "paid":
            raise ValueError("결제 완료 상태에서만 취소할 수 있습니다.")

        try:
            # 포트원 API로 결제 취소
            token = await self.get_access_token()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payments/{payment.payment_id}/cancel",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"reason": reason},
                )
                response.raise_for_status()

            # 취소 처리
            payment.status = "refunded"
            payment.refund_reason = reason
            payment.refunded_at = datetime.now(UTC)
            await db.commit()

            return {
                "success": True,
                "message": "결제가 취소되었습니다.",
            }

        except Exception as e:
            raise e
