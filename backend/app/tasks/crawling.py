"""크롤링 Celery 작업."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_app_settings
from app.models.crawl_job import CrawlJob, CrawlJobStatus
from app.models.crawled_product import CrawledProduct


def _get_sync_engine():
    """동기 SQLAlchemy 엔진 (Celery 워커용)."""
    settings = get_app_settings()
    # asyncpg → psycopg2 변환
    url = settings.database_url.replace("+asyncpg", "+psycopg2")
    return create_engine(url)


@shared_task(bind=True, name="crawling.run")
def run_crawl_job(self, crawl_job_id: str):
    """
    크롤링 작업 백그라운드 실행.

    1. DB에서 CrawlJob 조회
    2. 크롤러 생성 및 실행 (상태: RUNNING)
    3. 크롤링된 데이터를 CrawledProduct 테이블에 저장
    4. 완료 시 상태 COMPLETED/FAILED로 변경
    """
    engine = _get_sync_engine()

    with Session(engine) as db:
        job = db.execute(
            select(CrawlJob).where(CrawlJob.id == uuid.UUID(crawl_job_id))
        ).scalar_one_or_none()

        if not job:
            return {"error": "CrawlJob not found"}

        # 상태 업데이트: RUNNING
        job.status = CrawlJobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        db.commit()

        try:
            # 크롤러 모듈 임포트
            from richlychee.crawler import StaticCrawler, DynamicCrawler
            from richlychee.crawler.extractor import detect_currency

            # 크롤러 생성
            if job.target_type == "static":
                crawler = StaticCrawler(job.target_url, job.crawl_config)
            elif job.target_type == "dynamic":
                crawler = DynamicCrawler(job.target_url, job.crawl_config)
            else:
                raise ValueError(f"지원하지 않는 크롤러 타입: {job.target_type}")

            # 크롤링 실행 (비동기 → 동기 변환)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                products_data = loop.run_until_complete(crawler.crawl())

                # 환율 변환 (외화인 경우)
                from richlychee.utils.exchange_rate import convert_price, get_exchange_rate

                for data in products_data:
                    currency = data.get("currency", "KRW")
                    original_price = data.get("price", 0)

                    if currency != "KRW" and original_price > 0:
                        # 환율 조회 및 가격 변환
                        krw_price = loop.run_until_complete(
                            convert_price(original_price, currency, "KRW")
                        )
                        exchange_rate = loop.run_until_complete(
                            get_exchange_rate(currency, "KRW")
                        )
                        data["krw_price"] = krw_price
                        data["exchange_rate"] = exchange_rate
                    else:
                        data["krw_price"] = original_price
                        data["exchange_rate"] = 1.0

            finally:
                loop.close()

            if not products_data:
                job.status = CrawlJobStatus.COMPLETED
                job.finished_at = datetime.now(UTC)
                job.error_message = "크롤링 결과가 없습니다."
                db.commit()
                return {
                    "job_id": crawl_job_id,
                    "status": job.status.value,
                    "total": 0,
                    "success": 0,
                }

            job.total_items = len(products_data)
            db.commit()

            # 데이터베이스에 저장
            for idx, data in enumerate(products_data):
                # 취소 확인
                db.refresh(job)
                if job.status == CrawlJobStatus.CANCELLED:
                    break

                try:
                    # CrawledProduct 생성
                    product = CrawledProduct(
                        crawl_job_id=job.id,
                        user_id=job.user_id,
                        # 원본 데이터
                        original_title=data.get("title", ""),
                        original_price=data.get("price", 0),
                        original_currency=data.get("currency", "KRW"),
                        original_images=data.get("images", []),
                        original_url=data.get("url", ""),
                        original_data=data,
                        # 가공된 데이터 (환율 변환 적용)
                        product_name=data.get("title", ""),
                        sale_price=data.get("krw_price", 0),
                        exchange_rate=data.get("exchange_rate", 1.0),
                        stock_quantity=0,
                        crawled_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    db.add(product)
                    job.crawled_items = idx + 1
                    job.success_count += 1

                    # 10개마다 커밋
                    if idx % 10 == 0:
                        db.commit()

                        # Celery 상태 업데이트
                        self.update_state(
                            state="PROGRESS",
                            meta={
                                "crawled": job.crawled_items,
                                "total": job.total_items,
                                "success": job.success_count,
                                "failure": job.failure_count,
                            },
                        )

                except Exception as e:
                    job.failure_count += 1
                    print(f"상품 저장 실패 (idx={idx}): {e}")
                    continue

            # 마지막 커밋
            db.commit()

            # 완료
            if job.status != CrawlJobStatus.CANCELLED:
                job.status = CrawlJobStatus.COMPLETED
            job.finished_at = datetime.now(UTC)
            db.commit()

            # 이메일 알림 발송
            if job.status == CrawlJobStatus.COMPLETED:
                from app.services.email_service import EmailService
                from app.models.user import User

                settings = get_app_settings()
                email_service = EmailService(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                    from_email=settings.FROM_EMAIL,
                )

                # 사용자 조회
                user = db.execute(
                    select(User).where(User.id == job.user_id)
                ).scalar_one()

                # 완료 알림 발송
                email_service.send_crawl_completed(
                    to_email=settings.NOTIFICATION_EMAIL,
                    user_name=user.name,
                    crawl_job_id=str(job.id),
                    target_url=job.target_url,
                    success_count=job.success_count,
                    total_items=job.total_items,
                )

            return {
                "job_id": crawl_job_id,
                "status": job.status.value,
                "total": job.total_items,
                "success": job.success_count,
                "failure": job.failure_count,
            }

        except Exception as e:
            job.status = CrawlJobStatus.FAILED
            job.error_message = str(e)
            job.finished_at = datetime.now(UTC)
            db.commit()

            # 실패 이메일 알림 발송
            try:
                from app.services.email_service import EmailService
                from app.models.user import User

                settings = get_app_settings()
                email_service = EmailService(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                    from_email=settings.FROM_EMAIL,
                )

                # 사용자 조회
                user = db.execute(
                    select(User).where(User.id == job.user_id)
                ).scalar_one()

                # 실패 알림 발송
                email_service.send_crawl_failed(
                    to_email=settings.NOTIFICATION_EMAIL,
                    user_name=user.name,
                    crawl_job_id=str(job.id),
                    target_url=job.target_url,
                    error_message=str(e),
                )
            except Exception as email_error:
                print(f"이메일 발송 실패: {email_error}")

            raise


@shared_task(name="crawling.cancel")
def cancel_crawl_job(crawl_job_id: str):
    """크롤링 작업 취소."""
    engine = _get_sync_engine()

    with Session(engine) as db:
        job = db.execute(
            select(CrawlJob).where(CrawlJob.id == uuid.UUID(crawl_job_id))
        ).scalar_one_or_none()

        if job and job.status in (CrawlJobStatus.PENDING, CrawlJobStatus.RUNNING):
            job.status = CrawlJobStatus.CANCELLED
            job.finished_at = datetime.now(UTC)
            db.commit()

            return {"job_id": crawl_job_id, "status": "cancelled"}

        return {"error": "Job not found or cannot be cancelled"}
