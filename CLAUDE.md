# Richlychee 프로젝트 개발 가이드

## 프로젝트 개요

네이버 스마트스토어 대량 상품 등록 서비스 + 웹 크롤링 기반 상품 수집 플랫폼

**핵심 기능:**
- 엑셀/CSV 파일 업로드를 통한 대량 상품 등록
- 국내외 쇼핑몰 크롤링 (정적/동적 페이지 지원)
- 크롤링 데이터 저장 및 가격 조정 기능
- 구독 기반 요금제 (Free, Basic, Pro, Enterprise)
- 포트원 v2 결제 시스템
- 이메일 알림 (juuuno@naver.com)

## 기술 스택

### Backend
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async)
- **Background Tasks**: Celery + Redis
- **Crawling**: BeautifulSoup4 (정적), Playwright (동적)
- **Payment**: PortOne v2 API
- **Email**: SMTP + Jinja2 템플릿

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **Auth**: NextAuth.js
- **State Management**: SWR

### Infrastructure
- **Containerization**: Docker Compose
- **Migration**: Alembic

## 개발 원칙

### 1. 실행 속도 우선
- 이론적 설명보다는 **즉시 구현**
- "진행해줘" 지시 시 바로 코드 작성 시작
- 불필요한 확인 질문 최소화

### 2. 순차적이고 체계적인 구현
- 명확한 우선순위에 따라 단계별 진행
- 예: "1-2순으로해줘" → 프론트엔드 먼저, 그 다음 백엔드
- 각 단계 완료 후 다음 단계로 자연스럽게 전환

### 3. 완전한 기능 구현
- MVP가 아닌 **프로덕션 레벨 코드** 작성
- API 엔드포인트, 스키마, 서비스, UI 전부 구현
- 에러 처리, 로딩 상태, 성공/실패 메시지 포함

### 4. 풀스택 통합 개발
- 백엔드와 프론트엔드를 **유기적으로 연결**
- API 구현 시 프론트엔드 클라이언트 함수도 함께 작성
- 데이터 흐름의 전체 파이프라인 구현

### 5. 구체적인 요구사항 반영
- 명시된 기술 스택 정확히 준수 (예: 포트원 v2, juuuno@naver.com)
- 환경 변수, 설정 파일 모두 작성
- .env.example 파일로 설정 가이드 제공

### 6. 점진적 기능 확장
- 기본 기능부터 시작 → 고급 기능 추가
- 이전 구현을 기반으로 새 기능 확장
- 기존 코드와의 호환성 유지

### 7. 실전 중심 개발
- 실제 동작하는 코드 우선
- 테스트 가능한 형태로 구현
- Docker 컨테이너 내 코드 업데이트 방법 숙지

## 코드 작성 규칙

### Backend (FastAPI)

**파일 구조 준수:**
```
backend/
├── app/
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 스키마
│   ├── routers/         # API 엔드포인트
│   ├── services/        # 비즈니스 로직
│   ├── tasks/           # Celery 태스크
│   ├── dependencies/    # FastAPI Dependencies
│   └── templates/       # Jinja2 템플릿 (이메일)
└── richlychee/          # 크롤러, 유틸리티
```

**코딩 스타일:**
- SQLAlchemy 2.0 async 문법 사용 (`AsyncSession`, `select()`)
- Type hints 필수 (`from __future__ import annotations`)
- Pydantic v2 사용 (`model_validate`, `model_config`)
- 에러 처리는 `HTTPException` 사용

**필수 패턴:**
- 새 모델 추가 시 `app/models/__init__.py`에 import
- API 라우터 추가 시 `app/main.py`에 등록
- Celery 태스크는 동기 함수로 작성 (asyncio 변환 필요)
- 환경 변수는 `app/core/config.py`의 `AppSettings`에 추가

### Frontend (Next.js)

**파일 구조 준수:**
```
frontend/src/
├── app/
│   └── (dashboard)/     # 인증 필요한 페이지
├── components/
│   ├── ui/              # 재사용 UI 컴포넌트
│   ├── common/          # 공통 컴포넌트
│   └── [feature]/       # 기능별 컴포넌트
├── lib/
│   ├── api-client.ts    # API 클라이언트
│   └── utils.ts
└── types/
    └── index.ts         # TypeScript 타입 정의
```

**코딩 스타일:**
- `"use client"` 지시어 명확히 사용
- API 호출은 `api-client.ts`에 함수로 정의
- 로딩/에러 상태 UI 필수
- 환경 변수는 `NEXT_PUBLIC_` 접두사 사용

**UI 컴포넌트:**
- shadcn/ui + Radix UI 사용
- Tailwind CSS 클래스 활용
- `cn()` 유틸리티로 클래스 병합
- lucide-react 아이콘 사용

## 주요 기능별 구현 패턴

### 1. 크롤링 시스템

**구조:**
- `CrawlJob` (작업) + `CrawledProduct` (수집 상품)
- Celery 백그라운드 태스크
- 정적(BeautifulSoup), 동적(Playwright) 크롤러
- 환율 자동 계산 (외화 → KRW)
- 프리셋 시스템 (쿠팡, 11번가, Amazon, eBay, AliExpress)

**주의사항:**
- 크롤링 작업 상태는 `CrawlJobStatus` Enum 사용
- 이미지는 네이버 CDN에 업로드
- 사용량 제한 체크 (`SubscriptionService.check_limit`)

### 2. 구독 시스템

**4개 플랜:**
- Free: 무료 (제한적)
- Basic: 월 29,000원
- Pro: 월 79,000원
- Enterprise: 월 199,000원

**기능:**
- 사용량 추적 (`UserSubscription.usage`)
- 월간 리셋 (`usage_reset_at`)
- 80% 도달 시 이메일 경고
- 100% 도달 시 기능 차단 (402 Payment Required)

### 3. 결제 시스템 (포트원 v2)

**플로우:**
1. Frontend: 플랜 선택 → PaymentDialog 열기
2. Backend: `/payments/prepare` → Payment 레코드 생성
3. Frontend: PortOne SDK → 결제창 표시
4. Backend: `/payments/verify` → 포트원 API 검증 → 구독 활성화
5. Email: 결제 성공/실패 알림 → juuuno@naver.com

**환경 변수:**
- Backend: `PORTONE_API_KEY`, `PORTONE_API_SECRET`
- Frontend: `NEXT_PUBLIC_PORTONE_STORE_ID`, `NEXT_PUBLIC_PORTONE_CHANNEL_KEY`

### 4. 이메일 알림 시스템

**알림 종류:**
- 결제 성공/실패
- 크롤링 완료/실패
- 상품 등록 완료
- 사용량 경고 (80%)
- 사용량 한도 도달 (100%)

**발송 대상:** `juuuno@naver.com` (고정)

**템플릿 위치:** `backend/app/templates/emails/`

## 개발 워크플로우

### 새 기능 추가 시

1. **Backend 우선 또는 Frontend 우선 명확히 결정**
   - "1-2순으로" 같은 순서 지시 준수

2. **Backend 작업 순서:**
   ```
   1. 모델 생성 (models/)
   2. 스키마 정의 (schemas/)
   3. 서비스 로직 (services/)
   4. API 라우터 (routers/)
   5. Celery 태스크 (필요시)
   6. 마이그레이션 (alembic)
   7. 컨테이너 재시작
   ```

3. **Frontend 작업 순서:**
   ```
   1. 타입 정의 (types/)
   2. API 클라이언트 함수 (lib/api-client.ts)
   3. UI 컴포넌트 (components/)
   4. 페이지 구현 (app/)
   5. 라우터 추가 (sidebar.tsx)
   ```

4. **통합 테스트:**
   - Docker 컨테이너 모두 실행
   - Frontend → Backend → DB 전체 플로우 확인
   - 이메일 알림 테스트

### 데이터베이스 마이그레이션

```bash
# 컨테이너 내부에서
docker exec richlychee-backend-1 alembic revision --autogenerate -m "설명"
docker exec richlychee-backend-1 alembic upgrade head

# 재시작
docker compose restart backend
```

### 코드 업데이트 (Docker)

**주의:** Backend 코드는 이미지에 포함되므로 재빌드 필요

```bash
# 빠른 테스트: docker cp
docker cp backend/app/services/new_service.py richlychee-backend-1:/app/app/services/
docker compose restart backend

# 프로덕션: 이미지 재빌드
docker compose up -d --build backend
```

## 환경 변수 체크리스트

### Backend (.env)
```bash
✓ DATABASE_URL
✓ SECRET_KEY
✓ REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
✓ PORTONE_API_KEY, PORTONE_API_SECRET
✓ SMTP_HOST, SMTP_USER, SMTP_PASSWORD
✓ FROM_EMAIL, NOTIFICATION_EMAIL (juuuno@naver.com)
```

### Frontend (.env.local)
```bash
✓ NEXT_PUBLIC_API_URL
✓ NEXTAUTH_URL, NEXTAUTH_SECRET
✓ NEXT_PUBLIC_PORTONE_STORE_ID
✓ NEXT_PUBLIC_PORTONE_CHANNEL_KEY
```

## 트러블슈팅

### 자주 발생하는 문제

1. **마이그레이션이 새 모델을 감지 못함**
   - `app/models/__init__.py`에 import 확인
   - `alembic/env.py`에서 모델 import 확인

2. **Enum 타입 에러**
   - PostgreSQL Enum 대신 String 사용
   - 예: `status: Mapped[str] = mapped_column(String(20))`

3. **Frontend에서 API 401 에러**
   - NextAuth 세션 확인
   - `apiClient` 인터셉터 동작 확인

4. **이메일 발송 실패**
   - Gmail: 앱 비밀번호 사용 (2단계 인증 필요)
   - SMTP 포트 587 확인

5. **Docker 코드 변경 반영 안됨**
   - Backend: 이미지 재빌드 필요
   - Frontend: 볼륨 마운트 확인

## 커뮤니케이션 스타일

### 선호하는 응답 방식
- ✅ "진행하겠습니다" → 즉시 코드 작성 시작
- ✅ 구현 완료 후 간단한 요약
- ✅ 핵심 파일 경로와 주요 변경사항 명시
- ✅ 다음 단계 제안 (필요시)

### 지양하는 응답
- ❌ 과도한 설명이나 이론
- ❌ "어떻게 하시겠습니까?" 같은 반복 질문
- ❌ 구현 전 장황한 계획 설명
- ❌ 불필요한 확인 요청

## 프로젝트 목표

**비즈니스 가치:**
- 셀러의 상품 등록 시간 90% 단축
- 크롤링 자동화로 수작업 제거
- 구독 모델로 지속 가능한 수익 창출

**기술적 목표:**
- 안정적인 대량 처리 (1000+ 상품/작업)
- 확장 가능한 크롤링 아키텍처
- 프로덕션 레벨 보안 및 에러 처리

## OKR 기반 개발 원칙

### OKR이란?
Richlychee는 Google과 실리콘밸리 기업들이 사용하는 **OKR(Objectives and Key Results)** 방법론을 따릅니다. 모든 개발 작업은 OKR에 정렬되어야 하며, OKR과 무관한 작업은 우선순위에서 제외됩니다.

**상세 내용:** [OKR.md](OKR.md) 참조

### 핵심 원칙

1. **모든 작업은 OKR과 연결**
   - 새로운 기능 개발 시: "이 작업이 어떤 Key Result에 기여하는가?" 질문
   - OKR.md의 Initiatives 항목과 매칭
   - 매칭되지 않는 작업은 OKR 업데이트 필요성 검토

2. **Output이 아닌 Outcome에 집중**
   - ❌ Bad: "크롤링 기능 10개 추가" (Output)
   - ✅ Good: "크롤링 성공률 95% 달성" (Outcome)
   - 코드를 작성하는 이유가 "무엇을 만들기"가 아니라 "어떤 결과를 내기" 위함인지 명확히

3. **측정 가능한 목표 설정**
   - 모든 기능에 성공 지표 정의
   - 예: 결제 시스템 → "구독 전환율 25%"
   - 예: 크롤링 엔진 → "크롤링 성공률 95%"

4. **70% 달성을 목표로 하는 도전적 목표**
   - 100% 달성 가능한 목표는 너무 쉬운 것
   - 실패를 두려워하지 않고 도전적으로 설정
   - 50% 미만 달성 시 목표 재조정 검토

### OKR 체크 프로세스

**개발 시작 전:**
```
1. OKR.md에서 관련 Objective/KR 확인
2. 해당 작업이 Initiatives에 명시되어 있는지 확인
3. 없다면 OKR 업데이트 또는 작업 정당성 재검토
```

**개발 중:**
```
1. KR 달성에 직접적으로 기여하는 방향으로 구현
2. 부가 기능보다는 핵심 가치에 집중
3. "이게 정말 KR 달성에 도움이 되나?" 지속적 질문
```

**개발 완료 후:**
```
1. OKR.md의 해당 Initiative를 [x] 체크
2. 측정 가능한 경우 현재 KR 달성률 업데이트
3. 다음 우선순위 Initiative 확인
```

### 현재 주요 OKR (2026 Q1)

**Objective 1: 모든 네이버 스마트스토어 셀러가 가장 먼저 찾는 필수 자동화 도구가 된다**
- KR 1: 사용자 생산성 90% 향상
- KR 2: 구독 전환율 25%
- KR 3: 사용자 만족도(NPS) 70점 이상

**Objective 2: 국내외 모든 주요 쇼핑몰의 상품 데이터를 99% 정확도로 수집하는 크롤링 엔진 구축**
- KR 1: 크롤링 성공률 95% 이상
- KR 2: 지원 쇼핑몰 20개 이상
- KR 3: 크롤링 속도 평균 100개/분

**Objective 3: 월 1억 원의 안정적인 MRR 달성**
- KR 1: 유료 구독자 200명 확보
- KR 2: 고객 이탈률 5% 이하
- KR 3: 고객 생애 가치(LTV) 600만원 이상

### OKR 우선순위 매트릭스

모든 작업은 아래 우선순위에 따라 배정:

**P0 (최우선):** 현재 분기 OKR의 핵심 KR에 직접 기여
- 예: 크롤링 성공률 개선, 결제 전환율 최적화

**P1 (높음):** 현재 분기 OKR의 보조 KR에 기여
- 예: 지원 쇼핑몰 추가, 사용자 경험 개선

**P2 (중간):** 다음 분기 OKR 준비 작업
- 예: 새로운 기능 탐색, 기술 부채 해소

**P3 (낮음):** 장기 비전 관련 실험
- 예: 신기술 POC, 시장 조사

### OKR 리뷰 주기

- **주간:** 매주 월요일 - Initiatives 진행 상황 체크
- **월간:** 매월 말일 - Key Results 달성률 측정
- **분기:** 분기 마지막 주 - Objective 달성 평가 및 다음 분기 OKR 수립

---

**마지막 업데이트:** 2026-02-13
**프로젝트 상태:** 결제 시스템 구현 완료, 프로덕션 준비 단계
**현재 OKR 기간:** 2026 Q1 (01/01 ~ 03/31)
