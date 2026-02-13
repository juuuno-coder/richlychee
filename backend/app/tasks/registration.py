"""대량 등록 Celery 작업."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_app_settings
from app.core.security import decrypt_secret
from app.models.job import Job, JobStatus
from app.models.naver_credential import NaverCredential
from app.models.product_result import ProductResult


def _get_sync_engine():
    """동기 SQLAlchemy 엔진 (Celery 워커용)."""
    settings = get_app_settings()
    # asyncpg → psycopg2 변환
    url = settings.database_url.replace("+asyncpg", "+psycopg2")
    return create_engine(url)


@shared_task(bind=True, name="registration.run")
def run_registration(self, job_id: str):
    """대량 상품 등록 백그라운드 작업.

    1. DB에서 Job + NaverCredential 조회
    2. 파일 읽기 + 이미지 업로드 (상태: UPLOADING)
    3. 상품 순차 등록 (상태: RUNNING)
    4. 완료 시 상태 COMPLETED/FAILED로 변경
    """
    engine = _get_sync_engine()

    with Session(engine) as db:
        job = db.execute(select(Job).where(Job.id == uuid.UUID(job_id))).scalar_one_or_none()
        if not job:
            return {"error": "Job not found"}

        cred = db.execute(
            select(NaverCredential).where(NaverCredential.id == job.credential_id)
        ).scalar_one_or_none()
        if not cred:
            job.status = JobStatus.FAILED
            job.error_message = "자격증명을 찾을 수 없습니다."
            db.commit()
            return {"error": "Credential not found"}

        # richlychee 모듈 임포트
        from richlychee.api.images import upload_images_batch
        from richlychee.api.products import register_product
        from richlychee.auth.session import AuthSession
        from richlychee.api.client import NaverCommerceClient
        from richlychee.config import Settings
        from richlychee.data.reader import read_file
        from richlychee.data.transformer import (
            collect_local_images,
            row_to_product_row,
            product_row_to_payload,
        )

        secret = decrypt_secret(cred.naver_client_secret)
        settings = Settings(
            naver_client_id=cred.naver_client_id,
            naver_client_secret=secret,
        )
        auth = AuthSession(settings)
        client = NaverCommerceClient(settings, auth)

        try:
            # 파일 읽기
            df = read_file(job.stored_file_path)
            job.total_rows = len(df)
            job.status = JobStatus.UPLOADING
            job.started_at = datetime.now(UTC)
            db.commit()

            # 이미지 업로드
            local_images = collect_local_images(df)
            image_url_map = {}
            if local_images:
                image_url_map = upload_images_batch(client, local_images)

            # 상품 등록
            job.status = JobStatus.RUNNING
            db.commit()

            for idx, row_data in df.iterrows():
                # 취소 확인
                db.refresh(job)
                if job.status == JobStatus.CANCELLED:
                    break

                product_name = row_data.get("product_name", f"Row {idx}")
                try:
                    product_row = row_to_product_row(row_data)
                    payload = product_row_to_payload(product_row, image_url_map)

                    if job.dry_run:
                        result = ProductResult(
                            job_id=job.id,
                            row_index=idx,
                            product_name=product_name,
                            success=True,
                            naver_product_id="DRY_RUN",
                        )
                    else:
                        api_resp = register_product(client, payload)
                        product_id = str(
                            api_resp.get("smartstoreChannelProductNo")
                            or api_resp.get("originProductNo", "")
                        )
                        result = ProductResult(
                            job_id=job.id,
                            row_index=idx,
                            product_name=product_name,
                            success=True,
                            naver_product_id=product_id,
                            api_response=api_resp,
                        )
                    job.success_count += 1
                except Exception as e:
                    result = ProductResult(
                        job_id=job.id,
                        row_index=idx,
                        product_name=product_name,
                        success=False,
                        error_message=str(e),
                    )
                    job.failure_count += 1

                db.add(result)
                job.processed_rows = idx + 1
                db.commit()

                # Celery 상태 업데이트
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "processed": job.processed_rows,
                        "total": job.total_rows,
                        "success": job.success_count,
                        "failure": job.failure_count,
                    },
                )

            # 완료
            if job.status != JobStatus.CANCELLED:
                job.status = JobStatus.COMPLETED if job.failure_count == 0 else JobStatus.COMPLETED
            job.finished_at = datetime.now(UTC)
            db.commit()

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.finished_at = datetime.now(UTC)
            db.commit()
            raise

    return {
        "job_id": job_id,
        "status": job.status.value,
        "success": job.success_count,
        "failure": job.failure_count,
    }
