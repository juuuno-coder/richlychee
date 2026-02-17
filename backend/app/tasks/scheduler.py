"""크롤링 스케줄러 태스크."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_app_settings
from app.models.crawl_job import CrawlJob, CrawlJobStatus
from app.models.crawl_schedule import CrawlSchedule, ScheduleFrequency


def _get_sync_engine():
    """동기 SQLAlchemy 엔진."""
    settings = get_app_settings()
    url = settings.database_url.replace("+asyncpg", "+psycopg2")
    return create_engine(url)


@shared_task(name="scheduler.run_scheduled_crawls")
def run_scheduled_crawls():
    """
    스케줄된 크롤링 실행 (Celery Beat에서 주기적 호출).

    실행 주기: 1시간마다
    """
    engine = _get_sync_engine()

    with Session(engine) as db:
        now = datetime.now(UTC)

        # 실행할 스케줄 조회 (활성 + 실행 시간 도래)
        result = db.execute(
            select(CrawlSchedule).where(
                CrawlSchedule.is_active == True,  # noqa: E712
                CrawlSchedule.next_run_at <= now,
            )
        )
        schedules = result.scalars().all()

        for schedule in schedules:
            try:
                # 크롤링 작업 생성
                job = CrawlJob(
                    user_id=schedule.user_id,
                    target_url=schedule.target_url,
                    target_type=schedule.target_type,
                    crawl_config=schedule.crawl_config,
                    status=CrawlJobStatus.PENDING,
                )
                db.add(job)
                db.flush()

                # Celery 태스크 시작
                from app.tasks.crawling import run_crawl_job
                task = run_crawl_job.delay(str(job.id))

                job.celery_task_id = task.id
                job.status = CrawlJobStatus.RUNNING

                # 스케줄 업데이트
                schedule.total_runs += 1
                schedule.last_run_at = now
                schedule.next_run_at = _calculate_next_run(now, schedule.frequency)

                db.commit()

            except Exception as e:
                print(f"스케줄 실행 실패 ({schedule.name}): {e}")
                db.rollback()
                continue

    return {"executed": len(schedules)}


def _calculate_next_run(current: datetime, frequency: ScheduleFrequency) -> datetime:
    """다음 실행 시간 계산."""
    if frequency == ScheduleFrequency.HOURLY:
        return current + timedelta(hours=1)
    elif frequency == ScheduleFrequency.DAILY:
        return current + timedelta(days=1)
    elif frequency == ScheduleFrequency.WEEKLY:
        return current + timedelta(weeks=1)
    elif frequency == ScheduleFrequency.MONTHLY:
        return current + timedelta(days=30)
    else:
        return current + timedelta(days=1)
