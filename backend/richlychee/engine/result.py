"""결과 집계 및 리포트."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.table import Table

from richlychee.utils.logging import get_logger

logger = get_logger("engine.result")


@dataclass
class ProductResult:
    """단일 상품 등록 결과."""

    row_index: int
    product_name: str
    success: bool
    product_id: str | None = None
    error_message: str | None = None
    api_response: dict[str, Any] | None = None


@dataclass
class RegistrationReport:
    """대량 등록 전체 결과."""

    results: list[ProductResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def duration_seconds(self) -> float:
        if self.finished_at is None:
            return 0
        return (self.finished_at - self.started_at).total_seconds()

    def add(self, result: ProductResult) -> None:
        self.results.append(result)

    def finish(self) -> None:
        self.finished_at = datetime.now()

    def print_summary(self, console: Console | None = None) -> None:
        """콘솔에 요약 테이블 출력."""
        console = console or Console()

        table = Table(title="등록 결과 요약")
        table.add_column("항목", style="bold")
        table.add_column("값", justify="right")

        table.add_row("전체", str(self.total))
        table.add_row("성공", f"[green]{self.success_count}[/green]")
        table.add_row("실패", f"[red]{self.failure_count}[/red]")
        table.add_row("소요 시간", f"{self.duration_seconds:.1f}초")

        console.print(table)

        # 실패 상세 출력
        failures = [r for r in self.results if not r.success]
        if failures:
            console.print()
            fail_table = Table(title="실패 상세")
            fail_table.add_column("행", justify="right")
            fail_table.add_column("상품명")
            fail_table.add_column("오류")

            for r in failures:
                fail_table.add_row(
                    str(r.row_index),
                    r.product_name,
                    r.error_message or "알 수 없는 오류",
                )

            console.print(fail_table)

    def export_to_excel(self, output_dir: str = "output") -> Path:
        """결과를 엑셀 파일로 내보내기.

        Returns:
            생성된 파일 경로.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_path / f"registration_result_{timestamp}.xlsx"

        rows = []
        for r in self.results:
            rows.append({
                "행": r.row_index,
                "상품명": r.product_name,
                "결과": "성공" if r.success else "실패",
                "상품ID": r.product_id or "",
                "오류": r.error_message or "",
            })

        df = pd.DataFrame(rows)
        df.to_excel(file_path, index=False, engine="openpyxl")

        logger.info("결과 리포트 저장: %s", file_path)
        return file_path
