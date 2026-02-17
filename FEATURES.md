# Richlychee 전체 기능 가이드

## 🎯 핵심 기능

### 1. 파일 업로드 대량 등록 (기존)
- 엑셀/CSV 파일로 상품 정보 업로드
- 자동 검증 및 이미지 업로드
- 네이버 스마트스토어 API 연동

---

## 🔄 웹 크롤링 시스템

### Phase 1-5: 기본 크롤링 기능

#### 1.1 정적 페이지 크롤링 (BeautifulSoup)
```bash
POST /api/v1/crawl-jobs
{
  "target_url": "https://example.com/products",
  "target_type": "static",
  "crawl_config": {
    "item_selector": ".product-item",
    "title_selector": ".title",
    "price_selector": ".price"
  }
}
```

#### 1.2 동적 페이지 크롤링 (Playwright)
```bash
POST /api/v1/crawl-jobs
{
  "target_url": "https://spa-site.com/products",
  "target_type": "dynamic",  # JavaScript 렌더링
  "crawl_config": {...}
}
```

#### 1.3 환율 자동 계산
- USD, JPY, EUR, CNY → KRW 자동 변환
- exchangerate-api.com 연동
- 실시간 환율 적용

#### 1.4 가격 조정
```bash
POST /api/v1/crawled-products/adjust-price
{
  "product_ids": [...],
  "adjustment_type": "percentage",
  "adjustment_value": 10.0  # 10% 인상
}
```

#### 1.5 재등록
```bash
POST /api/v1/crawled-products/register
{
  "product_ids": [...],
  "credential_id": "...",
  "dry_run": false
}
```

---

## 🚀 신규 추가 기능 (Phase 6+)

### 1. 원클릭 크롤링 (Quick Crawl)

URL만 입력하면 자동으로 크롤링!

```bash
POST /api/v1/quick-crawl
{
  "url": "https://www.coupang.com/products?q=키보드",
  "auto_start": true
}
```

**자동 감지되는 쇼핑몰:**
- ✅ 쿠팡 (Coupang)
- ✅ 11번가
- ✅ Amazon US
- ✅ eBay
- ✅ AliExpress

**응답 예시:**
```json
{
  "job": {
    "id": "uuid",
    "status": "RUNNING",
    "target_url": "...",
    "crawler_type": "dynamic"
  },
  "detected_site": "쿠팡",
  "used_preset": "쿠팡"
}
```

### 2. 크롤링 프리셋 시스템

주요 쇼핑몰별 최적화된 설정 자동 적용

**프리셋 목록 조회:**
```bash
GET /api/v1/quick-crawl/presets
```

**응답:**
```json
{
  "presets": [
    {
      "id": "...",
      "name": "쿠팡",
      "site_url": "https://www.coupang.com",
      "description": "쿠팡 상품 페이지 크롤링",
      "crawler_type": "dynamic",
      "usage_count": 42
    },
    ...
  ]
}
```

**자동 감지 테스트:**
```bash
POST /api/v1/quick-crawl/detect?url=https://amazon.com/products

# 응답
{
  "crawler_type": "dynamic",
  "crawl_config": {...},
  "preset_name": "Amazon US"
}
```

### 3. 주기적 크롤링 스케줄러

정기적으로 자동 크롤링 실행

**스케줄 생성:**
```json
POST /api/v1/crawl-schedules
{
  "name": "Amazon 신상품 모니터링",
  "target_url": "https://amazon.com/new-products",
  "target_type": "dynamic",
  "crawl_config": {...},
  "frequency": "DAILY",  # HOURLY, DAILY, WEEKLY, MONTHLY
  "is_active": true
}
```

**스케줄 주기:**
- `HOURLY` - 매시간
- `DAILY` - 매일
- `WEEKLY` - 매주
- `MONTHLY` - 매월

**자동 실행:**
- Celery Beat가 1시간마다 스케줄 확인
- 실행 시간이 된 스케줄 자동 실행
- 크롤링 완료 후 다음 실행 시간 자동 계산

### 4. 가격 변동 모니터링

상품 가격 변화 추적 및 알림

**가격 이력 조회:**
```bash
GET /api/v1/crawled-products/{id}/price-history

# 응답
{
  "histories": [
    {
      "price": 29000,
      "price_change": -1000,
      "price_change_percent": -3.33,
      "checked_at": "2026-02-13T15:30:00Z"
    },
    ...
  ]
}
```

**가격 알림 설정:**
```json
POST /api/v1/price-alerts
{
  "crawled_product_id": "...",
  "alert_type": "below",  # below, above, change
  "target_price": 25000,  # 25,000원 이하로 하락 시 알림
  "is_active": true
}
```

**알림 타입:**
- `below` - 목표 가격 이하로 하락
- `above` - 목표 가격 이상으로 상승
- `change` - 특정 변동률 이상 변화

**자동 가격 체크:**
```bash
POST /api/v1/price-alerts/check

# 크롤링 시 자동으로 가격 비교
# 조건 만족 시 알림 트리거
```

---

## 🎛️ 전체 API 엔드포인트

### 원클릭 크롤링
- `POST /api/v1/quick-crawl` - URL 입력만으로 자동 크롤링
- `GET /api/v1/quick-crawl/presets` - 프리셋 목록
- `POST /api/v1/quick-crawl/detect` - 크롤러 설정 자동 감지

### 크롤링 작업
- `GET /api/v1/crawl-jobs` - 작업 목록
- `POST /api/v1/crawl-jobs` - 작업 생성 (수동)
- `GET /api/v1/crawl-jobs/{id}` - 작업 상세
- `POST /api/v1/crawl-jobs/{id}/start` - 작업 시작
- `POST /api/v1/crawl-jobs/{id}/cancel` - 작업 취소
- `GET /api/v1/crawl-jobs/{id}/products` - 크롤링 결과
- `DELETE /api/v1/crawl-jobs/{id}` - 작업 삭제

### 크롤링된 상품
- `GET /api/v1/crawled-products` - 상품 목록
- `GET /api/v1/crawled-products/export` - 엑셀 내보내기
- `GET /api/v1/crawled-products/{id}` - 상품 상세
- `PUT /api/v1/crawled-products/{id}` - 상품 수정
- `DELETE /api/v1/crawled-products/{id}` - 상품 삭제
- `POST /api/v1/crawled-products/adjust-price` - 가격 일괄 조정
- `POST /api/v1/crawled-products/register` - 네이버 재등록

### 스케줄 관리
- `GET /api/v1/crawl-schedules` - 스케줄 목록
- `POST /api/v1/crawl-schedules` - 스케줄 생성
- `PUT /api/v1/crawl-schedules/{id}` - 스케줄 수정
- `DELETE /api/v1/crawl-schedules/{id}` - 스케줄 삭제

### 가격 모니터링
- `GET /api/v1/crawled-products/{id}/price-history` - 가격 이력
- `POST /api/v1/price-alerts` - 알림 생성
- `GET /api/v1/price-alerts` - 알림 목록
- `PUT /api/v1/price-alerts/{id}` - 알림 수정
- `POST /api/v1/price-alerts/check` - 알림 확인

---

## 💡 사용 시나리오

### 시나리오 1: 해외 직구 대행
```
1. Amazon URL 입력 → 원클릭 크롤링
2. 자동 환율 변환 (USD → KRW)
3. 가격 10% 인상 (마진)
4. 네이버 스마트스토어에 재등록
```

### 시나리오 2: 가격 비교 자동화
```
1. 여러 쇼핑몰 URL 스케줄 등록
2. 매일 자동 크롤링
3. 가격 변동 추적
4. 최저가 알림 설정
```

### 시나리오 3: 신상품 자동 등록
```
1. "신상품" 카테고리 URL 스케줄 등록
2. 매일 새벽 자동 크롤링
3. 신규 상품 감지
4. 자동으로 네이버 등록
```

---

## 📊 데이터베이스 구조

### 새로운 테이블
1. **crawl_presets** - 크롤링 프리셋
2. **crawl_schedules** - 주기적 크롤링 스케줄
3. **price_histories** - 가격 변동 이력
4. **price_alerts** - 가격 알림 설정

### 기존 테이블 (Phase 1-5)
1. **crawl_jobs** - 크롤링 작업
2. **crawled_products** - 크롤링된 상품
3. **jobs** - 등록 작업
4. **users, credentials, product_results**

---

## 🔧 기술 스택

### 크롤링
- **BeautifulSoup4** - 정적 HTML 파싱
- **Playwright** - 동적 JavaScript 렌더링
- **httpx** - 비동기 HTTP 클라이언트
- **aiofiles** - 비동기 파일 I/O

### 백그라운드 처리
- **Celery** - 비동기 작업 큐
- **Celery Beat** - 주기적 작업 스케줄러
- **Redis** - 메시지 브로커 및 캐시

### 환율 & 가격
- **exchangerate-api.com** - 실시간 환율 API
- **PostgreSQL JSON** - 가격 이력 저장

---

## 🚀 다음 단계

### 구현 완료 ✅
- Phase 1: 기본 크롤링 (정적)
- Phase 2: 데이터 관리 API
- Phase 3: 재등록 기능
- Phase 4: 해외 사이트 지원 (환율)
- Phase 5: 동적 페이지 지원 (Playwright)
- **Phase 6: 원클릭 크롤링** ✨
- **Phase 7: 스케줄러** ✨
- **Phase 8: 가격 모니터링** ✨

### 향후 확장 가능 (선택)
- 다국어 자동 번역 (Papago/Google Translate)
- 이미지 OCR (상품 정보 추출)
- AI 상품 설명 자동 생성
- 재고 자동 동기화
- 텔레그램/이메일 알림

---

## 📖 개발자 가이드

### 새로운 프리셋 추가
```python
# app/services/crawl_preset_service.py
DEFAULT_PRESETS = [
    {
        "name": "새 쇼핑몰",
        "site_url": "https://new-shop.com",
        "url_pattern": r"new-shop\.com",
        "crawler_type": "static",
        "crawl_config": {
            "item_selector": ".product",
            "title_selector": ".title",
            "price_selector": ".price",
            "image_selector": "img",
        },
    }
]
```

### Celery Beat 설정
```python
# celery_beat_schedule.py
from celery.schedules import crontab

beat_schedule = {
    'run-scheduled-crawls': {
        'task': 'scheduler.run_scheduled_crawls',
        'schedule': crontab(minute=0),  # 매시간
    },
}
```

---

## 📞 API 예제

### Python
```python
import httpx

# 원클릭 크롤링
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/quick-crawl",
        json={
            "url": "https://amazon.com/products?q=keyboard",
            "auto_start": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    job = response.json()
    print(f"크롤링 시작: {job['detected_site']}")
```

### cURL
```bash
# 원클릭 크롤링
curl -X POST http://localhost:8000/api/v1/quick-crawl \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.coupang.com/products?q=키보드",
    "auto_start": true
  }'
```

---

## 🎉 완성!

**총 구현 기능:**
- ✅ 9개 페이즈 완료
- ✅ 40+ API 엔드포인트
- ✅ 12개 데이터베이스 테이블
- ✅ 5개 주요 쇼핑몰 프리셋
- ✅ 환율 자동 계산
- ✅ 주기적 크롤링
- ✅ 가격 모니터링

Richlychee는 이제 완전한 **통합 쇼핑몰 자동화 플랫폼**입니다! 🚀
