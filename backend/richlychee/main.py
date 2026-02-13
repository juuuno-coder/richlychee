"""CLI 진입점 (argparse)."""

from __future__ import annotations

import argparse
import sys

from richlychee import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="richlychee",
        description="네이버 스마트스토어 대량 상품 등록 도구",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="상세 로그 출력"
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # register
    reg_parser = subparsers.add_parser("register", help="대량 상품 등록")
    reg_parser.add_argument("file", help="입력 파일 경로 (.xlsx 또는 .csv)")
    reg_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="검증만 수행 (API 호출 없음)",
    )

    # validate
    val_parser = subparsers.add_parser("validate", help="입력 파일 검증")
    val_parser.add_argument("file", help="입력 파일 경로 (.xlsx 또는 .csv)")

    # auth-test
    subparsers.add_parser("auth-test", help="인증 테스트")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 메인 함수."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # 로깅 설정
    from richlychee.utils.logging import setup_logging

    setup_logging(verbose=args.verbose)

    # 설정 로드
    from richlychee.config import get_settings

    settings = get_settings()

    # 엔진 생성
    from richlychee.engine.runner import RegistrationRunner

    runner = RegistrationRunner(settings)

    if args.command == "register":
        report = runner.run(args.file, dry_run=args.dry_run)
        return 0 if report.failure_count == 0 else 1

    elif args.command == "validate":
        valid = runner.validate_only(args.file)
        return 0 if valid else 1

    elif args.command == "auth-test":
        success = runner.auth_test()
        return 0 if success else 1

    else:
        parser.print_help()
        return 0


# python -m richlychee 지원
if __name__ == "__main__":
    sys.exit(main())
