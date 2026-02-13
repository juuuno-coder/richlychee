"""대량 등록 오케스트레이터."""

from __future__ import annotations

import pandas as pd
import requests
from rich.console import Console
from tqdm import tqdm

from richlychee.api.client import NaverCommerceClient
from richlychee.api.images import upload_images_batch
from richlychee.api.products import register_product
from richlychee.auth.session import AuthSession
from richlychee.config import Settings
from richlychee.data.reader import read_file
from richlychee.data.transformer import (
    collect_local_images,
    product_row_to_payload,
    row_to_product_row,
    transform_dataframe,
)
from richlychee.data.validator import validate_dataframe
from richlychee.engine.result import ProductResult, RegistrationReport
from richlychee.utils.logging import get_logger

logger = get_logger("engine.runner")


class RegistrationRunner:
    """대량 상품 등록 오케스트레이터."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._console = Console()
        self._auth = AuthSession(settings)
        self._client = NaverCommerceClient(settings, self._auth)

    def run(
        self,
        file_path: str,
        *,
        dry_run: bool = False,
    ) -> RegistrationReport:
        """대량 등록 실행.

        Args:
            file_path: 입력 파일 경로 (xlsx/csv).
            dry_run: True면 검증만 수행 (API 호출 없음).

        Returns:
            등록 결과 리포트.
        """
        report = RegistrationReport()

        # 1. 파일 읽기
        self._console.print("[bold]1단계:[/bold] 파일 읽기...")
        df = read_file(file_path)
        self._console.print(f"  총 {len(df)}행 읽음")

        # 2. 사전 검증
        self._console.print("[bold]2단계:[/bold] 데이터 검증...")
        validation = validate_dataframe(df)

        if not validation.is_valid:
            self._console.print(f"  [red]검증 실패: 오류 {validation.total_errors}건[/red]")
            for err in validation.errors[:20]:
                self._console.print(f"    {err}")
            if validation.total_errors > 20:
                self._console.print(f"    ... 외 {validation.total_errors - 20}건")
            report.finish()
            return report

        if validation.total_warnings > 0:
            self._console.print(f"  [yellow]경고 {validation.total_warnings}건[/yellow]")
            for warn in validation.warnings[:10]:
                self._console.print(f"    {warn}")

        self._console.print("  [green]검증 통과[/green]")

        if dry_run:
            self._console.print("\n[bold yellow]--dry-run 모드: API 호출 없이 종료[/bold yellow]")
            # dry-run에서는 변환만 테스트
            payloads = transform_dataframe(df)
            self._console.print(f"  {len(payloads)}개 상품 페이로드 생성 확인")
            report.finish()
            return report

        # 3. 이미지 업로드
        self._console.print("[bold]3단계:[/bold] 이미지 업로드...")
        local_images = collect_local_images(df)

        image_url_map: dict[str, str] = {}
        if local_images:
            self._console.print(f"  {len(local_images)}개 로컬 이미지 업로드 중...")
            image_url_map = upload_images_batch(self._client, local_images)
            self._console.print(f"  {len(image_url_map)}개 업로드 완료")
        else:
            self._console.print("  업로드할 로컬 이미지 없음")

        # 4. 상품 등록
        self._console.print("[bold]4단계:[/bold] 상품 등록...")

        for idx, raw_row in tqdm(df.iterrows(), total=len(df), desc="상품 등록"):
            row_num = int(idx) + 2

            try:
                row = row_to_product_row(raw_row)
                payload = product_row_to_payload(row, image_url_map)
                result = register_product(self._client, payload)

                product_id = (
                    result.get("smartstoreChannelProduct", {}).get("channelProductNo")
                )
                report.add(
                    ProductResult(
                        row_index=row_num,
                        product_name=payload.name,
                        success=True,
                        product_id=str(product_id) if product_id else None,
                        api_response=result,
                    )
                )

            except requests.HTTPError as e:
                error_msg = str(e)
                try:
                    error_body = e.response.json() if e.response is not None else {}
                    error_msg = error_body.get("message", str(e))
                except Exception:
                    pass

                logger.error("행 %d 등록 실패: %s", row_num, error_msg)
                report.add(
                    ProductResult(
                        row_index=row_num,
                        product_name=raw_row.get("product_name", ""),
                        success=False,
                        error_message=error_msg,
                    )
                )

                if self._settings.registration.stop_on_error:
                    logger.error("stop_on_error=True — 등록 중단")
                    break

            except Exception as e:
                logger.error("행 %d 처리 중 예외: %s", row_num, e)
                report.add(
                    ProductResult(
                        row_index=row_num,
                        product_name=raw_row.get("product_name", ""),
                        success=False,
                        error_message=str(e),
                    )
                )

                if self._settings.registration.stop_on_error:
                    break

        report.finish()

        # 5. 결과 리포트
        self._console.print()
        report.print_summary(self._console)

        report_path = report.export_to_excel(self._settings.output.report_dir)
        self._console.print(f"\n결과 파일: {report_path}")

        return report

    def validate_only(self, file_path: str) -> bool:
        """파일 검증만 수행.

        Returns:
            검증 통과 여부.
        """
        df = read_file(file_path)
        result = validate_dataframe(df)

        if result.is_valid:
            self._console.print(f"[green]검증 통과:[/green] {len(df)}개 행")
        else:
            self._console.print(f"[red]검증 실패:[/red] 오류 {result.total_errors}건")
            for err in result.errors:
                self._console.print(f"  {err}")

        if result.total_warnings > 0:
            self._console.print(f"[yellow]경고:[/yellow] {result.total_warnings}건")
            for warn in result.warnings:
                self._console.print(f"  {warn}")

        return result.is_valid

    def auth_test(self) -> bool:
        """인증 테스트."""
        self._console.print("인증 테스트 중...")
        success = self._auth.test_connection()

        if success:
            self._console.print("[green]인증 성공[/green]")
        else:
            self._console.print("[red]인증 실패[/red]")
            self._console.print("  .env 파일의 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET를 확인하세요")

        return success
