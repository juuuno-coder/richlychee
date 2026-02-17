"""API 엔드포인트 테스트 스크립트."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_apis():
    """모든 주요 API 엔드포인트 테스트."""

    print("=" * 60)
    print("Richlychee API 엔드포인트 점검")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. Health Check
        print("\n[1] Health Check")
        try:
            resp = await client.get("http://localhost:8000/health")
            print(f"   ✓ /health: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"   ✗ /health: {e}")

        # 2. 회원가입 테스트 (이미 존재할 수 있음)
        print("\n[2] 인증 (Auth)")
        email = "testuser@richlychee.com"
        password = "Test1234!@"

        try:
            resp = await client.post(f"{BASE_URL}/auth/register", json={
                "email": email,
                "password": password,
                "name": "테스트 사용자"
            })
            if resp.status_code == 201:
                print(f"   ✓ POST /auth/register: {resp.status_code} (새 계정 생성)")
            elif resp.status_code == 400:
                print(f"   ✓ POST /auth/register: {resp.status_code} (이미 존재)")
            else:
                print(f"   ? POST /auth/register: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ POST /auth/register: {e}")

        # 3. 로그인
        try:
            resp = await client.post(f"{BASE_URL}/auth/login", json={
                "email": email,
                "password": password
            })
            data = resp.json()
            token = data.get("access_token")
            if token:
                print(f"   ✓ POST /auth/login: {resp.status_code} (토큰 발급)")
                headers = {"Authorization": f"Bearer {token}"}
            else:
                print(f"   ✗ POST /auth/login: 토큰 없음")
                return
        except Exception as e:
            print(f"   ✗ POST /auth/login: {e}")
            return

        # 4. 사용자 정보
        print("\n[3] 사용자 (Users)")
        try:
            resp = await client.get(f"{BASE_URL}/users/me", headers=headers)
            print(f"   ✓ GET /users/me: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ GET /users/me: {e}")

        # 5. 크롤링 프리셋
        print("\n[4] 원클릭 크롤링 (Quick Crawl)")
        try:
            resp = await client.get(f"{BASE_URL}/quick-crawl/presets")
            data = resp.json()
            presets = data.get("presets", [])
            print(f"   ✓ GET /quick-crawl/presets: {resp.status_code} ({len(presets)}개 프리셋)")
            for preset in presets[:3]:
                print(f"      - {preset['name']} ({preset['crawler_type']})")
        except Exception as e:
            print(f"   ✗ GET /quick-crawl/presets: {e}")

        # 6. URL 자동 감지
        try:
            resp = await client.post(
                f"{BASE_URL}/quick-crawl/detect",
                params={"url": "https://www.amazon.com/products"}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✓ POST /quick-crawl/detect: {resp.status_code}")
                print(f"      감지된 사이트: {data.get('preset_name')}")
                print(f"      크롤러 타입: {data.get('crawler_type')}")
            else:
                print(f"   ? POST /quick-crawl/detect: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ POST /quick-crawl/detect: {e}")

        # 7. 크롤링 작업 목록
        print("\n[5] 크롤링 작업 (Crawl Jobs)")
        try:
            resp = await client.get(f"{BASE_URL}/crawl-jobs", headers=headers)
            data = resp.json()
            jobs = data.get("items", [])
            print(f"   ✓ GET /crawl-jobs: {resp.status_code} ({len(jobs)}개 작업)")
        except Exception as e:
            print(f"   ✗ GET /crawl-jobs: {e}")

        # 8. 크롤링된 상품 목록
        print("\n[6] 크롤링된 상품 (Crawled Products)")
        try:
            resp = await client.get(f"{BASE_URL}/crawled-products", headers=headers)
            data = resp.json()
            products = data.get("items", [])
            print(f"   ✓ GET /crawled-products: {resp.status_code} ({len(products)}개 상품)")
        except Exception as e:
            print(f"   ✗ GET /crawled-products: {e}")

        # 9. 등록 작업 목록
        print("\n[7] 등록 작업 (Jobs)")
        try:
            resp = await client.get(f"{BASE_URL}/jobs", headers=headers)
            data = resp.json()
            jobs = data.get("items", [])
            print(f"   ✓ GET /jobs: {resp.status_code} ({len(jobs)}개 작업)")
        except Exception as e:
            print(f"   ✗ GET /jobs: {e}")

        # 10. 네이버 자격증명
        print("\n[8] 네이버 자격증명 (Credentials)")
        try:
            resp = await client.get(f"{BASE_URL}/credentials", headers=headers)
            data = resp.json()
            creds = data.get("credentials", [])
            print(f"   ✓ GET /credentials: {resp.status_code} ({len(creds)}개)")
        except Exception as e:
            print(f"   ✗ GET /credentials: {e}")

        # 11. 카테고리
        print("\n[9] 카테고리 (Categories)")
        try:
            resp = await client.get(f"{BASE_URL}/categories/display", headers=headers)
            data = resp.json()
            categories = data.get("categories", [])
            print(f"   ✓ GET /categories/display: {resp.status_code} ({len(categories)}개)")
        except Exception as e:
            print(f"   ✗ GET /categories/display: {e}")

    print("\n" + "=" * 60)
    print("점검 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_apis())
