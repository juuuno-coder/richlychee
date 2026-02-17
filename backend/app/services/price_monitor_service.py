"""가격 모니터링 서비스."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawled_product import CrawledProduct
from app.models.price_alert import PriceAlert
from app.models.price_history import PriceHistory


class PriceMonitorService:
    """가격 모니터링 서비스."""

    @staticmethod
    async def check_price_changes(db: AsyncSession, product_id: str, new_price: int) -> dict:
        """
        가격 변동 확인 및 기록.

        Args:
            db: 데이터베이스 세션
            product_id: 상품 ID
            new_price: 새로운 가격

        Returns:
            변동 정보
        """
        from uuid import UUID

        # 상품 조회
        result = await db.execute(
            select(CrawledProduct).where(CrawledProduct.id == UUID(product_id))
        )
        product = result.scalar_one_or_none()

        if not product:
            return {"error": "Product not found"}

        # 이전 가격
        old_price = product.sale_price or 0

        # 변동 계산
        price_change = new_price - old_price
        price_change_percent = 0.0
        if old_price > 0:
            price_change_percent = (price_change / old_price) * 100

        # 가격 이력 저장
        history = PriceHistory(
            crawled_product_id=product.id,
            price=new_price,
            currency="KRW",
            original_price=product.original_price,
            price_change=price_change,
            price_change_percent=price_change_percent,
            checked_at=datetime.now(UTC),
        )
        db.add(history)

        # 상품 가격 업데이트
        product.sale_price = new_price
        product.updated_at = datetime.now(UTC)

        await db.commit()

        return {
            "product_id": str(product.id),
            "old_price": old_price,
            "new_price": new_price,
            "price_change": price_change,
            "price_change_percent": round(price_change_percent, 2),
            "is_increase": price_change > 0,
        }

    @staticmethod
    async def check_alerts(db: AsyncSession, product_id: str) -> list[dict]:
        """
        가격 알림 확인.

        Args:
            db: 데이터베이스 세션
            product_id: 상품 ID

        Returns:
            트리거된 알림 목록
        """
        from uuid import UUID

        # 상품 및 최신 가격 조회
        result = await db.execute(
            select(CrawledProduct).where(CrawledProduct.id == UUID(product_id))
        )
        product = result.scalar_one_or_none()

        if not product:
            return []

        # 활성 알림 조회
        alerts_result = await db.execute(
            select(PriceAlert).where(
                PriceAlert.crawled_product_id == product.id,
                PriceAlert.is_active == True,  # noqa: E712
            )
        )
        alerts = alerts_result.scalars().all()

        triggered = []
        current_price = product.sale_price or 0

        for alert in alerts:
            should_trigger = False

            if alert.alert_type == "below" and alert.target_price:
                # 목표 가격 이하로 하락
                should_trigger = current_price <= alert.target_price

            elif alert.alert_type == "above" and alert.target_price:
                # 목표 가격 이상으로 상승
                should_trigger = current_price >= alert.target_price

            elif alert.alert_type == "change" and alert.change_threshold:
                # 특정 변동률 이상 변화
                history_result = await db.execute(
                    select(PriceHistory)
                    .where(PriceHistory.crawled_product_id == product.id)
                    .order_by(PriceHistory.checked_at.desc())
                    .limit(1)
                )
                latest_history = history_result.scalar_one_or_none()

                if latest_history and latest_history.price_change_percent:
                    should_trigger = abs(latest_history.price_change_percent) >= alert.change_threshold

            if should_trigger:
                alert.triggered_at = datetime.now(UTC)
                alert.is_active = False  # 한 번만 알림
                triggered.append({
                    "alert_id": str(alert.id),
                    "alert_type": alert.alert_type,
                    "current_price": current_price,
                    "target_price": alert.target_price,
                })

        await db.commit()
        return triggered
