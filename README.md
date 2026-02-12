# Richlychee

네이버 스마트스토어에 상품을 대량 등록하는 Python CLI 도구입니다.

엑셀(`.xlsx`) 또는 CSV 파일로 상품 데이터를 입력하면, 네이버 커머스 API를 통해 자동으로 등록합니다.

---

## 주요 기능

- **엑셀/CSV 입력** — 한글 컬럼명 자동 인식 (`상품명`, `판매가`, `카테고리ID` 등)
- **사전 검증** — 필수 필드, 가격, 재고, 이미지 수, 배송비 등 API 호출 전 검증
- **이미지 자동 업로드** — 로컬 이미지를 네이버 CDN에 업로드 후 URL 자동 치환
- **옵션 조합 자동 생성** — 색상/사이즈 등 옵션을 입력하면 모든 조합을 자동 생성
- **레이트 리밋 준수** — 토큰 버킷 알고리즘으로 API 호출 속도 제어
- **자동 재시도** — 429/5xx 에러 시 지수 백오프로 재시도
- **결과 리포트** — 콘솔 요약 테이블 + 엑셀 파일로 결과 내보내기
- **dry-run 모드** — API 호출 없이 전체 파이프라인 검증

---

## 설치

### 요구 사항

- Python 3.11 이상

### 설치 방법

```bash
git clone https://github.com/juuuno-coder/richlychee.git
cd richlychee
pip install -e ".[dev]"
```

---

## 사전 준비 (네이버 API 키 발급)

실제 상품 등록을 위해서는 네이버 커머스 API 키가 필요합니다.

### 1. 스마트스토어 판매자 계정 생성

[스마트스토어센터](https://sell.smartstore.naver.com/)에서 판매자 계정을 만듭니다.

### 2. API 애플리케이션 등록

[네이버 커머스 API 센터](https://apicenter.commerce.naver.com/)에서 앱을 등록하고 `client_id`와 `client_secret`을 발급받습니다.

필요한 API 권한:
- **상품 API** (필수) — 상품 등록/수정/조회
- **판매자 정보 API** (선택) — 스토어 정보 조회

### 3. IP 화이트리스트 등록

API를 호출할 PC/서버의 공인 IP를 API 센터에 등록합니다.

### 4. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 발급받은 키를 입력합니다.

```env
NAVER_CLIENT_ID=발급받은_클라이언트_ID
NAVER_CLIENT_SECRET=$2b$10$발급받은_시크릿
```

---

## 사용법

### 인증 테스트

```bash
python -m richlychee auth-test
```

### 입력 파일 검증

```bash
python -m richlychee validate products.xlsx
```

### 대량 등록 (dry-run)

API 호출 없이 전체 파이프라인을 검증합니다.

```bash
python -m richlychee register products.xlsx --dry-run
```

### 대량 등록 (실제)

```bash
python -m richlychee register products.xlsx
```

### 옵션

```
python -m richlychee --help
python -m richlychee register --help

-v, --verbose    상세 로그 출력
--dry-run        검증만 수행 (API 호출 없음)
--version        버전 표시
```

---

## 입력 파일 형식

엑셀(`.xlsx`) 또는 CSV 파일을 지원합니다. `templates/sample_products.xlsx`를 참고하세요.

### 컬럼 목록

| 컬럼명 | 필수 | 설명 | 예시 |
|---|---|---|---|
| 상품명 | O | 상품 이름 (최대 100자) | `프리미엄 면 티셔츠` |
| 카테고리ID | O | 네이버 카테고리 ID | `50000803` |
| 판매가 | O | 판매 가격 (원) | `29900` |
| 재고수량 | | 재고 수량 | `500` |
| 상세설명 | | HTML 형식 상세 설명 | `<p>설명</p>` |
| 대표이미지 | | 이미지 URL 또는 로컬 경로 | `https://...jpg` |
| 추가이미지 | | 쉼표 구분, 최대 9장 | `img1.jpg,img2.jpg` |
| 옵션1이름 | | 첫 번째 옵션명 | `색상` |
| 옵션1값 | | 쉼표 구분 옵션 값 | `빨강,파랑,초록` |
| 옵션2이름 | | 두 번째 옵션명 | `사이즈` |
| 옵션2값 | | 쉼표 구분 옵션 값 | `S,M,L,XL` |
| 배송비유형 | | `FREE`, `PAID`, `CONDITIONAL_FREE` | `PAID` |
| 기본배송비 | | 기본 배송비 (원) | `3000` |
| 무료배송조건금액 | | 조건부 무료배송 금액 | `50000` |
| 반품배송비 | | 반품 시 배송비 | `3000` |
| 교환배송비 | | 교환 시 배송비 | `3000` |
| 판매자관리코드 | | SKU 관리 코드 | `TS-001` |
| 브랜드 | | 브랜드명 | `나이키` |
| 제조사 | | 제조사명 | `(주)제조사` |
| 원산지 | | 원산지 | `국산` |
| 태그 | | 쉼표 구분 검색 태그 | `티셔츠,면티` |
| 상품상태 | | `NEW`, `USED`, `REFURBISHED` | `NEW` |

> 영문 snake_case 컬럼명(`product_name`, `sale_price` 등)도 지원합니다.

---

## 프로젝트 구조

```
richlychee/
├── main.py                  # CLI 진입점
├── config.py                # 설정 (.env + settings.yaml)
├── auth/
│   ├── token.py             # OAuth2 토큰 발급 (bcrypt 서명)
│   └── session.py           # 자동 토큰 갱신 세션
├── api/
│   ├── client.py            # HTTP 클라이언트 (레이트 리밋 + 재시도)
│   ├── products.py          # 상품 등록/조회
│   ├── images.py            # 이미지 업로드
│   └── categories.py        # 카테고리 조회
├── data/
│   ├── models.py            # Pydantic 데이터 모델
│   ├── reader.py            # 엑셀/CSV 파일 읽기
│   ├── transformer.py       # 스프레드시트 → API 페이로드 변환
│   └── validator.py         # 사전 검증
├── engine/
│   ├── runner.py            # 대량 등록 오케스트레이터
│   └── result.py            # 결과 리포트
└── utils/
    ├── logging.py           # Rich 기반 구조화 로깅
    └── rate_limiter.py      # 토큰 버킷 레이트 리미터
```

---

## 처리 흐름

```
엑셀/CSV 입력
    ↓
[reader] 파싱 + 컬럼 정규화
    ↓
[transformer] 행 → API 페이로드 변환 (옵션 조합 자동 생성)
    ↓
[validator] 사전 검증 (필수 필드, 가격, 이미지 수 등)
    ↓
[images] 로컬 이미지 업로드 → CDN URL 치환
    ↓
[auth] OAuth2 인증 (bcrypt 서명)
    ↓
[runner] 레이트 리밋 준수하며 순차 등록
    ↓
[result] 콘솔 요약 + 엑셀 결과 리포트
```

---

## 테스트

```bash
pytest tests/ -v
```

41개 단위 테스트 포함 (인증, 리더, 변환기, 검증기).

---

## 설정

### config/settings.yaml

API URL, 타임아웃, 레이트 리밋 등 비밀이 아닌 설정을 관리합니다.

```yaml
api:
  base_url: "https://api.commerce.naver.com/external/v1"
  timeout: 30
  max_retries: 3

rate_limit:
  requests_per_second: 10
  burst_max: 15

registration:
  batch_size: 50
  stop_on_error: false
```

### .env

시크릿을 관리합니다. `config/.env.example`을 참고하세요.

---

## 라이선스

MIT
